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
        stamp_recognition: StampRecognition | None = None,
        stamp_research: StampResearch | None = None,
        stamp_price_estimate: StampPriceEstimate | None = None,
        stamp_summary: StampSummary | None = None,
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
            research_qa = (
                StampResearchQA.objects.filter(
                    stamp_research=stamp_research
                ).first()
                if stamp_research else None
            )

            stamp_report = StampReport(
                stamp_image=stamp_analysis.stamp_image,
                width_mm=stamp_analysis.width_mm,
                height_mm=stamp_analysis.height_mm,
                ocr_text=stamp_analysis.ocr_text,
                dominant_colors=stamp_analysis.dominant_colors,
                recognized_name=(
                    stamp_recognition.name.strip() if stamp_recognition else ""
                ),
                research_source_url=(
                    stamp_research.source_url if stamp_research else ""
                ),
                research_description=(
                    stamp_research.description if stamp_research else ""
                ),
                research_questions=(
                    research_qa.questions if research_qa else []
                ),
                research_answers=(
                    research_qa.answers if research_qa else []
                ),
                estimated_price=(
                    stamp_price_estimate.estimated_price
                    if stamp_price_estimate else None
                ),
                median_price=(
                    stamp_price_estimate.median_price
                    if stamp_price_estimate else None
                ),
                mean_price=(
                    stamp_price_estimate.mean_price
                    if stamp_price_estimate else None
                ),
                minimum_price=(
                    stamp_price_estimate.minimum_price
                    if stamp_price_estimate else None
                ),
                maximum_price=(
                    stamp_price_estimate.maximum_price
                    if stamp_price_estimate else None
                ),
                price_currency=(
                    stamp_price_estimate.currency
                    if stamp_price_estimate else ""
                ),
                price_confidence=(
                    stamp_price_estimate.confidence
                    if stamp_price_estimate else ""
                ),
                summary=stamp_summary.summary if stamp_summary else "",
                summary_provider=(
                    self._summary_provider(stamp_summary)
                    if stamp_summary else ""
                ),
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
        stamp_recognition: StampRecognition | None,
        stamp_research: StampResearch | None,
        stamp_price_estimate: StampPriceEstimate | None,
        stamp_summary: StampSummary | None,
    ) -> None:
        if not stamp_analysis.pk:
            raise ReportError(
                "The stamp analysis must be saved before report creation."
            )

        optional_inputs = (
            ("stamp recognition", stamp_recognition),
            ("stamp research", stamp_research),
            ("stamp price estimate", stamp_price_estimate),
            ("stamp summary", stamp_summary),
        )
        for label, value in optional_inputs:
            if value is not None and not value.pk:
                raise ReportError(
                    f"The {label} must be saved before report creation."
                )

        if (stamp_recognition is not None and
                stamp_recognition.stamp_analysis_id != stamp_analysis.pk):
            raise ReportError(
                "The stamp recognition does not belong to the analysis."
            )

        if stamp_recognition is None and any(
            (stamp_research, stamp_price_estimate, stamp_summary)
        ):
            raise ReportError(
                "Recognition is required for enriched report data."
            )

        related_objects = (
            ("research", stamp_research.stamp_recognition_id)
            if stamp_research else None,
            ("price estimate", stamp_price_estimate.stamp_recognition_id)
            if stamp_price_estimate else None,
            ("summary", stamp_summary.stamp_recognition_id)
            if stamp_summary else None,
        )
        for related in related_objects:
            if related is None:
                continue
            label, recognition_id = related
            if recognition_id != stamp_recognition.pk:
                raise ReportError(
                    f"The stamp {label} does not belong to the recognition."
                )
