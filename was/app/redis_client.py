"""Async Redis client singleton."""

from __future__ import annotations

import structlog
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config import get_settings

logger = structlog.get_logger(__name__)

_pool: ConnectionPool | None = None
_client: Redis | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis(connection_pool=get_redis_pool())
    return _client


async def close_redis() -> None:
    """Close Redis connection pool on shutdown."""
    global _pool, _client
    if _pool is not None:
        logger.info("redis_pool_closing")
        await _pool.aclose()
        _pool = None
        _client = None
        logger.info("redis_pool_closed")
