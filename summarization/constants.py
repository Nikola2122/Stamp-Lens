import os


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_SUMMARY_MODEL = os.getenv(
    "GEMINI_SUMMARY_MODEL",
    "gemini-3.5-flash",
)
SUMMARY_PROVIDER = f"google-gemini/{GEMINI_SUMMARY_MODEL}"

SUMMARY_SUCCESS_MESSAGE = "Stamp summary completed successfully."
