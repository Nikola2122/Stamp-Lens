from django.contrib import admin

from research.models import StampResearch, StampResearchQA


@admin.register(StampResearch)
class StampResearchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_recognition",
        "source_title",
        "created_at",
    )
    search_fields = (
        "search_query",
        "source_title",
        "stamp_recognition__name",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(StampResearchQA)
class StampResearchQAAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "stamp_research",
        "question_count",
        "created_at",
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Questions")
    def question_count(self, obj):
        return len(obj.questions)
