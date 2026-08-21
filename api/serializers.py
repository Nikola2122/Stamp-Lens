from rest_framework import serializers

from ingestion.models import StampImage
from report.models import ReportTag, StampReport


class StampImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StampImage
        fields = [
            "id",
            "original_name",
            "file",
            "extension",
            "uploaded_at",
        ]


class ErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    code = serializers.CharField(required=False, allow_null=True)
    details = serializers.JSONField(required=False, allow_null=True)


class ProcessingJobStartSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    celery_task_id = serializers.CharField()
    channel = serializers.CharField()
    delay_seconds = serializers.IntegerField()


class CompletedProcessingJobSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class ReportTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTag
        fields = ["id", "name", "category", "confidence"]


class StampReportSerializer(serializers.ModelSerializer):
    tags = ReportTagSerializer(many=True, read_only=True)

    class Meta:
        model = StampReport
        fields = [
            "id",
            "stamp_image",
            "cropped_stamp",
            "width_mm",
            "height_mm",
            "ocr_text",
            "dominant_colors",
            "recognized_name",
            "research_source_url",
            "research_description",
            "research_questions",
            "research_answers",
            "estimated_price",
            "median_price",
            "mean_price",
            "minimum_price",
            "maximum_price",
            "price_currency",
            "price_confidence",
            "summary",
            "summary_provider",
            "tags",
            "created_at",
            "updated_at",
        ]
