from django.db import models

from ingestion.models import StampImage


class StampAnalysis(models.Model):
    stamp_image = models.OneToOneField(
        StampImage,
        on_delete=models.CASCADE,
        related_name="analysis",
    )
    cropped_stamp = models.ImageField(
        upload_to="extraction/stamps/",
    )
    width_mm = models.FloatField()
    height_mm = models.FloatField()
    ocr_text = models.TextField(blank=True)
    image_description = models.CharField(max_length=500, blank=True)
    dominant_colors = models.JSONField(default=list, blank=True)
    raw_result = models.JSONField(default=dict, blank=True)
    extraction_model_version = models.CharField(max_length=100)
    ocr_model_version = models.CharField(max_length=100)
    tagging_model_version = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.stamp_image.original_name}"


class StampTag(models.Model):
    stamp_analysis = models.ForeignKey(
        StampAnalysis,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    confidence = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.confidence:.2f})"
