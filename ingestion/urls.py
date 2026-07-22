from django.urls import path

from ingestion.views import UploadStampImageView


urlpatterns = [
    path(
        "upload/",
        UploadStampImageView.as_view(),
        name="upload-stamp-image"
    ),
]