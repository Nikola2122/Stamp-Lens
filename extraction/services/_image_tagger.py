from functools import cached_property

import cv2
import numpy as np
from PIL import Image

from extraction.constants import (
    MAX_STAMP_TAGS,
    STAMP_TAG_CATEGORIES,
    STAMP_TAG_LABELS,
    TAG_CONFIDENCE_THRESHOLD,
    TAGGING_MODEL_NAME,
)
from extraction.dtos import ImageTaggingDTO, StampTagDTO


class ImageTagger:
    @cached_property
    def _classifier(self):
        from transformers import pipeline

        return pipeline(
            task="zero-shot-image-classification",
            model=TAGGING_MODEL_NAME,
        )

    def process(self, cropped_stamp: np.ndarray) -> ImageTaggingDTO:
        rgb_image = cv2.cvtColor(cropped_stamp, cv2.COLOR_BGR2RGB)
        predictions = self._classifier(
            Image.fromarray(rgb_image),
            candidate_labels=STAMP_TAG_LABELS,
        )

        tags = []
        for prediction in predictions:
            confidence = float(prediction["score"])
            if confidence < TAG_CONFIDENCE_THRESHOLD:
                continue

            name = str(prediction["label"])
            tags.append(
                StampTagDTO(
                    name=name,
                    category=STAMP_TAG_CATEGORIES[name],
                    confidence=round(confidence, 4),
                )
            )
            if len(tags) == MAX_STAMP_TAGS:
                break

        if tags:
            names = [tag.name for tag in tags]
            description = f"Stamp depicting {', '.join(names)}."
        else:
            description = "No recognized subject."

        return ImageTaggingDTO(
            description=description,
            tags=tags,
            model_version=TAGGING_MODEL_NAME,
        )
