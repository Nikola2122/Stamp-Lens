from uuid import uuid4

from processingjob.constants import (
    PROCESSING_JOB_CHANNEL_PREFIX,
    PROCESSING_JOB_START_DELAY_SECONDS,
)
from processingjob.dtos import ProcessingJobStartDTO
from processingjob.tasks import execute_processing_job


class ProcessingJobError(RuntimeError):
    pass


class ProcessingJobService:
    """Public facade for scheduling the top-level processing task."""

    def start(self, job_id: str | None = None) -> ProcessingJobStartDTO:
        try:
            resolved_job_id = job_id.strip() if job_id else uuid4().hex
            if not resolved_job_id:
                raise ProcessingJobError("The job ID cannot be empty.")

            channel = (
                f"{PROCESSING_JOB_CHANNEL_PREFIX}:{resolved_job_id}"
            )
            async_result = execute_processing_job.apply_async(
                args=(resolved_job_id,),
                countdown=PROCESSING_JOB_START_DELAY_SECONDS,
            )
            return ProcessingJobStartDTO(
                job_id=resolved_job_id,
                celery_task_id=async_result.id,
                channel=channel,
                delay_seconds=PROCESSING_JOB_START_DELAY_SECONDS,
            )
        except ProcessingJobError:
            raise
        except Exception as error:
            raise ProcessingJobError(
                f"The processing job could not be scheduled: {error}"
            ) from error
