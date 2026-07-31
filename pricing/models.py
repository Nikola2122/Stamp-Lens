from django.db import models

from recognition.models import StampRecognition


class StampPriceEstimate(models.Model):
    stamp_recognition = models.OneToOneField(
        StampRecognition,
        on_delete=models.CASCADE,
        related_name="price_estimate",
    )
    search_query = models.CharField(max_length=500)
    provider = models.CharField(max_length=100)
    estimated_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    median_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    mean_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    minimum_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    maximum_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    currency = models.CharField(max_length=3)
    confidence = models.CharField(max_length=20)
    comparable_count = models.PositiveIntegerField()
    comparable_sales = models.JSONField(default=list, blank=True)
    raw_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.stamp_recognition}: "
            f"{self.estimated_price} {self.currency}"
        )
