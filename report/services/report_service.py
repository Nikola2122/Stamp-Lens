from uuid import uuid4

from django.core.files.base import ContentFile
from django.db import transaction

from extraction.models import StampAnalysis
from pricing.models import StampPriceEstimate
from recognition.models import StampRecognition
from report.constants import REPORT_SUCCESS_MESSAGE
from report.dtos import ReportServiceResultDTO
from report.models import ReportTag, StampReport
from research.models import StampResearch, StampResearchQA
from summarization.models import StampSummary


class ReportError(RuntimeError):
    pass


class ReportService:
    """Public synchronous facade for creating the final stamp report."""

    @transaction.atomic
    def create(
        self,
        stamp_analysis: StampAnalysis,
        stamp_recognition: StampRecognition,
        stamp_research: StampResearch,
        stamp_price_estimate: StampPriceEstimate,
        stamp_summary: StampSummary,
    ) -> ReportServiceResultDTO:
        self._validate_inputs(
            stamp_analysis,
            stamp_recognition,
            stamp_research,
            stamp_price_estimate,
            stamp_summary,
        )

        try:
            cropped_stamp_bytes = self._read_cropped_stamp(stamp_analysis)
            research_qa = StampResearchQA.objects.filter(
                stamp_research=stamp_research
            ).first()

            stamp_report = StampReport(
                stamp_image=stamp_analysis.stamp_image,
                width_mm=stamp_analysis.width_mm,
                height_mm=stamp_analysis.height_mm,
                ocr_text=stamp_analysis.ocr_text,
                dominant_colors=stamp_analysis.dominant_colors,
                recognized_name=stamp_recognition.name.strip(),
                research_source_url=stamp_research.source_url,
                research_description=stamp_research.description,
                research_questions=(
                    research_qa.questions if research_qa else []
                ),
                research_answers=(
                    research_qa.answers if research_qa else []
                ),
                estimated_price=stamp_price_estimate.estimated_price,
                median_price=stamp_price_estimate.median_price,
                mean_price=stamp_price_estimate.mean_price,
                minimum_price=stamp_price_estimate.minimum_price,
                maximum_price=stamp_price_estimate.maximum_price,
                price_currency=stamp_price_estimate.currency,
                price_confidence=stamp_price_estimate.confidence,
                summary=stamp_summary.summary,
                summary_provider=self._summary_provider(stamp_summary),
            )
            stamp_report.cropped_stamp.save(
                f"stamp-report-{uuid4().hex}.png",
                ContentFile(cropped_stamp_bytes),
                save=False,
            )
            stamp_report.save()

            ReportTag.objects.bulk_create(
                ReportTag(
                    stamp_report=stamp_report,
                    name=tag.name,
                    category=tag.category,
                    confidence=tag.confidence,
                )
                for tag in stamp_analysis.tags.all()
            )

            return ReportServiceResultDTO(
                message=REPORT_SUCCESS_MESSAGE,
                stamp_report=stamp_report,
            )
        except ReportError:
            raise
        except Exception as error:
            raise ReportError(
                f"Stamp report creation failed: {error}"
            ) from error

    @staticmethod
    def _read_cropped_stamp(stamp_analysis: StampAnalysis) -> bytes:
        if not stamp_analysis.cropped_stamp:
            raise ReportError(
                "The stamp analysis does not contain a cropped stamp."
            )

        stamp_analysis.cropped_stamp.open("rb")
        try:
            return stamp_analysis.cropped_stamp.read()
        finally:
            stamp_analysis.cropped_stamp.close()

    @staticmethod
    def _summary_provider(stamp_summary: StampSummary) -> str:
        if stamp_summary.model in stamp_summary.provider:
            return stamp_summary.provider
        return f"{stamp_summary.provider}/{stamp_summary.model}"

    @staticmethod
    def _validate_inputs(
        stamp_analysis: StampAnalysis,
        stamp_recognition: StampRecognition,
        stamp_research: StampResearch,
        stamp_price_estimate: StampPriceEstimate,
        stamp_summary: StampSummary,
    ) -> None:
        inputs = (
            ("stamp analysis", stamp_analysis),
            ("stamp recognition", stamp_recognition),
            ("stamp research", stamp_research),
            ("stamp price estimate", stamp_price_estimate),
            ("stamp summary", stamp_summary),
        )
        for label, value in inputs:
            if not value.pk:
                raise ReportError(
                    f"The {label} must be saved before report creation."
                )

        if stamp_recognition.stamp_analysis_id != stamp_analysis.pk:
            raise ReportError(
                "The stamp recognition does not belong to the analysis."
            )

        related_objects = (
            ("research", stamp_research.stamp_recognition_id),
            ("price estimate", stamp_price_estimate.stamp_recognition_id),
            ("summary", stamp_summary.stamp_recognition_id),
        )
        for label, recognition_id in related_objects:
            if recognition_id != stamp_recognition.pk:
                raise ReportError(
                    f"The stamp {label} does not belong to the recognition."
                )
