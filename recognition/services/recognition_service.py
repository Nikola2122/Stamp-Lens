from extraction.models import StampAnalysis
from recognition.constants import (
    GENERIC_RECOGNITION_NAMES,
    RECOGNITION_NOT_FOUND_MESSAGE,
    RECOGNITION_PROVIDER,
    RECOGNITION_SUCCESS_MESSAGE,
)
from recognition.models import StampRecognition
from recognition.dtos import RecognitionServiceResultDTO
from recognition.services._gemini_recognition_client import (
    GeminiRecognitionClient,
)


class RecognitionError(RuntimeError):
    pass


class RecognitionService:
    """
    Public synchronous facade for stamp recognition.

    The future background job calls only ``recognize`` with a saved
    ``StampAnalysis``. This service reads the cropped image, calls the
    recognition provider, and persists a meaningful recognized name.
    """

    def __init__(
        self,
        recognition_client: GeminiRecognitionClient | None = None,
    ):
        self._recognition_client = (
            recognition_client or GeminiRecognitionClient()
        )

    def recognize(
        self,
        stamp_analysis: StampAnalysis,
    ) -> RecognitionServiceResultDTO:
        if not stamp_analysis.pk:
            raise RecognitionError(
                "The stamp analysis must be saved before recognition."
            )
        if not stamp_analysis.cropped_stamp:
            raise RecognitionError(
                "The stamp analysis does not contain a cropped stamp."
            )

        try:
            stamp_analysis.cropped_stamp.open("rb")
            try:
                image_bytes = stamp_analysis.cropped_stamp.read()
            finally:
                stamp_analysis.cropped_stamp.close()

            result = self._recognition_client.recognize(
                image_bytes=image_bytes,
                ocr_text=stamp_analysis.ocr_text,
            )
            if not self._is_meaningful_name(result.name):
                return RecognitionServiceResultDTO(
                    message=RECOGNITION_NOT_FOUND_MESSAGE,
                    stamp_recognition=None,
                )

            stamp_recognition, _ = StampRecognition.objects.update_or_create(
                stamp_analysis=stamp_analysis,
                defaults={
                    "name": result.name,
                    "provider": RECOGNITION_PROVIDER,
                    "raw_result": result.raw_result,
                },
            )
            return RecognitionServiceResultDTO(
                message=RECOGNITION_SUCCESS_MESSAGE,
                stamp_recognition=stamp_recognition,
            )
        except RecognitionError:
            raise
        except Exception as error:
            raise RecognitionError(
                f"Stamp recognition failed: {error}"
            ) from error

    @staticmethod
    def _is_meaningful_name(name: str | None) -> bool:
        if not name:
            return False
        return name.strip().casefold() not in GENERIC_RECOGNITION_NAMES
