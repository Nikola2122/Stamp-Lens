from extraction.models import StampAnalysis
from pricing.models import StampPriceEstimate
from recognition.models import StampRecognition
from research.models import StampResearch, StampResearchQA
from summarization.constants import (
    GEMINI_SUMMARY_MODEL,
    SUMMARY_PROVIDER,
    SUMMARY_SUCCESS_MESSAGE,
)
from summarization.dtos import SummaryServiceResultDTO
from summarization.models import StampSummary
from summarization.services._gemini_summary_client import GeminiSummaryClient


class SummaryError(RuntimeError):
    pass


class SummaryService:
    """
    Public synchronous facade for the final AI summary.

    The future background job calls only ``summarize`` with the four persisted
    stage objects produced by extraction, recognition, research, and pricing.
    """

    def __init__(
        self,
        summary_client: GeminiSummaryClient | None = None,
    ):
        self._summary_client = summary_client or GeminiSummaryClient()

    def summarize(
        self,
        stamp_analysis: StampAnalysis,
        stamp_recognition: StampRecognition,
        stamp_research: StampResearch | None,
        stamp_price_estimate: StampPriceEstimate | None,
    ) -> SummaryServiceResultDTO:
        self._validate_inputs(
            stamp_analysis,
            stamp_recognition,
            stamp_research,
            stamp_price_estimate,
        )

        try:
            input_snapshot = self._build_input_snapshot(
                stamp_analysis,
                stamp_recognition,
                stamp_research,
                stamp_price_estimate,
            )
            result = self._summary_client.summarize(input_snapshot)
            stamp_summary, _ = StampSummary.objects.update_or_create(
                stamp_recognition=stamp_recognition,
                defaults={
                    "summary": result.summary,
                    "provider": SUMMARY_PROVIDER,
                    "model": GEMINI_SUMMARY_MODEL,
                    "input_snapshot": input_snapshot,
                    "raw_result": result.raw_result,
                },
            )
            return SummaryServiceResultDTO(
                message=SUMMARY_SUCCESS_MESSAGE,
                stamp_summary=stamp_summary,
            )
        except SummaryError:
            raise
        except Exception as error:
            raise SummaryError(
                f"Stamp summarization failed: {error}"
            ) from error

    @staticmethod
    def _validate_inputs(
        stamp_analysis: StampAnalysis,
        stamp_recognition: StampRecognition,
        stamp_research: StampResearch | None,
        stamp_price_estimate: StampPriceEstimate | None,
    ) -> None:
        inputs = (
            ("stamp analysis", stamp_analysis),
            ("stamp recognition", stamp_recognition),
        )
        for label, value in inputs:
            if not value.pk:
                raise SummaryError(
                    f"The {label} must be saved before summarization."
                )

        if stamp_recognition.stamp_analysis_id != stamp_analysis.pk:
            raise SummaryError(
                "The stamp recognition does not belong to the analysis."
            )
        if (stamp_research is not None and
                stamp_research.stamp_recognition_id != stamp_recognition.pk):
            raise SummaryError(
                "The stamp research does not belong to the recognition."
            )
        if (stamp_price_estimate is not None and
                stamp_price_estimate.stamp_recognition_id
                != stamp_recognition.pk):
            raise SummaryError(
                "The price estimate does not belong to the recognition."
            )

    @staticmethod
    def _build_input_snapshot(
        stamp_analysis: StampAnalysis,
        stamp_recognition: StampRecognition,
        stamp_research: StampResearch | None,
        stamp_price_estimate: StampPriceEstimate | None,
    ) -> dict:
        research_qa = (
            StampResearchQA.objects.filter(
                stamp_research=stamp_research
            ).first()
            if stamp_research else None
        )

        return {
            "analysis": {
                "width_mm": stamp_analysis.width_mm,
                "height_mm": stamp_analysis.height_mm,
                "ocr_text": stamp_analysis.ocr_text,
                "image_description": stamp_analysis.image_description,
                "dominant_colors": stamp_analysis.dominant_colors,
                "tags": [
                    {
                        "name": tag.name,
                        "category": tag.category,
                        "confidence": tag.confidence,
                    }
                    for tag in stamp_analysis.tags.all()
                ],
            },
            "recognition": {
                "name": stamp_recognition.name,
                "provider": stamp_recognition.provider,
            },
            "research": (
                {
                    "search_query": stamp_research.search_query,
                    "source_title": stamp_research.source_title,
                    "source_url": stamp_research.source_url,
                    "description": stamp_research.description,
                    "questions": (
                        research_qa.questions if research_qa else []
                    ),
                    "answers": research_qa.answers if research_qa else [],
                }
                if stamp_research else None
            ),
            "price_estimate": (
                {
                    "search_query": stamp_price_estimate.search_query,
                    "estimated_price": str(
                        stamp_price_estimate.estimated_price
                    ),
                    "median_price": str(stamp_price_estimate.median_price),
                    "mean_price": str(stamp_price_estimate.mean_price),
                    "minimum_price": str(
                        stamp_price_estimate.minimum_price
                    ),
                    "maximum_price": str(
                        stamp_price_estimate.maximum_price
                    ),
                    "currency": stamp_price_estimate.currency,
                    "confidence": stamp_price_estimate.confidence,
                    "comparable_count": stamp_price_estimate.comparable_count,
                    "comparable_listings": (
                        stamp_price_estimate.comparable_sales
                    ),
                }
                if stamp_price_estimate else None
            ),
        }
