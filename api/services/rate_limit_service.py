import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Tuple
import asyncio

class RateLimitService:
    """
    Rate limiting service using in-memory storage.
    In production, replace with Redis for distributed rate limiting.
    """
    
    def __init__(self):
        # In-memory storage: {key: [(timestamp, count)]}
        self._requests: dict = defaultdict(list)
        self._lock = asyncio.Lock()
        
        # Default limits
        self.default_requests_per_minute = 60
        self.default_requests_per_hour = 1000
    
    def _clean_old_entries(self, key: str, window_seconds: int) -> None:
        """Remove entries older than the window"""
        cutoff = time.time() - window_seconds
        self._requests[key] = [
            entry for entry in self._requests[key]
            if entry[0] > cutoff
        ]
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int = None,
        window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit.
        
        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: remaining, limit, reset_at
        """
        async with self._lock:
            limit = limit or self.default_requests_per_minute
            
            # Clean old entries
            self._clean_old_entries(key, window_seconds)
            
            # Count current requests
            current_count = len(self._requests[key])
            
            # Calculate reset time
            if self._requests[key]:
                oldest = min(entry[0] for entry in self._requests[key])
                reset_at = datetime.fromtimestamp(oldest + window_seconds)
            else:
                reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)
            
            info = {
                "limit": limit,
                "remaining": max(0, limit - current_count - 1),
                "reset_at": reset_at.isoformat(),
                "window_seconds": window_seconds
            }
            
            if current_count >= limit:
                return False, info
            
            # Add new request
            self._requests[key].append((time.time(), 1))
            info["remaining"] = max(0, limit - current_count - 1)
            
            return True, info
    
    async def get_usage(self, key: str, window_seconds: int = 60) -> dict:
        """Get current usage for a key"""
        async with self._lock:
            self._clean_old_entries(key, window_seconds)
            current_count = len(self._requests[key])
            
            return {
                "key": key,
                "current_count": current_count,
                "window_seconds": window_seconds
            }
    
    async def reset_key(self, key: str) -> None:
        """Reset rate limit for a specific key"""
        async with self._lock:
            if key in self._requests:
                del self._requests[key]

# Singleton instance
rate_limit_service = RateLimitService()