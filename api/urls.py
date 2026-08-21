from django.urls import path

from api.views import Api, processing_job_events


app_name = "api"

urlpatterns = [
    path(
        "images/",
        Api.as_view({"get": "get_all_images"}),
        name="images",
    ),
    path(
        "images/<int:image_id>/",
        Api.as_view({"get": "get_image", "delete": "delete_image"}),
        name="image-detail",
    ),
    path(
        "images/upload/",
        Api.as_view({"post": "upload_image"}),
        name="image-upload",
    ),
    path(
        "images/<int:image_id>/process/",
        Api.as_view({"post": "process_image"}),
        name="image-process",
    ),
    path(
        "images/<int:image_id>/processing-jobs/",
        Api.as_view({"get": "get_completed_processing_jobs"}),
        name="image-processing-jobs",
    ),
    path(
        "jobs/<uuid:job_id>/report/",
        Api.as_view({"get": "get_processing_job_report"}),
        name="processing-job-report",
    ),
    path(
        "jobs/events/",
        processing_job_events,
        name="processing-job-events",
    ),
]
