A4_SHORT_SIDE_MM = 210.0
A4_LONG_SIDE_MM = 297.0

EXTRACTION_MODEL_VERSION = "a4-contour-v1"
OCR_LANGUAGE = "en"
OCR_MODEL_VERSION = "PP-OCRv6"
TAGGING_MODEL_NAME = "openai/clip-vit-base-patch32"
TAG_CONFIDENCE_THRESHOLD = 0.08
MAX_STAMP_TAGS = 3

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
