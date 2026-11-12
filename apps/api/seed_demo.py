#!/usr/bin/env python
"""Seed a demo user with a watchlist and fresh sentiment predictions.

Run (with DATA_SOURCE=mock for offline, or yfinance in prod):
    .venv/bin/python seed_demo.py
"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from app.core.db import AsyncSessionLocal, init_db
from app.core.security import hash_password
from app.core.data_ingestion import DataIngestionService
from app.core.ml_sentiment import SentimentPredictor
from app.ai.factory import get_ai_provider
from app.models import User, Market, Watchlist, Prediction

DEMO_EMAIL = "demo@tradingsentinel.ai"
DEMO_PASSWORD = "Demo12345"
SYMBOLS = [
    ("AAPL", "Apple Inc.", "stock"),
    ("MSFT", "Microsoft", "stock"),
    ("NVDA", "Nvidia", "stock"),
    ("BTC-USD", "Bitcoin", "crypto"),
    ("TSLA", "Tesla", "stock"),
]


async def main():
    await init_db()
    predictor = SentimentPredictor(ai_provider=get_ai_provider())

    async with AsyncSessionLocal() as db:
        # Demo user
        res = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = res.scalars().first()
        if user is None:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
                        name="Demo Trader", subscription_tier="pro")
            db.add(user)
            await db.flush()
            print(f"Created demo user {DEMO_EMAIL} / {DEMO_PASSWORD}")

        for symbol, name, mtype in SYMBOLS:
            res = await db.execute(select(Market).where(Market.symbol == symbol))
            market = res.scalars().first()
            if market is None:
                market = Market(symbol=symbol, name=name, type=mtype)
                db.add(market)
                await db.flush()

            dup = await db.execute(
                select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.market_id == market.id)
            )
            if dup.scalars().first() is None:
                db.add(Watchlist(user_id=user.id, market_id=market.id, alert_on_flip=True))

            data = await DataIngestionService.fetch_latest(symbol)
            if data is None or data.empty:
                print(f"  ! no data for {symbol} (network blocked?) — skipping sentiment")
                continue
            result = await predictor.predict(data, symbol)
            db.add(Prediction(
                market_id=market.id, timestamp=datetime.utcnow(),
                sentiment=result["sentiment"], confidence=result["confidence"],
                bull_score=result["bull_score"], bear_score=result["bear_score"],
                reasoning=result["reasoning"], features=result.get("features"),
            ))
            print(f"  {symbol}: {result['sentiment'].upper()} "
                  f"bull {result['bull_score']:.0f}% / bear {result['bear_score']:.0f}%")

        await db.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
