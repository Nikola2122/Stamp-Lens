import os

from dotenv import load_dotenv


load_dotenv()

A4_SHORT_SIDE_MM = float(os.environ["EXTRACTION_A4_SHORT_SIDE_MM"])
A4_LONG_SIDE_MM = float(os.environ["EXTRACTION_A4_LONG_SIDE_MM"])
EXTRACTION_MODEL_VERSION = os.environ["EXTRACTION_MODEL_VERSION"]
MIN_PAGE_AREA_RATIO = float(os.environ["EXTRACTION_MIN_PAGE_AREA_RATIO"])
MIN_STAMP_AREA_RATIO = float(os.environ["EXTRACTION_MIN_STAMP_AREA_RATIO"])
MAX_STAMP_SIDE_RATIO = float(os.environ["EXTRACTION_MAX_STAMP_SIDE_RATIO"])
PAGE_INSET_RATIO = float(os.environ["EXTRACTION_PAGE_INSET_RATIO"])

OCR_LANGUAGE = os.environ["OCR_LANGUAGE"]
OCR_MODEL_VERSION = os.environ["OCR_MODEL_VERSION"]

TAGGING_MODEL_NAME = os.environ["TAGGING_MODEL_NAME"]
TAG_CONFIDENCE_THRESHOLD = float(os.environ["TAG_CONFIDENCE_THRESHOLD"])
MAX_STAMP_TAGS = int(os.environ["MAX_STAMP_TAGS"])
STAMP_TAG_CATEGORIES = {
    "horse": "animal",
    "bird": "animal",
    "dog": "animal",
    "cat": "animal",
    "fish": "animal",
    "butterfly": "animal",
    "tree": "plant",
    "flower": "plant",
    "person": "person",
    "portrait": "person",
    "building": "architecture",
    "castle": "architecture",
    "monument": "architecture",
    "bridge": "architecture",
    "ship": "transport",
    "train": "transport",
    "airplane": "transport",
    "car": "transport",
    "map": "geography",
    "coat of arms": "symbol",
    "flag": "symbol",
}

STAMP_TAG_LABELS = list(STAMP_TAG_CATEGORIES)
