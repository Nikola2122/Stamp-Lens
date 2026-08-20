from django.core.management.base import BaseCommand, CommandError

from extraction.models import StampAnalysis
from pricing.models import StampPriceEstimate
from recognition.models import StampRecognition
from report.services import ReportError, ReportService
from research.models import StampResearch
from summarization.models import StampSummary


class Command(BaseCommand):
    help = "Create a report from five saved stamp result objects."

    def add_arguments(self, parser):
        parser.add_argument("analysis_id", type=int)
        parser.add_argument("recognition_id", type=int)
        parser.add_argument("research_id", type=int)
        parser.add_argument("price_estimate_id", type=int)
        parser.add_argument("summary_id", type=int)

    def handle(self, *args, **options):
        stamp_analysis = self._get_object(
            StampAnalysis,
            options["analysis_id"],
            "Stamp analysis",
        )
        stamp_recognition = self._get_object(
            StampRecognition,
            options["recognition_id"],
            "Stamp recognition",
        )
        stamp_research = self._get_object(
            StampResearch,
            options["research_id"],
            "Stamp research",
        )
        stamp_price_estimate = self._get_object(
            StampPriceEstimate,
            options["price_estimate_id"],
            "Stamp price estimate",
        )
        stamp_summary = self._get_object(
            StampSummary,
            options["summary_id"],
            "Stamp summary",
        )

        try:
            result = ReportService().create(
                stamp_analysis,
                stamp_recognition,
                stamp_research,
                stamp_price_estimate,
                stamp_summary,
            )
        except ReportError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS(result.message))
        self.stdout.write(f"Report ID: {result.stamp_report.pk}")

    @staticmethod
    def _get_object(model, object_id: int, label: str):
        try:
            return model.objects.get(pk=object_id)
        except model.DoesNotExist as error:
            raise CommandError(
                f"{label} with ID {object_id} does not exist."
            ) from error
