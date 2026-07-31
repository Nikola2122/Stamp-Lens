import re
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean, median

from pricing.dtos import EbayListingDTO, PriceEstimateDTO


class PriceEstimator:
    EXCLUDED_TITLE_WORDS = {
        "album",
        "bulk",
        "collection",
        "copy",
        "facsimile",
        "lot",
        "replica",
        "reprint",
        "reproduction",
    }
    GENERIC_QUERY_WORDS = {
        "a",
        "and",
        "issue",
        "of",
        "postage",
        "stamp",
        "stamps",
        "the",
    }
    MONEY_QUANTUM = Decimal("0.01")

    def estimate(
        self,
        search_query: str,
        listings: list[EbayListingDTO],
    ) -> PriceEstimateDTO | None:
        comparable_listings = self._matching_listings(
            search_query,
            listings,
        )
        if not comparable_listings:
            return None

        comparable_listings = self._remove_price_outliers(
            comparable_listings
        )
        prices = [listing.price for listing in comparable_listings]
        median_price = self._money(Decimal(median(prices)))
        mean_price = self._money(Decimal(mean(prices)))
        minimum_price = self._money(min(prices))
        maximum_price = self._money(max(prices))

        return PriceEstimateDTO(
            estimated_price=median_price,
            median_price=median_price,
            mean_price=mean_price,
            minimum_price=minimum_price,
            maximum_price=maximum_price,
            currency=comparable_listings[0].currency,
            confidence=self._confidence(prices),
            comparable_sales=[
                {
                    "title": listing.title,
                    "price": str(self._money(listing.price)),
                    "currency": listing.currency,
                    "condition": listing.condition,
                    "sold_date": listing.sold_date,
                    "url": listing.url,
                }
                for listing in comparable_listings
            ],
        )

    def _matching_listings(
        self,
        search_query: str,
        listings: list[EbayListingDTO],
    ) -> list[EbayListingDTO]:
        query_words = self._significant_words(search_query)
        matches = []
        for listing in listings:
            title_words = self._words(listing.title)
            if title_words & self.EXCLUDED_TITLE_WORDS:
                continue
            if query_words:
                overlap = len(query_words & title_words) / len(query_words)
                if overlap < 0.35:
                    continue
            matches.append(listing)
        return matches

    def _remove_price_outliers(
        self,
        listings: list[EbayListingDTO],
    ) -> list[EbayListingDTO]:
        if len(listings) < 4:
            return listings

        prices = sorted(listing.price for listing in listings)
        q1 = self._percentile(prices, Decimal("0.25"))
        q3 = self._percentile(prices, Decimal("0.75"))
        iqr = q3 - q1
        lower_bound = max(Decimal("0"), q1 - Decimal("1.5") * iqr)
        upper_bound = q3 + Decimal("1.5") * iqr
        filtered = [
            listing
            for listing in listings
            if lower_bound <= listing.price <= upper_bound
        ]
        return filtered or listings

    @staticmethod
    def _percentile(
        sorted_values: list[Decimal],
        percentile: Decimal,
    ) -> Decimal:
        position = percentile * Decimal(len(sorted_values) - 1)
        lower_index = int(position)
        upper_index = min(lower_index + 1, len(sorted_values) - 1)
        fraction = position - lower_index
        return (
            sorted_values[lower_index]
            + (
                sorted_values[upper_index]
                - sorted_values[lower_index]
            )
            * fraction
        )

    @classmethod
    def _significant_words(cls, value: str) -> set[str]:
        return cls._words(value) - cls.GENERIC_QUERY_WORDS

    @staticmethod
    def _words(value: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", value.casefold()))

    @classmethod
    def _money(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.MONEY_QUANTUM, rounding=ROUND_HALF_UP)

    @staticmethod
    def _confidence(prices: list[Decimal]) -> str:
        count = len(prices)
        if count < 3:
            return "low"

        average = Decimal(mean(prices))
        spread = max(prices) - min(prices)
        relative_spread = spread / average if average else Decimal("1")
        if count >= 8 and relative_spread <= Decimal("1"):
            return "high"
        return "medium"
