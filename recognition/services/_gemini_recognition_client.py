from django.db import transaction
from django.utils import timezone

from recognition.constants import (
    GEMINI_API_KEY,
    GEMINI_RECOGNITION_MODEL,
    RECOGNITION_MONTHLY_REQUEST_LIMIT,
)
from recognition.dtos import RecognitionResultDTO
from recognition.models import RecognitionUsage


class GeminiRecognitionClient:
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"},
                ]
            }
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    PROMPT = """
Identify the exact postage stamp shown in the image.

Visible OCR text extracted from the stamp:
{ocr_text}

Return the most specific, searchable stamp name supported by the image and OCR.
Include the country, denomination, year, issue, or series in the name when they
are visible or can be identified confidently.

Return null when the stamp cannot be identified confidently. Do not return a
generic answer such as "stamp", "stamps", "postage stamp", or "postage stamps".
""".strip()

    def recognize(
        self,
        image_bytes: bytes,
        ocr_text: str,
    ) -> RecognitionResultDTO:
        from google import genai
        from google.genai import types

        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        self._reserve_request()
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_RECOGNITION_MODEL,
            contents=[
                self.PROMPT.format(
                    ocr_text=ocr_text.strip() or "No OCR text was detected."
                ),
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                ),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=self.RESPONSE_SCHEMA,
            ),
        )

        parsed = response.parsed
        if not isinstance(parsed, dict):
            raise RuntimeError(
                "Gemini returned an invalid recognition response."
            )

        name = parsed.get("name")
        if isinstance(name, str):
            name = name.strip() or None
        elif name is not None:
            name = None

        return RecognitionResultDTO(
            name=name,
            raw_result=response.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )

    @staticmethod
    @transaction.atomic
    def _reserve_request() -> None:
        current_period = timezone.now().date().replace(day=1)
        RecognitionUsage.objects.get_or_create(
            pk=1,
            defaults={
                "period_start": current_period,
                "request_count": 0,
            },
        )
        usage = RecognitionUsage.objects.select_for_update().get(pk=1)

        if usage.period_start != current_period:
            usage.period_start = current_period
            usage.request_count = 0

        if usage.request_count >= RECOGNITION_MONTHLY_REQUEST_LIMIT:
            raise RuntimeError(
                "The monthly Gemini recognition limit "
                f"of {RECOGNITION_MONTHLY_REQUEST_LIMIT} requests "
                "has been reached."
            )

        usage.request_count += 1
        usage.save(
            update_fields=(
                "period_start",
                "request_count",
                "updated_at",
            )
        )
