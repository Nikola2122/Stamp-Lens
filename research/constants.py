import os


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
SERPAPI_RESULT_LIMIT = 5

WIKIPEDIA_SEARCH_URL = (
    "https://en.wikipedia.org/w/rest.php/v1/search/page"
)
WIKIPEDIA_ACTION_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_ARTICLE_BASE_URL = "https://en.wikipedia.org/wiki/"
WIKIPEDIA_USER_AGENT = os.getenv(
    "WIKIPEDIA_USER_AGENT",
    "StampLens/1.0 (stamp research application)",
)
RESEARCH_REQUEST_TIMEOUT_SECONDS = 15
RESEARCH_HTTP_USER_AGENT = WIKIPEDIA_USER_AGENT

RESEARCH_SUCCESS_MESSAGE = "Stamp research completed successfully."
RESEARCH_NOT_FOUND_MESSAGE = (
    "Stamp research completed with warning: "
    "no useful online description was found."
)
