import json

from summarization.constants import GEMINI_API_KEY, GEMINI_SUMMARY_MODEL
from summarization.dtos import GeminiSummaryResultDTO


class GeminiSummaryClient:
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
            }
        },
        "required": ["summary"],
        "additionalProperties": False,
    }

    PROMPT = """
Write exactly one concise, user-friendly paragraph summarizing the postage
stamp described by the supplied data.

Use only the supplied facts. Mention the identification, relevant physical or
visual characteristics, useful historical information, and estimated market
price when available. Clearly communicate uncertainty. The marketplace prices
are asking prices from comparable listings, not confirmed sale values. Do not
invent missing information, expose technical processing details, or give
investment advice.

Stamp data:
{stamp_data}
""".strip()

    def summarize(self, stamp_data: dict) -> GeminiSummaryResultDTO:
        from google import genai
        from google.genai import types

        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_SUMMARY_MODEL,
            contents=self.PROMPT.format(
                stamp_data=json.dumps(
                    stamp_data,
                    ensure_ascii=False,
                    indent=2,
                )
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=self.RESPONSE_SCHEMA,
            ),
        )

        parsed = response.parsed
        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini returned an invalid summary response.")

        summary = parsed.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise RuntimeError("Gemini returned an empty stamp summary.")

        return GeminiSummaryResultDTO(
            summary=summary.strip(),
            raw_result=response.model_dump(
                mode="json",
                exclude_none=True,
            ),
        )
