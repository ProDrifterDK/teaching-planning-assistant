from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from api.services.rate_limit_service import rate_limit_service
from api.db.models import ServiceClient

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    Applies different limits based on authentication type.
    """
    
    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/"
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Determine rate limit key and limit
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            # API Key clients - check their specific limit
            # Note: This is simplified; in production, fetch from DB
            rate_key = f"apikey:{api_key[:20]}"
            limit = 100  # Default for API keys
        else:
            # JWT or unauthenticated - use IP-based limiting
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"ip:{client_ip}"
            limit = 30  # Lower limit for IP-based
        
        # Check rate limit
        is_allowed, info = await rate_limit_service.check_rate_limit(
            key=rate_key,
            limit=limit,
            window_seconds=60
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Limit: {info['limit']} per minute",
                    "retry_after": info["reset_at"]
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": info["reset_at"],
                    "Retry-After": "60"
                }
            )
        
        # Process request and add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = info["reset_at"]
        
        return response