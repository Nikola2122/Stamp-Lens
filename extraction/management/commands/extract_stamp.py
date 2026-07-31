from django.core.management.base import BaseCommand, CommandError

from extraction.services import ExtractionError, ExtractionService
from ingestion.models import StampImage


class Command(BaseCommand):
    help = "Run extraction for a saved stamp image."

    def add_arguments(self, parser):
        parser.add_argument(
            "image_id",
            type=int,
            help="ID of the StampImage to process.",
        )

    def handle(self, *args, **options):
        image_id = options["image_id"]

        try:
            stamp_image = StampImage.objects.get(pk=image_id)
        except StampImage.DoesNotExist as error:
            raise CommandError(
                f"Stamp image with ID {image_id} does not exist."
            ) from error

        try:
            result = ExtractionService().extract(stamp_image)
        except ExtractionError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS(result.message))
