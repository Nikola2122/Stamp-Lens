from django.db import models

from recognition.models import StampRecognition


class StampSummary(models.Model):
    stamp_recognition = models.OneToOneField(
        StampRecognition,
        on_delete=models.CASCADE,
        related_name="summary",
    )
    summary = models.TextField()
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    input_snapshot = models.JSONField(default=dict)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI summary for {self.stamp_recognition}"
