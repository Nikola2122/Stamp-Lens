from django.contrib import admin

from report.models import ReportTag, StampReport


class ReportTagInline(admin.TabularInline):
    model = ReportTag
    extra = 0


@admin.register(StampReport)
class StampReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_image",
        "recognized_name",
        "estimated_price",
        "price_currency",
        "created_at",
    )
    search_fields = (
        "recognized_name",
        "stamp_image__original_name",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = (ReportTagInline,)


@admin.register(ReportTag)
class ReportTagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_report",
        "name",
        "category",
        "confidence",
    )
    search_fields = ("name", "category")
