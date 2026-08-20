from django.core.management.base import BaseCommand, CommandError

from processingjob.services import ProcessingJobError, ProcessingJobService


class Command(BaseCommand):
    help = "Schedule the temporary processing job Redis test."

    def add_arguments(self, parser):
        parser.add_argument(
            "job_id",
            nargs="?",
            help="Optional job ID; a generated ID is used when omitted.",
        )

    def handle(self, *args, **options):
        try:
            result = ProcessingJobService().start(options["job_id"])
        except ProcessingJobError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS("Processing job scheduled."))
        self.stdout.write(f"Job ID: {result.job_id}")
        self.stdout.write(f"Celery task ID: {result.celery_task_id}")
        self.stdout.write(f"Redis channel: {result.channel}")
        self.stdout.write(f"Starts after: {result.delay_seconds} seconds")
