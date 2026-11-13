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
if settings.cors_origins:
    _origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
elif settings.debug:
    _origins = ["*"]
else:
    _origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # Allow any *.vercel.app preview deploy of this project in addition to the list
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "trading-sentinel-api"}


# Include routers
from app.api.auth import router as auth_router
from app.api.markets import router as markets_router
from app.api.watchlists import router as watchlists_router
from app.api.alerts import router as alerts_router

app.include_router(auth_router)
app.include_router(markets_router)
app.include_router(watchlists_router)
app.include_router(alerts_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.debug)
