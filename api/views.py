import json
from dataclasses import asdict
from uuid import UUID

import redis
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from ingestion.models import StampImage

from api.serializers import (
    CompletedProcessingJobSerializer,
    ErrorResponseSerializer,
    ProcessingJobStartSerializer,
    StampImageSerializer,
    StampReportSerializer,
)
from ingestion.services.stamp_image_service import StampImageService
from ingestion.services.stamp_image_upload_service import StampImageUploadService
from processingjob.constants import (
    PROCESSING_JOB_CHANNEL_PREFIX,
    PROCESSING_JOB_REDIS_URL,
)
from processingjob.models import StampProcessingJob
from processingjob.services import (
    ProcessingJobError,
    ProcessingJobReportNotFound,
    ProcessingJobService,
)


class Api(ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_service = StampImageService()
        self.upload_service = StampImageUploadService()
        self.processing_job_service = ProcessingJobService()

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

    def process_image(self, request, image_id):
        try:
            image = self.image_service.get_stamp_image_by_id(image_id)
            result = self.processing_job_service.start(image)
            serializer = ProcessingJobStartSerializer(asdict(result))
            return Response(
                serializer.data,
                status=status.HTTP_202_ACCEPTED,
            )
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
        except ProcessingJobError as error:
            payload = {
                "message": str(error),
                "code": "PROCESSING_JOB_START_FAILED",
                "details": None,
            }
            return Response(
                ErrorResponseSerializer(payload).data,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def get_completed_processing_jobs(self, request, image_id):
        try:
            image = self.image_service.get_stamp_image_by_id(image_id)
            jobs = self.processing_job_service.get_completed_jobs(image)
            serializer = CompletedProcessingJobSerializer(jobs, many=True)
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

    def get_processing_job_report(self, request, job_id):
        try:
            report = self.processing_job_service.get_report(str(job_id))
            serializer = StampReportSerializer(
                report,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ProcessingJobReportNotFound as error:
            payload = {
                "message": str(error),
                "code": "REPORT_NOT_FOUND",
                "details": None,
            }
            return Response(
                ErrorResponseSerializer(payload).data,
                status=status.HTTP_404_NOT_FOUND,
            )


def processing_job_events(request):
    if request.method != "GET":
        return JsonResponse(
            {"message": "Method not allowed", "code": "METHOD_NOT_ALLOWED"},
            status=405,
        )

    channel = request.GET.get("channel", "").strip()
    job_id = _job_id_from_channel(channel)
    job_exists = (
        job_id is not None
        and StampProcessingJob.objects.filter(pk=job_id).exists()
    )
    if not job_exists:
        return JsonResponse(
            {
                "message": "Invalid processing job channel",
                "code": "INVALID_CHANNEL",
            },
            status=400,
        )

    response = StreamingHttpResponse(
        _stream_redis_channel(channel),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def _job_id_from_channel(channel):
    prefix = f"{PROCESSING_JOB_CHANNEL_PREFIX}:"
    if not channel.startswith(prefix):
        return None
    try:
        return UUID(channel.removeprefix(prefix))
    except ValueError:
        return None


def _stream_redis_channel(channel):
    client = redis.Redis.from_url(
        PROCESSING_JOB_REDIS_URL,
        decode_responses=True,
    )
    pubsub = client.pubsub()
    try:
        pubsub.subscribe(channel)
        for redis_message in pubsub.listen():
            if redis_message["type"] != "message":
                continue

            raw_data = redis_message["data"]
            try:
                payload = json.loads(raw_data)
            except (TypeError, json.JSONDecodeError):
                continue

            if payload.get("finished") is True:
                yield f"data: {raw_data}\n\n"
                break

            yield f"data: {raw_data}\n\n"
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()
        client.close()
