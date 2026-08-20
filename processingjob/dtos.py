from dataclasses import dataclass


@dataclass
class ProcessingJobStartDTO:
    job_id: str
    celery_task_id: str
    channel: str
    delay_seconds: int
