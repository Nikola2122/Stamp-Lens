from extraction.services._a4_processor import A4Processor
from extraction.services._image_tagger import ImageTagger
from extraction.services._ocr_processor import OCRProcessor
from extraction.services.stamp_analysis_service import StampAnalysisService
from extraction.dtos import ExtractionServiceResultDTO
from ingestion.models import StampImage


class ExtractionError(RuntimeError):
    pass


class ExtractionService:
    """
    Public synchronous facade for stamp extraction.

    The background job calls only ``extract`` and is responsible for publishing
    progress after this method returns or for handling ``ExtractionError``.
    """

    def __init__(
        self,
        a4_processor: A4Processor | None = None,
        ocr_processor: OCRProcessor | None = None,
        image_tagger: ImageTagger | None = None,
        analysis_service: StampAnalysisService | None = None,
    ):
        self._a4_processor = a4_processor or A4Processor()
        self._ocr_processor = ocr_processor or OCRProcessor()
        self._image_tagger = image_tagger or ImageTagger()
        self._analysis_service = analysis_service or StampAnalysisService()

    def extract(
        self,
        stamp_image: StampImage,
    ) -> ExtractionServiceResultDTO:
        if not stamp_image.pk:
            raise ExtractionError(
                "The stamp image must be saved before it can be extracted."
            )

        try:
            stamp_image.file.open("rb")
            try:
                image_bytes = stamp_image.file.read()
            finally:
                stamp_image.file.close()

            extraction_result = self._a4_processor.process(image_bytes)
            cropped_stamp = extraction_result.cropped_stamp
            ocr_result = self._ocr_processor.process(cropped_stamp)
            tagging_result = self._image_tagger.process(cropped_stamp)

            stamp_analysis = self._analysis_service.save(
                stamp_image=stamp_image,
                extraction_result=extraction_result,
                ocr_result=ocr_result,
                tagging_result=tagging_result,
            )
            return ExtractionServiceResultDTO(
                message="Stamp extraction completed successfully.",
                stamp_analysis=stamp_analysis,
            )
        except ExtractionError:
            raise
        except Exception as error:
            raise ExtractionError(
                f"Stamp extraction failed: {error}"
            ) from error
