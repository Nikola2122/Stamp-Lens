from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from common.responses.error_response import ErrorResponseSerializer
from ingestion.services.stamp_image_upload_service import StampImageUploadService
from ingestion.serializers import StampImageSerializer


class UploadStampImageView(APIView):

    def __init__(self):
        super().__init__()
        self.service = StampImageUploadService()

    def post(self, request):
        try:
            file = request.FILES.get("file")

            image = self.service.upload_image(file)

            return Response(
                StampImageSerializer(image).data,
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            error = {
                "message": str(e),
                "code": "VALIDATION_ERROR",
                "details": None
            }

            return Response(
                ErrorResponseSerializer(error).data,
                status=status.HTTP_400_BAD_REQUEST
            )