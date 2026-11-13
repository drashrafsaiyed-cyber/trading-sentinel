"""Async SQLAlchemy engine, hardened for Supabase + Render.

Handles the three things that break a naive asyncpg connection to Supabase:
  1. SSL is required for any non-local host.
  2. The Supabase *transaction* pooler (port 6543, pgbouncer) does not support
     prepared statements, so asyncpg's statement cache must be disabled.
  3. libpq-style query params (sslmode, pgbouncer, channel_binding) that asyncpg
     does not understand must be stripped from the URL and translated.
"""
import ssl
import logging
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _build_engine_args(raw_url: str):
    """Return (sqlalchemy_url, connect_args) ready for asyncpg."""
    parts = urlsplit(raw_url)
    query = dict(parse_qsl(parts.query))

    host = (parts.hostname or "").lower()
    is_local = host in ("localhost", "127.0.0.1", "::1", "")

    # libpq params asyncpg can't take as query args
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    is_pgbouncer = query.pop("pgbouncer", "").lower() == "true" or ":6543" in raw_url

    # Rebuild a clean URL (asyncpg driver) without the stripped params
    clean = parts._replace(query="&".join(f"{k}={v}" for k, v in query.items()))
    scheme = "postgresql+asyncpg"
    sqlalchemy_url = urlunsplit((scheme, parts.netloc, parts.path, clean.query, ""))

    connect_args: dict = {"timeout": 15, "command_timeout": 30}

    # SSL: required on any remote host (Supabase). Disabled for local dev.
    want_ssl = not is_local and sslmode != "disable"
    if want_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # Supabase/Render terminate TLS; cert chain varies
        connect_args["ssl"] = ctx

    # pgbouncer transaction mode: no prepared statements
    if is_pgbouncer:
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0
        logger.info("pgbouncer detected — prepared statement cache disabled")

    return sqlalchemy_url, connect_args, is_pgbouncer


_url, _connect_args, _is_pgbouncer = _build_engine_args(settings.database_url)

# NullPool-like behavior is safest behind a transaction pooler; otherwise a
# small persistent pool is fine.
_engine_kwargs = dict(
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
if _is_pgbouncer:
    from sqlalchemy.pool import NullPool
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs.update(pool_size=10, max_overflow=20, pool_recycle=1800)

engine = create_async_engine(_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db():
    """FastAPI dependency: yield a DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create tables if they don't exist (idempotent)."""
    # Import models so metadata is populated before create_all
    from app import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db():
    await engine.dispose()
    logger.info("Database connection closed")
