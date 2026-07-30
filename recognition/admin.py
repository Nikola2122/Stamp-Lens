from django.contrib import admin

from recognition.models import RecognitionUsage, StampRecognition


@admin.register(StampRecognition)
class StampRecognitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_analysis",
        "name",
        "provider",
        "created_at",
    )
    search_fields = (
        "name",
        "stamp_analysis__stamp_image__original_name",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(RecognitionUsage)
class RecognitionUsageAdmin(admin.ModelAdmin):
    list_display = ("period_start", "request_count", "updated_at")
    readonly_fields = ("period_start", "request_count", "updated_at")
