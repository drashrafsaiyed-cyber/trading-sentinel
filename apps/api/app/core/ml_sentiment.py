"""ML-based sentiment prediction for trading"""
import json
import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from app.core.indicators import TechnicalIndicators, calculate_support_resistance

logger = logging.getLogger(__name__)


class SentimentPredictor:
    """Predict Bull/Bear sentiment using technical analysis + AI"""

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    async def predict(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Predict Bull/Bear sentiment for a symbol

        Returns:
            {
                'sentiment': 'bull' | 'bear' | 'neutral',
                'bull_score': 0-100,
                'bear_score': 0-100,
                'confidence': 0-100,
                'reasoning': str,
                'features': Dict[str, float]
            }
        """
        if len(df) < 20:
            return {'error': 'Insufficient data'}

        # Compute indicators
        df = TechnicalIndicators.compute_all(df)
        features = TechnicalIndicators.extract_features(df)
        support, resistance = calculate_support_resistance(df)

        # Rule-based scoring (hardcoded logic)
        bull_score, bear_score = self._rule_based_score(features, df, support, resistance)

        # AI refinement (if provider available)
        if self.ai_provider:
            ai_boost = await self._ai_refinement(symbol, df, features, bull_score, bear_score)
            bull_score = bull_score * 0.7 + ai_boost.get('bull_score', bull_score) * 0.3
            bear_score = bear_score * 0.7 + ai_boost.get('bear_score', bear_score) * 0.3

        # Normalize to 100%
        total = bull_score + bear_score
        if total > 0:
            bull_pct = (bull_score / total) * 100
            bear_pct = (bear_score / total) * 100
        else:
            bull_pct = bear_pct = 50

        # Determine sentiment
        if bull_pct > 60:
            sentiment = 'bull'
        elif bear_pct > 60:
            sentiment = 'bear'
        else:
            sentiment = 'neutral'

        confidence = max(bull_pct, bear_pct)

        return {
            'sentiment': sentiment,
            'bull_score': round(bull_pct, 2),
            'bear_score': round(bear_pct, 2),
            'confidence': round(confidence, 2),
            'reasoning': self._generate_reasoning(features, sentiment, bull_pct, bear_pct),
            'features': features,
            'support': round(float(support), 2),
            'resistance': round(float(resistance), 2)
        }

    def _rule_based_score(self, features: Dict, df: pd.DataFrame, support: float, resistance: float) -> Tuple[float, float]:
        """Calculate bull/bear score using technical rules"""
        bull_score = 0.0
        bear_score = 0.0

        # Price position (strong indicator)
        if features.get('price_above_sma_200'):
            bull_score += 25
        else:
            bear_score += 25

        if features.get('price_above_sma_50'):
            bull_score += 20
        else:
            bear_score += 20

        # RSI (overbought/oversold)
        rsi = features.get('rsi_14', 50)
        if rsi > 70:  # Overbought
            bear_score += 15
        elif rsi < 30:  # Oversold
            bull_score += 15
        elif 40 <= rsi <= 60:
            bull_score += 5

        # MACD
        if features.get('macd_positive'):
            bull_score += 20
        else:
            bear_score += 20

        # Bollinger Bands
        bb_pos = features.get('bb_position', 0.5)
        if bb_pos > 0.8:  # Near upper band (overbought)
            bear_score += 10
        elif bb_pos < 0.2:  # Near lower band (oversold)
            bull_score += 10

        # Volume trend
        vol_trend = features.get('volume_trend', 0)
        if vol_trend > 0.2:  # Increasing volume
            if features.get('macd_positive'):
                bull_score += 10
            else:
                bear_score += 10

        # SMA trend
        sma_angle = features.get('sma_20_angle', 0)
        if sma_angle > 0.01:
            bull_score += 10
        elif sma_angle < -0.01:
            bear_score += 10

        return bull_score, bear_score

    async def _ai_refinement(self, symbol: str, df: pd.DataFrame, features: Dict, bull_score: float, bear_score: float) -> Dict:
        """Use AI to refine the prediction"""
        if not self.ai_provider:
            return {'bull_score': bull_score, 'bear_score': bear_score}

        try:
            latest = df.iloc[-1]

            prompt = f"""Analyze this trading chart for {symbol} and predict if the next candle will be BULLISH or BEARISH.

Current Price: ${latest['close']:.2f}
20-day MA: ${latest['sma_20']:.2f}
50-day MA: ${latest['sma_50']:.2f}
200-day MA: ${latest['sma_200']:.2f}

Technical Indicators:
- RSI (14): {latest['rsi_14']:.1f}
- MACD: {latest['macd']:.4f} (Signal: {latest['macd_signal']:.4f})
- Bollinger Bands: Upper ${latest['bb_upper']:.2f}, Lower ${latest['bb_lower']:.2f}
- 5-day Volume Trend: {features.get('volume_trend', 0)*100:.1f}%

Price is above SMA20: {features.get('price_above_sma_20', False)}
Price is above SMA50: {features.get('price_above_sma_50', False)}
Price is above SMA200: {features.get('price_above_sma_200', False)}

Based on this technical analysis, respond with ONLY valid JSON (no markdown):
{{"bull_confidence": <0-100>, "bear_confidence": <0-100>, "reason": "one sentence"}}"""

            result = await self.ai_provider.complete(prompt)
            response_text = result.content if hasattr(result, 'content') else str(result)

            # Parse JSON from AI response
            try:
                ai_result = json.loads(response_text)
                return {
                    'bull_score': ai_result.get('bull_confidence', bull_score),
                    'bear_score': ai_result.get('bear_confidence', bear_score),
                    'ai_reasoning': ai_result.get('reason', '')
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response: {response_text}")
                return {'bull_score': bull_score, 'bear_score': bear_score}

        except Exception as e:
            logger.error(f"AI refinement failed: {e}")
            return {'bull_score': bull_score, 'bear_score': bear_score}

    def _generate_reasoning(self, features: Dict, sentiment: str, bull_pct: float, bear_pct: float) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        if features.get('price_above_sma_200'):
            reasons.append(f"Price above 200-MA (bullish trend)")
        else:
            reasons.append(f"Price below 200-MA (bearish trend)")

        rsi = features.get('rsi_14', 50)
        if rsi > 70:
            reasons.append(f"RSI {rsi:.0f} (overbought)")
        elif rsi < 30:
            reasons.append(f"RSI {rsi:.0f} (oversold)")

        if features.get('macd_positive'):
            reasons.append("MACD positive crossover")
        else:
            reasons.append("MACD negative")

        reason_str = " · ".join(reasons)
        return f"{sentiment.upper()} {bull_pct:.0f}% - {reason_str}"
