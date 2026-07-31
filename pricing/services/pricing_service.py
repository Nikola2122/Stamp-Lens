from recognition.models import StampRecognition
from pricing.constants import (
    PRICE_NOT_FOUND_MESSAGE,
    PRICE_PROVIDER,
    PRICE_SUCCESS_MESSAGE,
)
from pricing.models import StampPriceEstimate
from pricing.dtos import PriceEstimateServiceResultDTO
from pricing.services._price_estimator import PriceEstimator
from pricing.services._serpapi_ebay_client import SerpApiEbayClient


class PriceEstimateError(RuntimeError):
    pass


class PriceEstimateService:
    """
    Public synchronous facade for stamp price estimation.

    The future background job calls only ``estimate`` with a saved
    ``StampRecognition``. eBay listings are fetched through a dedicated
    SerpApi client, filtered, summarized, and persisted as one estimate.
    """

    def __init__(
        self,
        serpapi_client: SerpApiEbayClient | None = None,
        estimator: PriceEstimator | None = None,
    ):
        self._serpapi_client = serpapi_client or SerpApiEbayClient()
        self._estimator = estimator or PriceEstimator()

    def estimate(
        self,
        stamp_recognition: StampRecognition,
    ) -> PriceEstimateServiceResultDTO:
        if not stamp_recognition.pk:
            raise PriceEstimateError(
                "The stamp recognition must be saved before pricing."
            )
        if not stamp_recognition.name.strip():
            raise PriceEstimateError(
                "The stamp recognition does not contain a name."
            )

        try:
            search_query = stamp_recognition.name.strip()
            serpapi_result = self._serpapi_client.search(
                search_query
            )
            if not serpapi_result:
                return PriceEstimateServiceResultDTO(
                    message=PRICE_NOT_FOUND_MESSAGE,
                    stamp_price_estimate=None,
                )

            estimate = self._estimator.estimate(
                search_query,
                serpapi_result.listings,
            )
            if not estimate:
                return PriceEstimateServiceResultDTO(
                    message=PRICE_NOT_FOUND_MESSAGE,
                    stamp_price_estimate=None,
                )

            stamp_price_estimate, _ = (
                StampPriceEstimate.objects.update_or_create(
                stamp_recognition=stamp_recognition,
                defaults={
                    "search_query": search_query,
                    "provider": PRICE_PROVIDER,
                    "estimated_price": estimate.estimated_price,
                    "median_price": estimate.median_price,
                    "mean_price": estimate.mean_price,
                    "minimum_price": estimate.minimum_price,
                    "maximum_price": estimate.maximum_price,
                    "currency": estimate.currency,
                    "confidence": estimate.confidence,
                    "comparable_count": len(
                        estimate.comparable_sales
                    ),
                    "comparable_sales": estimate.comparable_sales,
                    "raw_result": serpapi_result.raw_result,
                },
            )
            )
            return PriceEstimateServiceResultDTO(
                message=PRICE_SUCCESS_MESSAGE,
                stamp_price_estimate=stamp_price_estimate,
            )
        except PriceEstimateError:
            raise
        except Exception as error:
            raise PriceEstimateError(
                f"Stamp price estimation failed: {error}"
            ) from error
