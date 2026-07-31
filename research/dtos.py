from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from research.models import StampResearch


@dataclass
class ResearchServiceResultDTO:
    message: str
    stamp_research: "StampResearch | None"


@dataclass
class ResearchResultDTO:
    search_query: str
    source_title: str
    source_url: str
    description: str
    raw_result: dict


@dataclass
class SerpApiResultDTO:
    organic_results: list[dict]
    related_questions: list[dict]
    raw_result: dict
    source_title: str = ""
    source_url: str = ""
    description: str = ""
