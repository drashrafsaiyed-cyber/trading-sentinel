from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/trading_sentinel")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # AI Provider
    ai_provider: str = os.getenv("AI_PROVIDER", "nvidia")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_model: str = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")

    # Auth
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "168"))

    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Trading
    yfinance_cache_hours: int = int(os.getenv("YFINANCE_CACHE_HOURS", "1"))
    backtest_lookback_days: int = int(os.getenv("BACKTEST_LOOKBACK_DAYS", "365"))
    # Data source: "yfinance" (real, production) or "mock" (synthetic, offline dev)
    data_source: str = os.getenv("DATA_SOURCE", "yfinance")

    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    # Comma-separated list of allowed frontend origins (production CORS).
    # e.g. "https://trading-sentinel.vercel.app,https://app.tradingsentinel.ai"
    cors_origins: str = os.getenv("CORS_ORIGINS", "")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
