from django.core.management.base import BaseCommand, CommandError

from recognition.models import StampRecognition
from pricing.constants import PRICE_NOT_FOUND_MESSAGE
from pricing.services import PriceEstimateError, PriceEstimateService


class Command(BaseCommand):
    help = "Estimate a saved stamp recognition's price from eBay listings."

    def add_arguments(self, parser):
        parser.add_argument(
            "recognition_id",
            type=int,
            help="ID of the StampRecognition to price.",
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
            result = PriceEstimateService().estimate(
                stamp_recognition
            )
        except PriceEstimateError as error:
            raise CommandError(str(error)) from error

        if result.message == PRICE_NOT_FOUND_MESSAGE:
            self.stdout.write(self.style.WARNING(result.message))
        else:
            self.stdout.write(self.style.SUCCESS(result.message))
