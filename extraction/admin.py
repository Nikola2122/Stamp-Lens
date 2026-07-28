from django.contrib import admin

from extraction.models import StampAnalysis, StampTag


class StampTagInline(admin.TabularInline):
    model = StampTag
    extra = 0
    readonly_fields = ("name", "category", "confidence")


@admin.register(StampAnalysis)
class StampAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_image",
        "width_mm",
        "height_mm",
        "updated_at",
    )
    search_fields = ("stamp_image__original_name", "ocr_text")
    readonly_fields = ("created_at", "updated_at")
    inlines = (StampTagInline,)


@admin.register(StampTag)
class StampTagAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "confidence", "stamp_analysis")
    list_filter = ("category",)
    search_fields = ("name", "stamp_analysis__stamp_image__original_name")
