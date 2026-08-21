from django.core.management.base import BaseCommand, CommandError

from ingestion.models import StampImage

from processingjob.services import ProcessingJobError, ProcessingJobService


class Command(BaseCommand):
    help = "Schedule a complete stamp processing job."

    def add_arguments(self, parser):
        parser.add_argument(
            "stamp_image_id",
            type=int,
            help="ID of the uploaded stamp image to process.",
        )

    def handle(self, *args, **options):
        try:
            stamp_image = StampImage.objects.get(
                pk=options["stamp_image_id"]
            )
            result = ProcessingJobService().start(stamp_image)
        except StampImage.DoesNotExist as error:
            raise CommandError("The stamp image does not exist.") from error
        except ProcessingJobError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS("Processing job scheduled."))
        self.stdout.write(f"Job ID: {result.job_id}")
        self.stdout.write(f"Celery task ID: {result.celery_task_id}")
        self.stdout.write(f"Redis channel: {result.channel}")
        self.stdout.write(f"Starts after: {result.delay_seconds} seconds")
