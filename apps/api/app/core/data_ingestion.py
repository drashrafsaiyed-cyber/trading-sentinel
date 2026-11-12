"""Data ingestion from external sources (yfinance, APIs)"""
import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Fetch and process market data"""

    @staticmethod
    async def fetch_yfinance(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch data from yfinance

        Args:
            symbol: Stock/crypto symbol (e.g., 'AAPL', 'BTC-USD')
            period: '1mo', '3mo', '6mo', '1y'
            interval: '1m', '5m', '15m', '1h', '1d'
        """
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)

            if data.empty:
                logger.warning(f"No data for {symbol}")
                return None

            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            data = data[['open', 'high', 'low', 'close', 'volume']]
            data = data.dropna()

            logger.info(f"Fetched {len(data)} candles for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    @staticmethod
    async def fetch_latest(symbol: str, lookback_days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch latest data for fast analysis"""
        data = await DataIngestionService.fetch_yfinance(symbol, period="1y", interval="1d")
        if data is not None:
            data = data.tail(lookback_days)
        return data

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate if symbol exists"""
        try:
            data = yf.download(symbol, period="1d", interval="1d", progress=False)
            return not data.empty
        except:
            return False


class DataValidation:
    """Validate OHLCV data quality"""

    @staticmethod
    def validate_candle(o: float, h: float, l: float, c: float, v: float) -> bool:
        """Check if OHLCV values make sense"""
        # High should be >= all prices
        if not (h >= o and h >= l and h >= c):
            return False

        # Low should be <= all prices
        if not (l <= o and l <= h and l <= c):
            return False

        # Volume should be positive
        if v <= 0:
            return False

        return True
