"""In-memory sliding-window rate limiting middleware with per-client tracking."""

import time
from collections import defaultdict
from typing import Dict, List
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.logging import logger


class SlidingWindowRateLimiter:
    """Tracks request timestamps per client within a 60-second sliding window."""

    def __init__(self, limit_per_minute: int = 120):
        self.limit_per_minute = limit_per_minute
        self.window_seconds = 60.0
        self._clients: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Return True if request is within limit, False otherwise."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Clean timestamps older than window
        timestamps = [t for t in self._clients[client_id] if t > cutoff]
        self._clients[client_id] = timestamps

        if len(timestamps) >= self.limit_per_minute:
            return False

        self._clients[client_id].append(now)
        return True

    def reset(self):
        """Clear all tracked request history."""
        self._clients.clear()


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter(limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)


class RateLimitMiddleware:
    """Enforces request rate limits per client IP or authorization token via pure ASGI."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not settings.ENABLE_RATE_LIMITER:
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Allow test bypass header if explicitly provided
        if request.headers.get("X-Bypass-Rate-Limit") == "true":
            await self.app(scope, receive, send)
            return

        # Allow swagger/docs/openapi and health check exemption
        exempt_paths = {"/docs", "/redoc", "/openapi.json", "/", "/api/v1/health"}
        if request.url.path in exempt_paths:
            await self.app(scope, receive, send)
            return

        # Identify client by Bearer token or client host IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            client_id = f"token:{auth_header[7:30]}"
        else:
            client_id = f"ip:{request.client.host if request.client else 'unknown'}"

        if not rate_limiter.is_allowed(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id} at {request.url.path}")
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please wait before submitting additional inquiries.",
                    "limit_per_minute": rate_limiter.limit_per_minute,
                },
                headers={"Retry-After": "60"}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
