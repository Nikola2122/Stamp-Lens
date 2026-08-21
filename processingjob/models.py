import uuid

from django.db import models


class ProcessingJobStatus(models.TextChoices):
    INITIATED = "initiated", "Initiated"
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    SUCCEEDED = "succeeded", "Succeeded"
    SUCCEEDED_WITH_WARNINGS = (
        "succeeded_with_warnings",
        "Succeeded with warnings",
    )
    FAILED = "failed", "Failed"


class ProcessingStep(models.TextChoices):
    EXTRACTION = "extraction", "Extraction"
    RECOGNITION = "recognition", "Recognition"
    RESEARCH = "research", "Research"
    PRICING = "pricing", "Pricing"
    SUMMARY = "summary", "Summary"
    FINAL_REPORT = "final_report", "Final report"


class ProcessingStepStatus(models.TextChoices):
    SUCCESSFUL = "successful", "Successful"
    SUCCESSFUL_WITH_WARNING = (
        "successful_with_warning",
        "Successful with warning",
    )
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class StampProcessingJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stamp_image = models.ForeignKey(
        "ingestion.StampImage",
        on_delete=models.CASCADE,
        related_name="processing_jobs",
    )
    report = models.OneToOneField(
        "report.StampReport",
        on_delete=models.SET_NULL,
        related_name="processing_job",
        null=True,
        blank=True,
    )
    celery_task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32,
        choices=ProcessingJobStatus.choices,
        default=ProcessingJobStatus.INITIATED,
    )
    current_step = models.CharField(
        max_length=32,
        choices=ProcessingStep.choices,
        null=True,
        blank=True,
    )
    step_statuses = models.JSONField(default=dict, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def redis_channel(self) -> str:
        from processingjob.constants import PROCESSING_JOB_CHANNEL_PREFIX

        return f"{PROCESSING_JOB_CHANNEL_PREFIX}:{self.id}"

    def __str__(self):
        return f"Processing job {self.id} for {self.stamp_image}"
