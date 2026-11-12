"""Watchlist endpoints — per-user tracked symbols with price targets & alerts."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User, Watchlist, Market, Prediction, AuditLog
from app.core.data_ingestion import DataIngestionService
from app.core.ml_sentiment import SentimentPredictor
from app.ai.factory import get_ai_provider

router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])

FREE_TIER_LIMIT = 5


class WatchlistCreate(BaseModel):
    symbol: str
    name: Optional[str] = None
    type: str = "stock"
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    alert_on_flip: bool = True


class WatchlistUpdate(BaseModel):
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    alert_on_flip: Optional[bool] = None


@router.post("", status_code=201)
async def add_to_watchlist(
    req: WatchlistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a symbol to the user's watchlist (creating the Market if needed)."""
    # Free-tier limit
    count_res = await db.execute(select(Watchlist).where(Watchlist.user_id == user.id))
    if user.subscription_tier == "free" and len(count_res.scalars().all()) >= FREE_TIER_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=f"Free tier limited to {FREE_TIER_LIMIT} watchlist items. Upgrade to Pro.",
        )

    symbol = req.symbol.upper()

    # Resolve or create the market
    mkt_res = await db.execute(select(Market).where(Market.symbol == symbol))
    market = mkt_res.scalars().first()
    if market is None:
        if not await DataIngestionService.validate_symbol(symbol):
            raise HTTPException(status_code=400, detail=f"Symbol '{symbol}' not found")
        market = Market(symbol=symbol, name=req.name or symbol, type=req.type)
        db.add(market)
        await db.flush()

    # Prevent duplicates
    dup = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id, Watchlist.market_id == market.id)
    )
    if dup.scalars().first():
        raise HTTPException(status_code=409, detail="Already in watchlist")

    item = Watchlist(
        user_id=user.id,
        market_id=market.id,
        entry_price=req.entry_price,
        target_price=req.target_price,
        stop_loss=req.stop_loss,
        alert_on_flip=req.alert_on_flip,
    )
    db.add(item)
    db.add(AuditLog(user_id=user.id, action="watchlist_add", entity_type="watchlist", entity_id=market.id))
    await db.commit()
    await db.refresh(item)

    return {
        "id": str(item.id),
        "symbol": symbol,
        "name": market.name,
        "entry_price": item.entry_price,
        "target_price": item.target_price,
        "stop_loss": item.stop_loss,
        "alert_on_flip": item.alert_on_flip,
    }


@router.get("")
async def list_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's watchlist with the latest stored sentiment for each."""
    res = await db.execute(
        select(Watchlist, Market)
        .join(Market, Watchlist.market_id == Market.id)
        .where(Watchlist.user_id == user.id)
    )
    rows = res.all()

    items = []
    for wl, market in rows:
        pred_res = await db.execute(
            select(Prediction)
            .where(Prediction.market_id == market.id)
            .order_by(Prediction.timestamp.desc())
            .limit(1)
        )
        pred = pred_res.scalars().first()
        items.append({
            "id": str(wl.id),
            "symbol": market.symbol,
            "name": market.name,
            "type": market.type,
            "entry_price": wl.entry_price,
            "target_price": wl.target_price,
            "stop_loss": wl.stop_loss,
            "alert_on_flip": wl.alert_on_flip,
            "sentiment": pred.sentiment if pred else None,
            "bull_score": pred.bull_score if pred else None,
            "bear_score": pred.bear_score if pred else None,
            "confidence": pred.confidence if pred else None,
            "last_updated": pred.timestamp.isoformat() if pred else None,
        })
    return {"count": len(items), "items": items}


@router.patch("/{watchlist_id}")
async def update_watchlist(
    watchlist_id: str,
    req: WatchlistUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update price targets or alert settings for a watchlist item."""
    res = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    item = res.scalars().first()
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    for field in ("entry_price", "target_price", "stop_loss", "alert_on_flip"):
        value = getattr(req, field)
        if value is not None:
            setattr(item, field, value)

    await db.commit()
    return {"status": "ok", "id": watchlist_id}


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an item from the watchlist."""
    res = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    item = res.scalars().first()
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    await db.delete(item)
    db.add(AuditLog(user_id=user.id, action="watchlist_remove", entity_type="watchlist"))
    await db.commit()
    return {"status": "ok", "message": "Removed from watchlist"}


@router.post("/{watchlist_id}/refresh")
async def refresh_sentiment(
    watchlist_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recompute sentiment for one watchlist item on demand."""
    res = await db.execute(
        select(Watchlist, Market)
        .join(Market, Watchlist.market_id == Market.id)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
    )
    row = res.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    wl, market = row

    data = await DataIngestionService.fetch_latest(market.symbol)
    if data is None or data.empty:
        raise HTTPException(status_code=400, detail="Could not fetch market data")

    predictor = SentimentPredictor(ai_provider=get_ai_provider())
    result = await predictor.predict(data, market.symbol)

    db.add(Prediction(
        market_id=market.id,
        timestamp=datetime.utcnow(),
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        bull_score=result["bull_score"],
        bear_score=result["bear_score"],
        reasoning=result["reasoning"],
        features=result.get("features"),
    ))
    wl.last_sentiment = result["sentiment"]
    await db.commit()

    return {"symbol": market.symbol, **result}
