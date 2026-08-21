from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessingJobStartDTO:
    job_id: str
    celery_task_id: str
    channel: str
    delay_seconds: int


@dataclass
class CompletedProcessingJobDTO:
    job_id: str
    status: str
    created_at: datetime
