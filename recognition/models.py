from django.db import models

from extraction.models import StampAnalysis


class StampRecognition(models.Model):
    stamp_analysis = models.OneToOneField(
        StampAnalysis,
        on_delete=models.CASCADE,
        related_name="recognition",
    )
    name = models.CharField(max_length=500)
    provider = models.CharField(max_length=100)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RecognitionUsage(models.Model):
    period_start = models.DateField()
    request_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Gemini recognition usage for {self.period_start:%Y-%m}: "
            f"{self.request_count}"
        )
