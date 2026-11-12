from sqlalchemy import Column, String, Float, Integer, BigInteger, DateTime, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.db import Base


class Market(Base):
    __tablename__ = "markets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # stock, crypto, forex
    exchange = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    candles = relationship("Candle", back_populates="market", cascade="all, delete-orphan")
    indicators = relationship("Indicator", back_populates="market", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="market", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="market", cascade="all, delete-orphan")


class Candle(Base):
    __tablename__ = "candles"

    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False, primary_key=True)
    timestamp = Column(DateTime, nullable=False, primary_key=True, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    market = relationship("Market", back_populates="candles")


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    bb_upper = Column(Float)
    bb_lower = Column(Float)
    bb_middle = Column(Float)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    volume_sma = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

    market = relationship("Market", back_populates="indicators")

    __table_args__ = (UniqueConstraint('market_id', 'timestamp', name='uq_indicator_market_timestamp'),)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    sentiment = Column(String(20), nullable=False)  # bull, bear, neutral
    confidence = Column(Float, nullable=False)  # 0-100
    bull_score = Column(Float)
    bear_score = Column(Float)
    reasoning = Column(String(500))
    features = Column(JSON)
    model_version = Column(String(50))
    accuracy_on_backtest = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    market = relationship("Market", back_populates="predictions")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200))
    telegram_user_id = Column(String(50))
    subscription_tier = Column(String(20), default="free")  # free, pro, api
    subscription_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    backtest_results = relationship("BacktestResult", back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    entry_price = Column(Float)
    target_price = Column(Float)
    stop_loss = Column(Float)
    alert_on_flip = Column(Boolean, default=True)
    last_sentiment = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watchlists")
    market = relationship("Market", back_populates="watchlists")

    __table_args__ = (UniqueConstraint('user_id', 'market_id', name='uq_watchlist_user_market'),)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlists.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # sentiment_flip, price_target, stop_loss
    triggered_at = Column(DateTime)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_return = Column(Float)  # %
    win_rate = Column(Float)
    num_trades = Column(Integer)
    max_drawdown = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="backtest_results")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
