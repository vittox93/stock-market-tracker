import os
from dotenv import load_dotenv

# Load .env from project root if present
load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE_URL = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")


def get_finnhub_key() -> str:
    """Return the configured Finnhub API key or raise an error if missing."""
    key = FINNHUB_API_KEY
    if not key:
        raise RuntimeError("FINNHUB_API_KEY non impostata. Imposta la variabile d'ambiente o scrivila in .env")
    return key
