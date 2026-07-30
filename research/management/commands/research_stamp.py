from django.core.management.base import BaseCommand, CommandError

from recognition.models import StampRecognition
from research.constants import RESEARCH_NOT_FOUND_MESSAGE
from research.services import ResearchError, ResearchService


class Command(BaseCommand):
    help = "Run Wikipedia research for a saved stamp recognition."

    def add_arguments(self, parser):
        parser.add_argument(
            "recognition_id",
            type=int,
            help="ID of the StampRecognition to research.",
        )

    def handle(self, *args, **options):
        recognition_id = options["recognition_id"]

        try:
            stamp_recognition = StampRecognition.objects.get(
                pk=recognition_id
            )
        except StampRecognition.DoesNotExist as error:
            raise CommandError(
                "Stamp recognition with ID "
                f"{recognition_id} does not exist."
            ) from error

        try:
            message = ResearchService().research(stamp_recognition)
        except ResearchError as error:
            raise CommandError(str(error)) from error

        if message == RESEARCH_NOT_FOUND_MESSAGE:
            self.stdout.write(self.style.WARNING(message))
        else:
            self.stdout.write(self.style.SUCCESS(message))
