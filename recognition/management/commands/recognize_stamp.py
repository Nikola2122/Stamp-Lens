from django.core.management.base import BaseCommand, CommandError

from extraction.models import StampAnalysis
from recognition.constants import RECOGNITION_NOT_FOUND_MESSAGE
from recognition.services import RecognitionError, RecognitionService


class Command(BaseCommand):
    help = "Run recognition for a saved stamp analysis."

    def add_arguments(self, parser):
        parser.add_argument(
            "analysis_id",
            type=int,
            help="ID of the StampAnalysis to recognize.",
        )

    def handle(self, *args, **options):
        analysis_id = options["analysis_id"]

        try:
            stamp_analysis = StampAnalysis.objects.get(pk=analysis_id)
        except StampAnalysis.DoesNotExist as error:
            raise CommandError(
                f"Stamp analysis with ID {analysis_id} does not exist."
            ) from error

        try:
            result = RecognitionService().recognize(stamp_analysis)
        except RecognitionError as error:
            raise CommandError(str(error)) from error

        if result.message == RECOGNITION_NOT_FOUND_MESSAGE:
            self.stdout.write(self.style.WARNING(result.message))
        else:
            self.stdout.write(self.style.SUCCESS(result.message))
