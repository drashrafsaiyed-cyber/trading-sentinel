"""Synthetic OHLCV generator for offline development / demos.

Deterministic per-symbol (seeded by the symbol) so a given ticker always shows
the same chart within a run. Produces a trending random walk with realistic
intrabar high/low/volume. Only used when DATA_SOURCE=mock.
"""
import hashlib
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# A few well-known tickers get a plausible starting price and bias.
_PROFILES = {
    "AAPL": (190.0, 0.0004), "MSFT": (420.0, 0.0005), "GOOGL": (165.0, 0.0003),
    "TSLA": (240.0, -0.0002), "NVDA": (880.0, 0.0010), "AMZN": (185.0, 0.0004),
    "BTC-USD": (67000.0, 0.0008), "ETH-USD": (3500.0, 0.0006), "SPY": (520.0, 0.0003),
    "EURUSD=X": (1.08, 0.0000),
}


def _seed(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)


def generate(symbol: str, days: int = 365) -> pd.DataFrame:
    """Generate a synthetic daily OHLCV DataFrame for a symbol."""
    rng = np.random.default_rng(_seed(symbol))
    start_price, drift = _PROFILES.get(symbol.upper(), (100.0 + _seed(symbol) % 400, 0.0003))

    vol = 0.018  # daily volatility
    returns = rng.normal(drift, vol, days)
    close = start_price * np.exp(np.cumsum(returns))

    # Build OHLC around the close path
    open_ = np.empty(days)
    open_[0] = start_price
    open_[1:] = close[:-1]
    intraday = np.abs(rng.normal(0, vol, days)) * close
    high = np.maximum(open_, close) + intraday * rng.uniform(0.2, 1.0, days)
    low = np.minimum(open_, close) - intraday * rng.uniform(0.2, 1.0, days)
    base_vol = 1_000_000 + (_seed(symbol) % 50) * 200_000
    volume = (base_vol * rng.uniform(0.5, 2.0, days)).astype("int64")

    end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    index = pd.date_range(end=end, periods=days, freq="D")

    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )
