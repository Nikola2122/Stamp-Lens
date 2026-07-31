from decimal import Decimal, InvalidOperation

import requests

from pricing.constants import (
    PRICE_CURRENCY,
    PRICE_REQUEST_TIMEOUT_SECONDS,
    PRICE_SERPAPI_API_KEY,
    PRICE_SERPAPI_EBAY_DOMAIN,
    PRICE_SERPAPI_RESULT_LIMIT,
    PRICE_SERPAPI_SEARCH_URL,
)
from pricing.dtos import EbayListingDTO, SerpApiEbayResultDTO


class SerpApiEbayClient:
    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "StampLens/1.0 (stamp pricing application)",
            }
        )

    def search(
        self,
        search_query: str,
    ) -> SerpApiEbayResultDTO | None:
        if not PRICE_SERPAPI_API_KEY:
            return None

        response = self._session.get(
            PRICE_SERPAPI_SEARCH_URL,
            params={
                "engine": "ebay",
                "ebay_domain": PRICE_SERPAPI_EBAY_DOMAIN,
                "_nkw": search_query,
                "_ipg": PRICE_SERPAPI_RESULT_LIMIT,
                "api_key": PRICE_SERPAPI_API_KEY,
            },
            timeout=PRICE_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise requests.RequestException(data["error"])

        return SerpApiEbayResultDTO(
            listings=self._listings(data),
            raw_result=data,
        )

    @staticmethod
    def _listings(data: dict) -> list[EbayListingDTO]:
        listings = []
        for item in data.get("organic_results", []):
            title = item.get("title")
            url = item.get("link")
            sold_date = item.get("sold_date")
            price = SerpApiEbayClient._extract_price(item.get("price"))
            if not title or not url or price is None:
                continue

            listings.append(
                EbayListingDTO(
                    title=title.strip(),
                    price=price,
                    currency=PRICE_CURRENCY,
                    condition=item.get("condition", ""),
                    sold_date=sold_date,
                    url=url,
                    raw_result=item,
                )
            )
        return listings

    @staticmethod
    def _extract_price(price_data) -> Decimal | None:
        if not isinstance(price_data, dict):
            return None

        value = price_data.get("extracted")
        if value is None:
            return None

        try:
            price = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

        return price if price > 0 else None
