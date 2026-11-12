"""Technical indicators for trading analysis"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import talib


class TechnicalIndicators:
    """Compute technical indicators from OHLCV data"""

    @staticmethod
    def rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index (0-100)"""
        return talib.RSI(closes, timeperiod=period)

    @staticmethod
    def macd(closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD (Moving Average Convergence Divergence)"""
        macd, signal_line, histogram = talib.MACD(closes, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        return macd, signal_line, histogram

    @staticmethod
    def bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands (upper, middle, lower)"""
        upper, middle, lower = talib.BBANDS(closes, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
        return upper, middle, lower

    @staticmethod
    def sma(closes: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        return talib.SMA(closes, timeperiod=period)

    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        """Compute all indicators for a DataFrame with OHLCV columns"""
        closes = df['close'].values

        df['rsi_14'] = TechnicalIndicators.rsi(closes, 14)
        df['macd'], df['macd_signal'], df['macd_hist'] = TechnicalIndicators.macd(closes)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = TechnicalIndicators.bollinger_bands(closes)
        df['sma_20'] = TechnicalIndicators.sma(closes, 20)
        df['sma_50'] = TechnicalIndicators.sma(closes, 50)
        df['sma_200'] = TechnicalIndicators.sma(closes, 200)

        return df

    @staticmethod
    def extract_features(df: pd.DataFrame) -> Dict[str, float]:
        """Extract features for ML sentiment prediction"""
        features = {}

        if len(df) < 200:
            return features

        latest = df.iloc[-1]

        # Price features
        features['price_above_sma_20'] = float(latest['close'] > latest['sma_20'])
        features['price_above_sma_50'] = float(latest['close'] > latest['sma_50'])
        features['price_above_sma_200'] = float(latest['close'] > latest['sma_200'])

        # RSI
        features['rsi_14'] = float(latest['rsi_14'])
        features['rsi_overbought'] = float(latest['rsi_14'] > 70)
        features['rsi_oversold'] = float(latest['rsi_14'] < 30)

        # MACD
        features['macd_positive'] = float(latest['macd'] > latest['macd_signal'])
        features['macd_histogram'] = float(latest['macd_hist'])

        # Bollinger Bands
        bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        features['bb_position'] = float(np.clip(bb_position, 0, 1))  # 0 = lower, 1 = upper

        # Trend strength (SMA angles)
        features['sma_20_angle'] = float((df['sma_20'].iloc[-1] - df['sma_20'].iloc[-5]) / df['sma_20'].iloc[-5])

        # Volume trend
        features['volume_trend'] = float((df['volume'].iloc[-1] - df['volume'].iloc[-5].mean()) / df['volume'].iloc[-5].mean())

        return features


def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    """Identify support and resistance levels"""
    highs = df['high'].rolling(window=window).max()
    lows = df['low'].rolling(window=window).min()

    resistance = highs.iloc[-1]
    support = lows.iloc[-1]

    return float(support), float(resistance)
