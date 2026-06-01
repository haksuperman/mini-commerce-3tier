"""Rate limiting utilities.

Redis-backed per-IP rate limiter for the login route, with an in-process
counter fallback if Redis is unavailable. Called manually inside the login
handler (not registered as middleware).
"""

from __future__ import annotations

import time

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)

# In-memory fallback (used if Redis is unavailable)
_in_memory_counts: dict[str, tuple[int, float]] = {}

LOGIN_LIMIT = 5  # requests
LOGIN_WINDOW = 60  # seconds


async def check_login_rate_limit(request: Request) -> JSONResponse | None:
    """Check if the requester has exceeded the login rate limit (5/minute).

    Returns a 429 JSONResponse if rate limited, otherwise None.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:login:{client_ip}"

    try:
        from app.redis_client import get_redis

        redis = get_redis()
        count_raw = await redis.get(key)
        count = int(count_raw) if count_raw else 0

        if count >= LOGIN_LIMIT:
            logger.warning("login_rate_limited", ip=client_ip, count=count)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many login attempts. Try again in {LOGIN_WINDOW} seconds."},
                headers={"Retry-After": str(LOGIN_WINDOW)},
            )

        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_WINDOW)
        await pipe.execute()

    except Exception:
        # Fallback to in-memory if Redis unavailable
        now = time.monotonic()
        existing = _in_memory_counts.get(client_ip)

        if existing:
            count_mem, window_start = existing
            if now - window_start < LOGIN_WINDOW:
                if count_mem >= LOGIN_LIMIT:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many login attempts. Try again later."},
                    )
                _in_memory_counts[client_ip] = (count_mem + 1, window_start)
            else:
                _in_memory_counts[client_ip] = (1, now)
        else:
            _in_memory_counts[client_ip] = (1, now)

    return None
