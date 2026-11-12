"""Technical indicators for trading analysis.

Pure pandas/numpy implementations — no TA-Lib C dependency, so this installs
and deploys cleanly everywhere (Render, Vercel functions, bare venv).
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple


class TechnicalIndicators:
    """Compute technical indicators from OHLCV data."""

    @staticmethod
    def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index (0-100), Wilder's smoothing."""
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD line, signal line, histogram."""
        ema_fast = closes.ewm(span=fast, adjust=False).mean()
        ema_slow = closes.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(closes: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands (upper, middle, lower)."""
        middle = closes.rolling(window=period).mean()
        std = closes.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower

    @staticmethod
    def sma(closes: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return closes.rolling(window=period).mean()

    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        """Compute all indicators for a DataFrame with OHLCV columns."""
        df = df.copy()
        closes = df['close']

        df['rsi_14'] = TechnicalIndicators.rsi(closes, 14)
        df['macd'], df['macd_signal'], df['macd_hist'] = TechnicalIndicators.macd(closes)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = TechnicalIndicators.bollinger_bands(closes)
        df['sma_20'] = TechnicalIndicators.sma(closes, 20)
        df['sma_50'] = TechnicalIndicators.sma(closes, 50)
        df['sma_200'] = TechnicalIndicators.sma(closes, 200)

        return df

    @staticmethod
    def _f(value, default=0.0) -> float:
        """Safe float coercion — NaN/None become the default."""
        try:
            v = float(value)
            return default if np.isnan(v) else v
        except (TypeError, ValueError):
            return default

    @staticmethod
    def extract_features(df: pd.DataFrame) -> Dict[str, float]:
        """Extract features for ML sentiment prediction.

        Degrades gracefully on short histories: SMA-200 is skipped if we have
        fewer than 200 candles rather than returning nothing.
        """
        features: Dict[str, float] = {}
        if len(df) < 20:
            return features

        _f = TechnicalIndicators._f
        latest = df.iloc[-1]
        n = len(df)

        features['price_above_sma_20'] = float(_f(latest['close']) > _f(latest['sma_20']))
        if n >= 50:
            features['price_above_sma_50'] = float(_f(latest['close']) > _f(latest['sma_50']))
        if n >= 200:
            features['price_above_sma_200'] = float(_f(latest['close']) > _f(latest['sma_200']))

        features['rsi_14'] = _f(latest['rsi_14'], 50.0)
        features['rsi_overbought'] = float(features['rsi_14'] > 70)
        features['rsi_oversold'] = float(features['rsi_14'] < 30)

        features['macd_positive'] = float(_f(latest['macd']) > _f(latest['macd_signal']))
        features['macd_histogram'] = _f(latest['macd_hist'])

        bb_upper, bb_lower, close = _f(latest['bb_upper']), _f(latest['bb_lower']), _f(latest['close'])
        bb_range = bb_upper - bb_lower
        bb_position = (close - bb_lower) / bb_range if bb_range > 0 else 0.5
        features['bb_position'] = float(np.clip(bb_position, 0, 1))

        if n >= 6:
            sma_now = _f(df['sma_20'].iloc[-1])
            sma_prev = _f(df['sma_20'].iloc[-6])
            features['sma_20_angle'] = (sma_now - sma_prev) / sma_prev if sma_prev else 0.0

            vol_now = _f(df['volume'].iloc[-1])
            vol_avg = _f(df['volume'].iloc[-6:-1].mean())
            features['volume_trend'] = (vol_now - vol_avg) / vol_avg if vol_avg else 0.0

        return features


def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    """Identify nearest support and resistance levels."""
    w = min(window, len(df))
    support = TechnicalIndicators._f(df['low'].tail(w).min())
    resistance = TechnicalIndicators._f(df['high'].tail(w).max())
    return float(support), float(resistance)
