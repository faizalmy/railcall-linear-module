"""Tests for cache module."""

import pytest
from unittest.mock import Mock, patch
from handlers.cache import CacheManager


class TestCacheManager:
    """Test cache manager functionality."""
    
    def test_memory_cache_set_get(self):
        """Should store and retrieve values from memory cache."""
        cache = CacheManager(backend="memory")
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        assert result == {"data": "value"}
    
    def test_memory_cache_ttl(self):
        """Should expire values after TTL."""
        cache = CacheManager(backend="memory")
        cache.set("test_key", {"data": "value"}, ttl=0)
        result = cache.get("test_key")
        assert result is None
    
    def test_memory_cache_delete(self):
        """Should delete values from cache."""
        cache = CacheManager(backend="memory")
        cache.set("test_key", {"data": "value"})
        cache.delete("test_key")
        result = cache.get("test_key")
        assert result is None
    
    def test_memory_cache_clear(self):
        """Should clear all values from cache."""
        cache = CacheManager(backend="memory")
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    @patch('redis.Redis')
    def test_redis_cache_connection(self, mock_redis):
        """Should connect to Redis when available."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        
        cache = CacheManager(backend="redis")
        assert cache._backend is not None
    
    @patch('redis.Redis')
    def test_redis_cache_fallback_to_memory(self, mock_redis):
        """Should fallback to memory cache when Redis unavailable."""
        mock_redis.side_effect = Exception("Connection failed")
        
        cache = CacheManager(backend="auto")
        # Should fallback to memory cache
        assert cache._backend is not None
    
    def test_auto_backend_selection(self):
        """Should auto-select backend based on availability."""
        cache = CacheManager(backend="auto")
        # Should work without errors
        assert cache._backend is not None
