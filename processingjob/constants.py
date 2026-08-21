import os


PROCESSING_JOB_REDIS_URL = os.getenv(
    "PROCESSING_JOB_REDIS_URL",
    "redis://localhost:6379/0",
)
PROCESSING_JOB_CHANNEL_PREFIX = "stamp_processing_job"
PROCESSING_JOB_START_DELAY_SECONDS = int(
    os.getenv("PROCESSING_JOB_START_DELAY_SECONDS", "10")
)
