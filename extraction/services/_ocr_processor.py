from functools import cached_property

import numpy as np

from extraction.constants import OCR_LANGUAGE, OCR_MODEL_VERSION
from extraction.dtos import OCRRegionDTO, OCRResultDTO


class OCRProcessor:
    @cached_property
    def _engine(self):
        from paddleocr import PaddleOCR

        return PaddleOCR(
            lang=OCR_LANGUAGE,
            ocr_version=OCR_MODEL_VERSION,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            enable_mkldnn=False,
        )

    def process(self, cropped_stamp: np.ndarray) -> OCRResultDTO:
        predictions = self._engine.predict(cropped_stamp)
        texts = []
        scores = []
        regions = []

        for prediction in predictions:
            payload = getattr(prediction, "json", prediction)
            if callable(payload):
                payload = payload()
            payload = self._json_safe(payload)
            data = payload.get("res", payload) if isinstance(payload, dict) else {}

            result_texts = data.get("rec_texts", [])
            result_scores = data.get("rec_scores", [])
            result_polygons = data.get("rec_polys", data.get("dt_polys", []))

            for index, text in enumerate(result_texts):
                normalized_text = str(text).strip()
                if not normalized_text:
                    continue

                score = (
                    float(result_scores[index])
                    if index < len(result_scores)
                    else 0.0
                )
                polygon = (
                    result_polygons[index]
                    if index < len(result_polygons)
                    else []
                )
                texts.append(normalized_text)
                scores.append(score)
                regions.append(
                    OCRRegionDTO(
                        text=normalized_text,
                        confidence=round(score, 4),
                        polygon=self._json_safe(polygon),
                    )
                )

        return OCRResultDTO(
            text=" ".join(texts),
            confidence=(
                round(sum(scores) / len(scores), 4)
                if scores
                else 0.0
            ),
            regions=regions,
            model_version=OCR_MODEL_VERSION,
        )

    @classmethod
    def _json_safe(cls, value):
        if isinstance(value, dict):
            return {
                str(key): cls._json_safe(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [cls._json_safe(item) for item in value]
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        return value
