from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pricing.models import StampPriceEstimate


@dataclass
class PriceEstimateServiceResultDTO:
    message: str
    stamp_price_estimate: "StampPriceEstimate | None"


@dataclass
class EbayListingDTO:
    title: str
    price: Decimal
    currency: str
    condition: str
    sold_date: str | None
    url: str
    raw_result: dict


@dataclass
class SerpApiEbayResultDTO:
    listings: list[EbayListingDTO]
    raw_result: dict


@dataclass
class PriceEstimateDTO:
    estimated_price: Decimal
    median_price: Decimal
    mean_price: Decimal
    minimum_price: Decimal
    maximum_price: Decimal
    currency: str
    confidence: str
    comparable_sales: list[dict]
