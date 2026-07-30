import os


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_RECOGNITION_MODEL = os.getenv(
    "GEMINI_RECOGNITION_MODEL",
    "gemini-3.5-flash",
)
RECOGNITION_PROVIDER = f"google-gemini/{GEMINI_RECOGNITION_MODEL}"
RECOGNITION_MONTHLY_REQUEST_LIMIT = int(
    os.getenv("RECOGNITION_MONTHLY_REQUEST_LIMIT", "900")
)

GENERIC_RECOGNITION_NAMES = {
    "postage stamp",
    "postage stamps",
    "stamp",
    "stamps",
}

RECOGNITION_SUCCESS_MESSAGE = "Stamp recognition completed successfully."
RECOGNITION_NOT_FOUND_MESSAGE = (
    "Stamp recognition completed with warning: "
    "no meaningful stamp name was found."
)
