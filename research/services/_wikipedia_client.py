from urllib.parse import quote

import requests

from research.constants import (
    RESEARCH_REQUEST_TIMEOUT_SECONDS,
    WIKIPEDIA_ACTION_API_URL,
    WIKIPEDIA_ARTICLE_BASE_URL,
    WIKIPEDIA_SEARCH_URL,
    WIKIPEDIA_USER_AGENT,
)
from research.dtos import ResearchResultDTO


class WikipediaClient:
    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": WIKIPEDIA_USER_AGENT,
            }
        )

    def find_description(
        self,
        search_query: str,
    ) -> ResearchResultDTO | None:
        search_data = self._search(search_query)
        pages = search_data.get("pages", [])
        if not pages:
            return None

        best_match = pages[0]
        page_id = best_match.get("id")
        article_title = best_match.get("title")
        article_key = best_match.get("key")
        if page_id is None or not article_title or not article_key:
            return None

        extract_data = self._get_extract(page_id)
        extracted_pages = extract_data.get("query", {}).get("pages", [])
        page_data = extracted_pages[0] if extracted_pages else {}
        description = page_data.get("extract", "").strip()
        if not description:
            return None

        return ResearchResultDTO(
            search_query=search_query,
            source_title="Wikipedia",
            source_url=(
                f"{WIKIPEDIA_ARTICLE_BASE_URL}"
                f"{quote(article_key, safe='')}"
            ),
            description=description,
            raw_result={
                "search": search_data,
                "extract": extract_data,
            },
        )

    def _search(self, search_query: str) -> dict:
        response = self._session.get(
            WIKIPEDIA_SEARCH_URL,
            params={
                "q": search_query,
                "limit": 1,
            },
            timeout=RESEARCH_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def _get_extract(self, page_id: int) -> dict:
        response = self._session.get(
            WIKIPEDIA_ACTION_API_URL,
            params={
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "pageids": page_id,
            },
            timeout=RESEARCH_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
