import requests

from research.constants import (
    RESEARCH_HTTP_USER_AGENT,
    RESEARCH_REQUEST_TIMEOUT_SECONDS,
    SERPAPI_API_KEY,
    SERPAPI_RESULT_LIMIT,
    SERPAPI_SEARCH_URL,
)
from research.dtos import SerpApiResultDTO
from research.services._page_description_extractor import (
    PageDescriptionExtractor,
)


class SerpApiClient:
    def __init__(
        self,
        session: requests.Session | None = None,
        page_extractor: PageDescriptionExtractor | None = None,
    ):
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": RESEARCH_HTTP_USER_AGENT,
            }
        )
        self._page_extractor = (
            page_extractor or PageDescriptionExtractor()
        )

    def search(self, search_query: str) -> SerpApiResultDTO | None:
        if not SERPAPI_API_KEY:
            return None

        response = self._session.get(
            SERPAPI_SEARCH_URL,
            params={
                "engine": "google",
                "q": search_query,
                "api_key": SERPAPI_API_KEY,
                "google_domain": "google.com",
                "hl": "en",
                "gl": "us",
            },
            timeout=RESEARCH_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise requests.RequestException(data["error"])

        organic_results = self._organic_results(data)
        related_questions = self._related_questions(data)

        source_title = ""
        source_url = ""
        description = ""
        for organic_result in organic_results:
            try:
                description = self._page_extractor.extract_english(
                    organic_result["url"]
                )
            except requests.RequestException:
                continue
            if description:
                source_title = organic_result["title"]
                source_url = organic_result["url"]
                break

        return SerpApiResultDTO(
            organic_results=organic_results,
            related_questions=related_questions,
            raw_result=data,
            source_title=source_title,
            source_url=source_url,
            description=description,
        )

    @staticmethod
    def _organic_results(data: dict) -> list[dict]:
        results = []
        for item in data.get("organic_results", [])[
            :SERPAPI_RESULT_LIMIT
        ]:
            title = item.get("title")
            url = item.get("link")
            if not title or not url:
                continue
            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": item.get("snippet", ""),
                }
            )
        return results

    @staticmethod
    def _related_questions(data: dict) -> list[dict]:
        questions = []
        for item in data.get("related_questions", []):
            question = item.get("question")
            answer = item.get("snippet") or item.get("answer")
            if not question or not answer:
                continue
            questions.append(
                {
                    "question": question,
                    "answer": answer,
                    "source_url": item.get("link", ""),
                }
            )
        return questions
