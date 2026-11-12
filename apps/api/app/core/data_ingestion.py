"""Data ingestion from external sources (yfinance)."""
import asyncio
import logging
from typing import Optional
import pandas as pd
import yfinance as yf
from app.config import settings
from app.core import mock_data

logger = logging.getLogger(__name__)


def _normalize(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Flatten yfinance output to lowercase open/high/low/close/volume."""
    if df is None or df.empty:
        return None

    # yfinance can return a MultiIndex (field, ticker) for single symbols
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)

    df.columns = [str(c).lower() for c in df.columns]
    needed = ["open", "high", "low", "close", "volume"]
    if not all(c in df.columns for c in needed):
        logger.warning("Missing OHLCV columns, got: %s", list(df.columns))
        return None

    df = df[needed].dropna()
    return df if not df.empty else None


class DataIngestionService:
    """Fetch and process market data (runs blocking yfinance off the event loop)."""

    @staticmethod
    async def fetch_yfinance(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        if settings.data_source == "mock":
            days = {"5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}.get(period, 365)
            return mock_data.generate(symbol, days=max(days, 60))

        def _download():
            return yf.download(
                symbol, period=period, interval=interval,
                progress=False, auto_adjust=True, threads=False,
            )
        try:
            raw = await asyncio.to_thread(_download)
            df = _normalize(raw)
            if df is None:
                logger.warning("No usable data for %s", symbol)
                return None
            logger.info("Fetched %d candles for %s", len(df), symbol)
            return df
        except Exception as e:  # noqa: BLE001
            logger.error("Error fetching %s: %s", symbol, e)
            return None

    @staticmethod
    async def fetch_latest(symbol: str, lookback_days: int = 365) -> Optional[pd.DataFrame]:
        df = await DataIngestionService.fetch_yfinance(symbol, period="1y", interval="1d")
        if df is not None and lookback_days:
            df = df.tail(lookback_days)
        return df

    @staticmethod
    async def validate_symbol(symbol: str) -> bool:
        df = await DataIngestionService.fetch_yfinance(symbol, period="5d", interval="1d")
        return df is not None and not df.empty
