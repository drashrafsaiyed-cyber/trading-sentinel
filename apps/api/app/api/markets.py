from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.db import get_db
from app.models import Market, Candle, Prediction
from app.core.data_ingestion import DataIngestionService, DataValidation
from app.core.indicators import TechnicalIndicators
from app.core.ml_sentiment import SentimentPredictor
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


class MarketCreate(BaseModel):
    symbol: str
    name: str
    type: str = "stock"
    exchange: str = None


class MarketResponse(BaseModel):
    id: str
    symbol: str
    name: str
    type: str
    exchange: str = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/add", response_model=MarketResponse)
async def add_market(market: MarketCreate, db: AsyncSession = Depends(get_db)):
    """Add a new market to track"""

    # Validate symbol exists
    if not await DataIngestionService.validate_symbol(market.symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol")

    # Check if already exists
    existing = await db.execute(
        select(Market).where(Market.symbol == market.symbol)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Market already exists")

    # Create market
    new_market = Market(
        symbol=market.symbol,
        name=market.name,
        type=market.type,
        exchange=market.exchange
    )
    db.add(new_market)
    await db.commit()
    await db.refresh(new_market)

    return new_market


@router.get("/list", response_model=List[MarketResponse])
async def list_markets(db: AsyncSession = Depends(get_db)):
    """List all tracked markets"""
    result = await db.execute(select(Market))
    markets = result.scalars().all()
    return markets


@router.get("/{symbol}/sentiment")
async def get_market_sentiment(symbol: str, db: AsyncSession = Depends(get_db)):
    """Get latest Bull/Bear sentiment for a symbol"""

    # Get market
    result = await db.execute(select(Market).where(Market.symbol == symbol))
    market = result.scalars().first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Get latest prediction
    pred_result = await db.execute(
        select(Prediction)
        .where(Prediction.market_id == market.id)
        .order_by(Prediction.timestamp.desc())
        .limit(1)
    )
    prediction = pred_result.scalars().first()

    if prediction:
        return {
            "symbol": symbol,
            "timestamp": prediction.timestamp,
            "sentiment": prediction.sentiment,
            "bull_score": prediction.bull_score,
            "bear_score": prediction.bear_score,
            "confidence": prediction.confidence,
            "reasoning": prediction.reasoning
        }

    # No prediction yet - compute one
    data = await DataIngestionService.fetch_latest(symbol)
    if data is None or data.empty:
        raise HTTPException(status_code=400, detail="Could not fetch data")

    predictor = SentimentPredictor()
    prediction_data = await predictor.predict(data, symbol)

    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow(),
        **prediction_data
    }


@router.post("/{symbol}/compute-sentiment")
async def compute_sentiment(symbol: str, db: AsyncSession = Depends(get_db)):
    """Compute and store sentiment prediction for a market"""

    # Get market
    result = await db.execute(select(Market).where(Market.symbol == symbol))
    market = result.scalars().first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Fetch latest data
    data = await DataIngestionService.fetch_latest(symbol)
    if data is None or data.empty:
        raise HTTPException(status_code=400, detail="Could not fetch data for symbol")

    # Compute sentiment
    predictor = SentimentPredictor()
    prediction_data = await predictor.predict(data, symbol)

    # Store in DB
    new_prediction = Prediction(
        market_id=market.id,
        timestamp=datetime.utcnow(),
        sentiment=prediction_data['sentiment'],
        confidence=prediction_data['confidence'],
        bull_score=prediction_data['bull_score'],
        bear_score=prediction_data['bear_score'],
        reasoning=prediction_data['reasoning'],
        features=prediction_data['features']
    )
    db.add(new_prediction)
    await db.commit()

    return prediction_data


@router.get("/{symbol}/candles")
async def get_candles(symbol: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get recent candles for a symbol"""

    # Get market
    result = await db.execute(select(Market).where(Market.symbol == symbol))
    market = result.scalars().first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    # Fetch from yfinance if not in DB
    data = await DataIngestionService.fetch_latest(symbol, lookback_days=365)
    if data is None or data.empty:
        raise HTTPException(status_code=400, detail="Could not fetch data")

    # Convert to JSON-serializable format
    candles = []
    for timestamp, row in data.iterrows():
        candles.append({
            "timestamp": timestamp.isoformat(),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "volume": int(row['volume'])
        })

    return {
        "symbol": symbol,
        "candles": candles[-limit:]
    }
