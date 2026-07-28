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
