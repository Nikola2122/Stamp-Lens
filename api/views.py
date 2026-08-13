from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from ingestion.models import StampImage

from api.serializers import StampImageSerializer, ErrorResponseSerializer
from ingestion.services.stamp_image_service import StampImageService
from ingestion.services.stamp_image_upload_service import StampImageUploadService


class Api(ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_service = StampImageService()
        self.upload_service = StampImageUploadService()

    def get_all_images(self, request):
        images = self.image_service.get_all_stamp_images()
        serializer = StampImageSerializer(
            images,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_image(self, request, image_id):
        try:
            image = self.image_service.get_stamp_image_by_id(image_id)
            serializer = StampImageSerializer(
                image,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StampImage.DoesNotExist:
            payload = {
                "message": "Image not found",
                "code": "NOT_FOUND",
                "details": None,
            }
            return Response(
                ErrorResponseSerializer(payload).data,
                status=status.HTTP_404_NOT_FOUND,
            )

    def upload_image(self, request):
        try:
            image = self.upload_service.upload_image(request.FILES.get("file"))
            serializer = StampImageSerializer(
                image,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as error:
            payload = {
                "message": str(error),
                "code": "VALIDATION_ERROR",
                "details": None,
            }
            return Response(
                ErrorResponseSerializer(payload).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete_image(self, request, image_id):
        try:
            self.image_service.delete_stamp_image(image_id)
            return Response(status=status.HTTP_200_OK)
        except StampImage.DoesNotExist:
            payload = {
                "message": "Image not found",
                "code": "NOT_FOUND",
                "details": None,
            }
            return Response(
                ErrorResponseSerializer(payload).data,
                status=status.HTTP_404_NOT_FOUND,
            )
