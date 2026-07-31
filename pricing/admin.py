from django.contrib import admin

from pricing.models import StampPriceEstimate


@admin.register(StampPriceEstimate)
class StampPriceEstimateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_recognition",
        "estimated_price",
        "currency",
        "confidence",
        "comparable_count",
        "created_at",
    )
    search_fields = (
        "search_query",
        "stamp_recognition__name",
    )
    readonly_fields = ("created_at", "updated_at")
