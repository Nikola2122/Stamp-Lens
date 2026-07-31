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
class A4ExtractionDTO:
    cropped_stamp: np.ndarray
    width_mm: float
    height_mm: float
    dominant_colors: list[str]
    model_version: str
    a4_corners: list[list[float]]
    a4_width_mm: float
    a4_height_mm: float
    corrected_page_width_px: int
    corrected_page_height_px: int
    stamp_box: StampBoxDTO


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
