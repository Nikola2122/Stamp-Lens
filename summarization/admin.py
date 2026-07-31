from django.contrib import admin

from summarization.models import StampSummary


@admin.register(StampSummary)
class StampSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_recognition",
        "model",
        "created_at",
    )
    search_fields = (
        "stamp_recognition__name",
        "summary",
    )
    readonly_fields = ("created_at", "updated_at")
