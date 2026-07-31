import os


PRICE_SERPAPI_API_KEY = os.getenv("PRICE_SERPAPI_API_KEY", "")
PRICE_SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
PRICE_SERPAPI_EBAY_DOMAIN = "ebay.com"
PRICE_SERPAPI_RESULT_LIMIT = 200
PRICE_REQUEST_TIMEOUT_SECONDS = 15
PRICE_PROVIDER = "serpapi_ebay"
PRICE_CURRENCY = "USD"

PRICE_SUCCESS_MESSAGE = "Stamp price estimate completed successfully."
PRICE_NOT_FOUND_MESSAGE = (
    "Stamp price estimate completed with warning: "
    "no useful comparable listings were found."
)
