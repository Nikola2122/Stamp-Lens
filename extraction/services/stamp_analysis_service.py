from uuid import uuid4

import cv2
from django.core.files.base import ContentFile
from django.db import transaction

from extraction.dtos import A4ExtractionDTO, ImageTaggingDTO, OCRResultDTO
from extraction.models import StampAnalysis, StampTag
from ingestion.models import StampImage


class StampAnalysisService:
    @transaction.atomic
    def save(
        self,
        stamp_image: StampImage,
        extraction_result: A4ExtractionDTO,
        ocr_result: OCRResultDTO,
        tagging_result: ImageTaggingDTO,
    ) -> None:
        encoded_successfully, encoded_crop = cv2.imencode(
            ".png",
            extraction_result.cropped_stamp,
        )
        if not encoded_successfully:
            raise ValueError("The extracted stamp crop could not be encoded.")

        analysis, _ = StampAnalysis.objects.get_or_create(
            stamp_image=stamp_image,
            defaults={
                "width_mm": extraction_result.width_mm,
                "height_mm": extraction_result.height_mm,
                "extraction_model_version": extraction_result.model_version,
                "ocr_model_version": ocr_result.model_version,
                "tagging_model_version": tagging_result.model_version,
            },
        )

        analysis.width_mm = extraction_result.width_mm
        analysis.height_mm = extraction_result.height_mm
        analysis.ocr_text = ocr_result.text
        analysis.image_description = tagging_result.description
        analysis.dominant_colors = extraction_result.dominant_colors
        analysis.raw_result = {
            "extraction": {
                "a4_corners": extraction_result.a4_corners,
                "a4_width_mm": extraction_result.a4_width_mm,
                "a4_height_mm": extraction_result.a4_height_mm,
                "corrected_page_width_px": (
                    extraction_result.corrected_page_width_px
                ),
                "corrected_page_height_px": (
                    extraction_result.corrected_page_height_px
                ),
                "stamp_box": {
                    "x": extraction_result.stamp_box.x,
                    "y": extraction_result.stamp_box.y,
                    "width": extraction_result.stamp_box.width,
                    "height": extraction_result.stamp_box.height,
                },
            },
            "ocr": {
                "confidence": ocr_result.confidence,
                "regions": [
                    {
                        "text": region.text,
                        "confidence": region.confidence,
                        "polygon": region.polygon,
                    }
                    for region in ocr_result.regions
                ],
            },
            "tagging": {
                "tags": [
                    {
                        "name": tag.name,
                        "category": tag.category,
                        "confidence": tag.confidence,
                    }
                    for tag in tagging_result.tags
                ],
            },
        }
        analysis.extraction_model_version = extraction_result.model_version
        analysis.ocr_model_version = ocr_result.model_version
        analysis.tagging_model_version = tagging_result.model_version
        analysis.cropped_stamp.save(
            f"stamp-{stamp_image.pk}-{uuid4().hex}.png",
            ContentFile(encoded_crop.tobytes()),
            save=False,
        )
        analysis.save()

        analysis.tags.all().delete()
        StampTag.objects.bulk_create(
            StampTag(
                stamp_analysis=analysis,
                name=tag.name,
                category=tag.category,
                confidence=tag.confidence,
            )
            for tag in tagging_result.tags
        )
