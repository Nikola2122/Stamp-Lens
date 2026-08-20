from celery import shared_task

from processingjob.constants import (
    PROCESSING_JOB_CHANNEL_PREFIX,
    PROCESSING_JOB_TEST_MESSAGE,
)
from processingjob._redis_publisher import RedisProgressPublisher


@shared_task(name="processingjob.execute")
def execute_processing_job(job_id: str) -> dict:
    """Temporary processing task that only publishes one test event."""

    channel = f"{PROCESSING_JOB_CHANNEL_PREFIX}:{job_id}"
    subscriber_count = RedisProgressPublisher().publish(
        channel,
        PROCESSING_JOB_TEST_MESSAGE,
    )
    return {
        "job_id": job_id,
        "channel": channel,
        "message": PROCESSING_JOB_TEST_MESSAGE,
        "subscriber_count": subscriber_count,
    }
