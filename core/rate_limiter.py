from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import ErrorCode

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default rate limit
    storage_uri="memory://"  # Store rate limits in memory (you can change this to Redis for distributed systems)
)

def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": False,
            "error_code": ErrorCode.TOO_MANY_REQUESTS.value,
            "message": f"Unable to process your request at this time. Please try again later.",
            "data": None
        }
    )

def init_rate_limiter(app: FastAPI):
    """Initialize rate limiting for the FastAPI application."""
    # Enable rate limiting
    limiter.enabled = True
    
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    # Register the rate limit exceeded handler
    app.add_exception_handler(429, rate_limit_exceeded_handler)
    
    # Apply rate limiting to all routes by default
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Skip rate limiting for certain paths if needed
        if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            return await call_next(request)
            
        # Apply rate limiting to all other routes
        response = await call_next(request)
        return response