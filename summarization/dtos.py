from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from summarization.models import StampSummary


@dataclass
class GeminiSummaryResultDTO:
    summary: str
    raw_result: dict


@dataclass
class SummaryServiceResultDTO:
    message: str
    stamp_summary: "StampSummary"
