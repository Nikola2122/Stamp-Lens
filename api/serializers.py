from rest_framework import serializers

from ingestion.models import StampImage


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