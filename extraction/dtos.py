from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from extraction.models import StampAnalysis


@dataclass
class ExtractionServiceResultDTO:
    message: str
    stamp_analysis: "StampAnalysis"


@dataclass
class StampBoxDTO:
    x: int
    y: int
    width: int
    height: int


@dataclass
class SurfaceExtractionDTO:
    cropped_stamp: np.ndarray
    width_mm: float
    height_mm: float
    dominant_colors: list[str]
    model_version: str
    image_width_px: int
    image_height_px: int
    background_color: str
    background_uniform_ratio: float
    stamp_box: StampBoxDTO


# Kept as an alias so callers written for the first A4 implementation do not
# break while the stored database schema is migrated independently.
A4ExtractionDTO = SurfaceExtractionDTO


@dataclass
class OCRRegionDTO:
    text: str
    confidence: float
    polygon: list


@dataclass
class OCRResultDTO:
    text: str
    confidence: float
    regions: list[OCRRegionDTO]
    model_version: str


@dataclass
class StampTagDTO:
    name: str
    category: str
    confidence: float


@dataclass
class ImageTaggingDTO:
    description: str
    tags: list[StampTagDTO]
    model_version: str
