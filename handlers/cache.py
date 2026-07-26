"""Caching layer with Redis and in-memory fallback."""

import hashlib
import logging
import os
import json
import time
from typing import Any, Callable, Dict, Optional
from functools import wraps

from .credentials import resolve_api_key

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base cache backend interface."""

    def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def delete_prefix(self, prefix: str) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support."""
    
    def __init__(self) -> None:
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

    def delete_prefix(self, prefix: str) -> int:
        """Delete every key starting with prefix. Returns the number removed."""
        doomed = [k for k in self._cache if k.startswith(prefix)]
        for key in doomed:
            del self._cache[key]
        return len(doomed)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        url: Optional[str] = None,
    ) -> None:
        try:
            import redis
            client: Any = (
                redis.Redis.from_url(url, decode_responses=True)
                if url
                else redis.Redis(host=host, port=port, db=db, decode_responses=True)
            )
            client.ping()  # Test connection
            self._client = client
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Redis: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        value = self._client.get(key)
        if value is None:
            return None
        return json.loads(str(value))
    
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

    def delete_prefix(self, prefix: str) -> int:
        """Delete every key starting with prefix. Returns the number removed."""
        removed = 0
        # scan_iter avoids blocking the server the way KEYS would
        for key in self._client.scan_iter(match=f"{prefix}*", count=500):
            self._client.delete(key)
            removed += 1
        return removed

    def clear(self) -> None:
        """Clear all keys (use with caution)."""
        self._client.flushdb()


class CacheManager:
    """Cache manager with automatic backend selection."""
    
    def __init__(self, backend: Optional[str] = None) -> None:
        """Initialize cache manager.
        
        Args:
            backend: Cache backend ('redis', 'memory', or None for auto-detect)
        """
        self._backend: CacheBackend
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
        """Create Redis backend from environment variables.

        REDIS_URL is the documented setting; REDIS_HOST/PORT/DB remain supported
        for deployments that pass the parts separately.
        """
        url = os.environ.get("REDIS_URL")
        if url:
            return RedisCache(url=url)

        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        db = int(os.environ.get("REDIS_DB", "0"))
        if not os.environ.get("REDIS_PASSWORD") and not url:
            logger.warning(
                "Redis connection without authentication — set REDIS_URL with "
                "credentials for production"
            )
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

    def delete_prefix(self, prefix: str) -> int:
        """Delete every key starting with prefix. Returns the number removed."""
        return self._backend.delete_prefix(prefix)

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


def cache_namespace() -> str:
    """Namespace prefix identifying the credential the cache entries belong to.

    A shared Redis instance may serve several Linear workspaces. Without this,
    two tenants running the same command with the same arguments would collide
    on one key and read each other's data. The key is hashed, never stored raw.
    """
    api_key = resolve_api_key() or ""
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    return f"linear:{digest}"


def make_cache_key(func_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
    """Build a tenant-scoped cache key for a call.

    The RailCall `context` argument is excluded - it carries per-invocation data
    that would otherwise make every key unique and defeat the cache.
    """
    parts = [str(arg) for arg in args]
    parts.extend(
        f"{k}={v}" for k, v in sorted(kwargs.items()) if k != "context"
    )
    # The separator after func_name is always emitted, including for a no-argument
    # call. Without it a key like "...:list_projects" would not match the
    # "...:list_projects:" prefix that invalidate() deletes.
    return f"{cache_namespace()}:{func_name}:" + ":".join(parts)


def invalidate(func_name: str) -> int:
    """Drop every cached entry for one command. Returns the number removed."""
    return get_cache().delete_prefix(f"{cache_namespace()}:{func_name}:")


def invalidate_all(*func_names: str) -> None:
    """Drop cached entries for several commands after a write."""
    for name in func_names:
        invalidate(name)


def cached(ttl: int = 300) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache function results.

    Only applied to reads of slow-changing workspace metadata (teams, projects,
    users, states, labels). Issue and comment reads are left uncached so they
    always reflect the current state.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = make_cache_key(func.__name__, args, kwargs)

            cache = get_cache()

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        setattr(wrapper, "invalidate", lambda: invalidate(func.__name__))
        return wrapper
    return decorator
