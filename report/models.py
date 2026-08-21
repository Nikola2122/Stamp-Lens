from django.contrib.postgres.fields import ArrayField
from django.db import models

from ingestion.models import StampImage


class StampReport(models.Model):
    stamp_image = models.ForeignKey(
        StampImage,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    cropped_stamp = models.ImageField(
        upload_to="report/stamps/",
    )
    width_mm = models.FloatField()
    height_mm = models.FloatField()
    ocr_text = models.TextField(blank=True)
    dominant_colors = models.JSONField(default=list, blank=True)

    recognized_name = models.CharField(max_length=500, blank=True)

    research_source_url = models.URLField(max_length=2000, blank=True)
    research_description = models.TextField(blank=True)
    research_questions = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True,
    )
    research_answers = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True,
    )

    estimated_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    median_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    mean_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    minimum_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    maximum_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price_currency = models.CharField(max_length=3, blank=True)
    price_confidence = models.CharField(max_length=20, blank=True)

    summary = models.TextField(blank=True)
    summary_provider = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report for {self.recognized_name or self.stamp_image}"


class ReportTag(models.Model):
    stamp_report = models.ForeignKey(
        StampReport,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    confidence = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.confidence:.2f})"
