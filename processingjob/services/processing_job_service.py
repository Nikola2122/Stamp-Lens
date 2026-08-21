from uuid import uuid4

from ingestion.models import StampImage

from processingjob.constants import (
    PROCESSING_JOB_START_DELAY_SECONDS,
)
from processingjob.dtos import (
    CompletedProcessingJobDTO,
    ProcessingJobStartDTO,
)
from processingjob.models import ProcessingJobStatus, StampProcessingJob
from processingjob.tasks import execute_processing_job


class ProcessingJobError(RuntimeError):
    pass


class ProcessingJobReportNotFound(ProcessingJobError):
    pass


class ProcessingJobService:
    """Public facade for scheduling the top-level processing task."""

    def start(self, stamp_image: StampImage) -> ProcessingJobStartDTO:
        if not stamp_image.pk:
            raise ProcessingJobError(
                "The stamp image must be saved before processing."
            )

        celery_task_id = uuid4().hex
        job = StampProcessingJob.objects.create(
            stamp_image=stamp_image,
            celery_task_id=celery_task_id,
        )
        try:
            async_result = execute_processing_job.apply_async(
                args=(str(job.id),),
                task_id=celery_task_id,
                countdown=PROCESSING_JOB_START_DELAY_SECONDS,
            )
            job.status = ProcessingJobStatus.QUEUED
            job.save(update_fields=("status", "updated_at"))
            return ProcessingJobStartDTO(
                job_id=str(job.id),
                celery_task_id=async_result.id,
                channel=job.redis_channel,
                delay_seconds=PROCESSING_JOB_START_DELAY_SECONDS,
            )
        except Exception as error:
            job.status = ProcessingJobStatus.FAILED
            job.error_message = f"Scheduling failed: {error}"
            job.save(
                update_fields=("status", "error_message", "updated_at")
            )
            raise ProcessingJobError(
                f"The processing job could not be scheduled: {error}"
            ) from error

    def get_completed_jobs(
        self,
        stamp_image: StampImage,
    ) -> list[CompletedProcessingJobDTO]:
        if not stamp_image.pk:
            raise ProcessingJobError(
                "The stamp image must be saved before loading its jobs."
            )

        completed_statuses = (
            ProcessingJobStatus.SUCCEEDED,
            ProcessingJobStatus.SUCCEEDED_WITH_WARNINGS,
        )
        jobs = stamp_image.processing_jobs.filter(
            status__in=completed_statuses,
        ).order_by("-created_at")
        return [
            CompletedProcessingJobDTO(
                job_id=str(job.id),
                status=job.status,
                created_at=job.created_at,
            )
            for job in jobs
        ]

    def get_report(self, processing_job_id: str):
        completed_statuses = (
            ProcessingJobStatus.SUCCEEDED,
            ProcessingJobStatus.SUCCEEDED_WITH_WARNINGS,
        )
        try:
            job = StampProcessingJob.objects.select_related("report").get(
                pk=processing_job_id,
                status__in=completed_statuses,
            )
        except (StampProcessingJob.DoesNotExist, ValueError) as error:
            raise ProcessingJobReportNotFound(
                "The completed processing job does not exist."
            ) from error

        if job.report is None:
            raise ProcessingJobReportNotFound(
                "The processing job does not have a report."
            )
        return job.report
