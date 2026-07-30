import json

import requests
from bs4 import BeautifulSoup

from research.constants import (
    RESEARCH_HTTP_USER_AGENT,
    RESEARCH_REQUEST_TIMEOUT_SECONDS,
)


class PageDescriptionExtractor:
    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": RESEARCH_HTTP_USER_AGENT,
            }
        )

    def extract_english(self, url: str) -> str:
        response = self._session.get(
            url,
            timeout=RESEARCH_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        if "html" not in response.headers.get("Content-Type", "").lower():
            return ""

        soup = BeautifulSoup(response.text, "html.parser")
        page_language = (
            soup.html.get("lang", "").strip().casefold()
            if soup.html
            else ""
        )
        if page_language and not page_language.startswith("en"):
            return ""

        description = self._visible_description(soup)
        if description and self._is_english(description):
            return description

        description = self._meta_description(soup)
        if description and self._is_english(description):
            return description

        description = self._json_ld_description(soup)
        if description and self._is_english(description):
            return description

        paragraphs = []
        character_count = 0
        for paragraph in soup.find_all("p"):
            text = " ".join(paragraph.get_text(" ", strip=True).split())
            if len(text) < 80:
                continue
            paragraphs.append(text)
            character_count += len(text)
            if character_count >= 1200:
                break
        description = "\n\n".join(paragraphs)
        return description if self._is_english(description) else ""

    @staticmethod
    def _visible_description(soup: BeautifulSoup) -> str:
        description_label = soup.find(id="fileinfotpl_desc")
        if not description_label:
            return ""

        description_row = description_label.find_parent("tr")
        if not description_row:
            return ""

        english_description = description_row.select_one(
            '.description[lang^="en"]'
        )
        if not english_description:
            return ""

        language_label = english_description.select_one(".language")
        if language_label:
            language_label.decompose()
        return " ".join(
            english_description.get_text(" ", strip=True).split()
        )

    @staticmethod
    def _meta_description(soup: BeautifulSoup) -> str:
        for attributes in (
            {"property": "og:description"},
            {"name": "description"},
        ):
            tag = soup.find("meta", attrs=attributes)
            if tag and tag.get("content"):
                return " ".join(tag["content"].split())
        return ""

    def _json_ld_description(self, soup: BeautifulSoup) -> str:
        for script in soup.find_all(
            "script",
            attrs={"type": "application/ld+json"},
        ):
            try:
                data = json.loads(script.string or "")
            except (TypeError, json.JSONDecodeError):
                continue
            description = self._find_description(data)
            if description:
                return " ".join(description.split())
        return ""

    def _find_description(self, value) -> str:
        if isinstance(value, dict):
            description = value.get("description")
            if isinstance(description, str) and description.strip():
                return description.strip()
            for nested_value in value.values():
                found = self._find_description(nested_value)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = self._find_description(item)
                if found:
                    return found
        return ""

    @staticmethod
    def _is_english(text: str) -> bool:
        latin_count = sum(
            character.isascii() and character.isalpha()
            for character in text
        )
        cyrillic_count = sum(
            "\u0400" <= character <= "\u04ff"
            for character in text
        )
        return bool(latin_count) and cyrillic_count <= latin_count * 0.15
