"""
Stock Market Tracker - Main Application (improved for Finnhub)
- Uses config.get_finnhub_key() to read the API key
- Adds retry with exponential backoff (tenacity)
- Adds simple caching (cachetools TTLCache) to respect rate limits
- Uses requests.Session for connection pooling
"""

import os
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt
from cachetools import TTLCache, cached

from config import get_finnhub_key, FINNHUB_BASE_URL

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Session for HTTP connections
_session = requests.Session()

# Simple in-memory TTL cache: cache Finnhub quote responses for 60 seconds
_CACHE = TTLCache(maxsize=1024, ttl=60)


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(4))
@cached(_CACHE)
def _fetch_finnhub_quote(symbol: str):
    """Fetch raw quote from Finnhub and cache the result per-symbol.

    Note: token is read at call-time so we don't embed secrets into cache keys.
    """
    token = get_finnhub_key()
    url = f"{FINNHUB_BASE_URL}/quote"
    params = {"symbol": symbol, "token": token}

    logger.debug("Requesting Finnhub for %s", symbol)
    resp = _session.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


class StockTracker:
    """Main class for tracking stock market data (Finnhub-focused improvements)"""

    def __init__(self):
        # Do not raise at init — read key when needed. Keep attributes for compatibility.
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.base_url_finnhub = FINNHUB_BASE_URL
        self.stocks_data = []

    def get_stock_price_finnhub(self, symbol: str):
        """Fetch stock price using Finnhub API with caching and retry.

        Returns a dict with keys compatible with the UI: symbol, price, change, high, low, open, previous_close, timestamp, source
        """
        try:
            data = _fetch_finnhub_quote(symbol)

            # Finnhub returns keys: c (current), h (high), l (low), o (open), pc (previous close)
            if not data or 'c' not in data:
                logger.warning("No Finnhub data for %s: %s", symbol, data)
                return None

            current = data.get('c', 0)
            prev_close = data.get('pc', 0) or 0
            change = None
            try:
                change = float(current) - float(prev_close)
            except Exception:
                change = 0.0

            return {
                'symbol': symbol,
                'price': float(current),
                'high': float(data.get('h', 0) or 0),
                'low': float(data.get('l', 0) or 0),
                'open': float(data.get('o', 0) or 0),
                'previous_close': float(prev_close),
                'change': change,
                'change_percent': f"{(change / prev_close * 100):.2f}%" if prev_close else 'N/A',
                'timestamp': datetime.now().isoformat(),
                'source': 'Finnhub'
            }

        except requests.HTTPError as e:
            logger.error("HTTP error fetching Finnhub for %s: %s", symbol, e)
            return None
        except Exception as e:
            logger.exception("Unexpected error fetching Finnhub for %s: %s", symbol, e)
            return None

    def add_stock(self, symbol: str, source: str = 'finnhub'):
        """Add a stock to the in-memory portfolio. Defaults to Finnhub."""
        source = source.lower() if source else 'finnhub'

        if source == 'finnhub':
            data = self.get_stock_price_finnhub(symbol)
        else:
            logger.error("Unknown source requested: %s", source)
            return

        if data:
            # Keep a consistent shape with previous implementation
            self.stocks_data.append(data)
            logger.info("Added %s: $%s", symbol, data.get('price'))
        else:
            logger.info("Failed to add %s", symbol)

    def get_portfolio(self):
        """Return current portfolio as a pandas DataFrame or empty DataFrame"""
        if not self.stocks_data:
            return pd.DataFrame()
        return pd.DataFrame(self.stocks_data)

    def display_portfolio(self):
        df = self.get_portfolio()
        if df.empty:
            logger.info("Portfolio is empty")
            return
        print(df.to_string(index=False))

    def save_to_csv(self, filename='portfolio.csv'):
        df = self.get_portfolio()
        if not df.empty:
            df.to_csv(filename, index=False)
            logger.info("Saved portfolio to %s", filename)


def main():
    print("🚀 Stock Market Tracker (Finnhub) Started\n")
    tracker = StockTracker()

    if not tracker.finnhub_key:
        print("⚠️  Warning: FINNHUB_API_KEY non configurata. Aggiungi la chiave a .env o come variabile d'ambiente.")

    stocks_to_track = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    for s in stocks_to_track:
        tracker.add_stock(s, source='finnhub')

    tracker.display_portfolio()
    tracker.save_to_csv('portfolio.csv')


if __name__ == '__main__':
    main()
