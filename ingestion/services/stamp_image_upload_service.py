import os

from django.core.files.uploadedfile import UploadedFile

from ingestion.models import StampImage
from ingestion.services.stamp_image_service import StampImageService


class StampImageUploadService:

    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]

    def __init__(self):
        self.stamp_image_service = StampImageService()

    def upload_image(self, file: UploadedFile):

        if file is None:
            raise ValueError("File is required")

        extension = os.path.splitext(file.name)[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Only image files are allowed")

        stamp_image = StampImage(
            file=file,
            original_name=file.name,
            extension=extension
        )

        return self.stamp_image_service.create_stamp_image(stamp_image)