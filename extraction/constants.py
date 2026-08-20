import os

from dotenv import load_dotenv


load_dotenv()

EXTRACTION_MODEL_VERSION = os.getenv(
    "EXTRACTION_MODEL_VERSION",
    "uniform-surface-v1",
)
MIN_STAMP_AREA_RATIO = float(
    os.getenv("EXTRACTION_MIN_STAMP_AREA_RATIO", "0.005")
)
MAX_STAMP_AREA_RATIO = float(
    os.getenv("EXTRACTION_MAX_STAMP_AREA_RATIO", "0.75")
)
BACKGROUND_BORDER_RATIO = float(
    os.getenv("EXTRACTION_BACKGROUND_BORDER_RATIO", "0.08")
)
BACKGROUND_COLOR_THRESHOLD = float(
    os.getenv("EXTRACTION_BACKGROUND_COLOR_THRESHOLD", "35")
)
BACKGROUND_UNIFORM_RATIO = float(
    os.getenv("EXTRACTION_BACKGROUND_UNIFORM_RATIO", "0.90")
)

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
