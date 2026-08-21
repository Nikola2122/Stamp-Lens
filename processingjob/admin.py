from django.contrib import admin

from processingjob.models import StampProcessingJob


@admin.register(StampProcessingJob)
class StampProcessingJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_image",
        "status",
        "current_step",
        "created_at",
        "finished_at",
    )
    list_filter = ("status", "current_step")
    search_fields = ("id", "celery_task_id", "stamp_image__original_name")
    readonly_fields = ("created_at", "started_at", "finished_at", "updated_at")
