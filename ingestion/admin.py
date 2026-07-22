from django.contrib import admin

from ingestion.models import StampImage


@admin.register(StampImage)
class StampImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_name",
        "extension",
        "uploaded_at",
    )

    search_fields = (
        "original_name",
    )

    readonly_fields = (
        "uploaded_at",
    )