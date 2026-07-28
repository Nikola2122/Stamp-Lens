from dataclasses import dataclass

import numpy as np


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
