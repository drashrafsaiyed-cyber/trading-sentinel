"""Alert endpoints and the sentiment-flip / price-target scan engine."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User, Alert, Watchlist, Market, Prediction
from app.core.data_ingestion import DataIngestionService
from app.core.ml_sentiment import SentimentPredictor
from app.core.telegram import telegram
from app.ai.factory import get_ai_provider

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's alert history (most recent first)."""
    res = await db.execute(
        select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()).limit(100)
    )
    alerts = res.scalars().all()
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
                "sent": a.sent,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    }


async def scan_user_watchlist(user: User, db: AsyncSession) -> list[dict]:
    """Recompute sentiment for a user's watchlist and fire alerts on flips /
    price-target / stop-loss hits. Returns the list of alerts fired."""
    res = await db.execute(
        select(Watchlist, Market)
        .join(Market, Watchlist.market_id == Market.id)
        .where(Watchlist.user_id == user.id)
    )
    rows = res.all()
    predictor = SentimentPredictor(ai_provider=get_ai_provider())
    fired: list[dict] = []

    for wl, market in rows:
        data = await DataIngestionService.fetch_latest(market.symbol)
        if data is None or data.empty:
            continue

        result = await predictor.predict(data, market.symbol)
        new_sentiment = result["sentiment"]
        latest_close = float(data["close"].iloc[-1])

        # Persist the fresh prediction
        db.add(Prediction(
            market_id=market.id,
            timestamp=datetime.utcnow(),
            sentiment=new_sentiment,
            confidence=result["confidence"],
            bull_score=result["bull_score"],
            bear_score=result["bear_score"],
            reasoning=result["reasoning"],
            features=result.get("features"),
        ))

        alerts_for_item = []

        # Sentiment flip
        if wl.alert_on_flip and wl.last_sentiment and wl.last_sentiment != new_sentiment:
            alerts_for_item.append((
                "sentiment_flip",
                f"🔄 <b>{market.symbol}</b> flipped {wl.last_sentiment.upper()} → "
                f"<b>{new_sentiment.upper()}</b> ({result['confidence']:.0f}% conf)\n{result['reasoning']}",
            ))

        # Price target
        if wl.target_price and latest_close >= wl.target_price:
            alerts_for_item.append((
                "price_target",
                f"🎯 <b>{market.symbol}</b> hit target ${wl.target_price:.2f} "
                f"(now ${latest_close:.2f})",
            ))

        # Stop loss
        if wl.stop_loss and latest_close <= wl.stop_loss:
            alerts_for_item.append((
                "stop_loss",
                f"🛑 <b>{market.symbol}</b> hit stop-loss ${wl.stop_loss:.2f} "
                f"(now ${latest_close:.2f})",
            ))

        for alert_type, message in alerts_for_item:
            alert = Alert(
                user_id=user.id,
                watchlist_id=wl.id,
                alert_type=alert_type,
                triggered_at=datetime.utcnow(),
                sent=False,
            )
            db.add(alert)

            # Deliver via Telegram if linked
            if user.telegram_user_id:
                ok = await telegram.send_message(user.telegram_user_id, message)
                alert.sent = ok

            fired.append({"symbol": market.symbol, "type": alert_type, "message": message})

        wl.last_sentiment = new_sentiment

    await db.commit()
    return fired


@router.post("/scan")
async def scan_now(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an alert scan of the user's watchlist."""
    fired = await scan_user_watchlist(user, db)
    return {"status": "ok", "alerts_fired": len(fired), "alerts": fired}


@router.post("/test-telegram")
async def test_telegram(
    user: User = Depends(get_current_user),
):
    """Send a test message to the user's linked Telegram."""
    if not user.telegram_user_id:
        raise HTTPException(status_code=400, detail="No Telegram linked. Use /auth/link-telegram first.")
    if not telegram.enabled:
        raise HTTPException(status_code=503, detail="Telegram bot token not configured on server.")

    ok = await telegram.send_message(
        user.telegram_user_id,
        "✅ <b>Trading Sentinel</b> alerts are connected! You'll get notified on sentiment flips.",
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to send. Check chat id / that you started the bot.")
    return {"status": "ok", "message": "Test alert sent"}
