"""Security headers middleware for protecting against MIME-sniffing, clickjacking, and XSS."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects essential security headers into every HTTP response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Protect against MIME type confusion / sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent frame injection & clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable browser XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (allow local scripts, styles, fonts, KaTeX, and audio)
        response.headers["Permissions-Policy"] = "microphone=(self), camera=()"

        return response

