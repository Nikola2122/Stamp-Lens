import requests

from recognition.models import StampRecognition
from research.constants import (
    RESEARCH_NOT_FOUND_MESSAGE,
    RESEARCH_SUCCESS_MESSAGE,
)
from research.models import StampResearch, StampResearchQA
from research.services._serpapi_client import SerpApiClient
from research.services._wikipedia_client import WikipediaClient


class ResearchError(RuntimeError):
    pass


class ResearchService:
    """
    Public synchronous facade for online stamp research.

    The future background job calls only ``research`` with a saved
    ``StampRecognition``. SerpApi is tried first and Wikipedia is the
    fallback when the selected web page has no usable description.
    """

    def __init__(
        self,
        serpapi_client: SerpApiClient | None = None,
        wikipedia_client: WikipediaClient | None = None,
    ):
        self._serpapi_client = serpapi_client or SerpApiClient()
        self._wikipedia_client = wikipedia_client or WikipediaClient()

    def research(self, stamp_recognition: StampRecognition) -> str:
        if not stamp_recognition.pk:
            raise ResearchError(
                "The stamp recognition must be saved before research."
            )
        if not stamp_recognition.name.strip():
            raise ResearchError(
                "The stamp recognition does not contain a name."
            )

        try:
            search_query = stamp_recognition.name.strip()
            serpapi_result = None
            try:
                serpapi_result = self._serpapi_client.search(search_query)
            except requests.RequestException:
                pass

            result = None
            if serpapi_result and serpapi_result.description:
                result = {
                    "source_title": serpapi_result.source_title,
                    "source_url": serpapi_result.source_url,
                    "description": serpapi_result.description,
                    "wikipedia_raw_result": {},
                }
            else:
                wikipedia_result = self._wikipedia_client.find_description(
                    search_query
                )
                if wikipedia_result:
                    result = {
                        "source_title": wikipedia_result.source_title,
                        "source_url": wikipedia_result.source_url,
                        "description": wikipedia_result.description,
                        "wikipedia_raw_result": (
                            wikipedia_result.raw_result
                        ),
                    }

            if result is None:
                return RESEARCH_NOT_FOUND_MESSAGE

            stamp_research, _ = StampResearch.objects.update_or_create(
                stamp_recognition=stamp_recognition,
                defaults={
                    "search_query": search_query,
                    "source_title": result["source_title"],
                    "source_url": result["source_url"],
                    "description": result["description"],
                    "organic_results": (
                        serpapi_result.organic_results
                        if serpapi_result
                        else []
                    ),
                    "raw_result": {
                        "serpapi": (
                            serpapi_result.raw_result
                            if serpapi_result
                            else {}
                        ),
                        "wikipedia": result[
                            "wikipedia_raw_result"
                        ],
                    },
                },
            )
            related_questions = (
                serpapi_result.related_questions
                if serpapi_result
                else []
            )
            StampResearchQA.objects.update_or_create(
                stamp_research=stamp_research,
                defaults={
                    "questions": [
                        item["question"]
                        for item in related_questions
                    ],
                    "answers": [
                        item.get("answer", "")
                        for item in related_questions
                    ],
                },
            )
            return RESEARCH_SUCCESS_MESSAGE
        except ResearchError:
            raise
        except Exception as error:
            raise ResearchError(
                f"Stamp research failed: {error}"
            ) from error
