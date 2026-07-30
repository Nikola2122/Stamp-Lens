from dataclasses import dataclass


@dataclass
class RecognitionResultDTO:
    name: str | None
    raw_result: dict
