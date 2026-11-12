from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.db import init_db, close_db
from app.config import settings
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Trading Sentinel API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="Trading Sentinel API",
    description="AI-powered trading sentiment analysis",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://trading-sentinel.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "trading-sentinel-api"}


# Include routers
from app.api.markets import router as markets_router
app.include_router(markets_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)
