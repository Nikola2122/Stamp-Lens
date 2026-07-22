from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    code = serializers.CharField(required=False, allow_null=True)
    details = serializers.JSONField(required=False, allow_null=True)