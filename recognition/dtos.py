from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recognition.models import StampRecognition


@dataclass
class RecognitionServiceResultDTO:
    message: str
    stamp_recognition: "StampRecognition | None"


@dataclass
class RecognitionResultDTO:
    name: str | None
    raw_result: dict
