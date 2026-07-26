"""Caching layer with Redis and in-memory fallback."""

import os
import json
import time
from typing import Any, Optional, Dict
from functools import wraps


class CacheBackend:
    """Base cache backend interface."""
    
    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        raise NotImplementedError
    
    def delete(self, key: str) -> None:
        raise NotImplementedError
    
    def clear(self) -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value with TTL in seconds."""
        if ttl > 0:
            expires_at = time.time() + ttl
        elif ttl == 0:
            # TTL=0 means expire immediately
            expires_at = time.time()
        else:
            # Negative TTL means no expiry
            expires_at = None
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
        }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            import redis
            self._client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self._client.ping()  # Test connection
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Redis: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        value = self._client.get(key)
        if value is None:
            return None
        return json.loads(value)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in Redis with TTL."""
        serialized = json.dumps(value)
        if ttl > 0:
            self._client.setex(key, ttl, serialized)
        else:
            self._client.set(key, serialized)
    
    def delete(self, key: str) -> None:
        """Delete key from Redis."""
        self._client.delete(key)
    
    def clear(self) -> None:
        """Clear all keys (use with caution)."""
        self._client.flushdb()


class CacheManager:
    """Cache manager with automatic backend selection."""
    
    def __init__(self, backend: Optional[str] = None):
        """Initialize cache manager.
        
        Args:
            backend: Cache backend ('redis', 'memory', or None for auto-detect)
        """
        if backend == "redis":
            self._backend = self._create_redis_backend()
        elif backend == "memory":
            self._backend = MemoryCache()
        else:
            # Auto-detect: try Redis, fallback to memory
            try:
                self._backend = self._create_redis_backend()
            except RuntimeError:
                self._backend = MemoryCache()
    
    def _create_redis_backend(self) -> RedisCache:
        """Create Redis backend from environment variables."""
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        db = int(os.environ.get("REDIS_DB", "0"))
        return RedisCache(host=host, port=port, db=db)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._backend.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        self._backend.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._backend.delete(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._backend.clear()


# Global cache instance
_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


def cached(ttl: int = 300):
    """Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            cache = get_cache()
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
