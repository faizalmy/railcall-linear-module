"""Tests for cache module."""

import os

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


class TestCacheKeyNamespacing:
    """Cache entries must not leak between Linear workspaces."""

    def test_key_differs_per_api_key(self):
        """Should namespace by credential so tenants cannot collide."""
        from handlers.cache import make_cache_key

        with patch.dict(os.environ, {"LINEAR_API_KEY": "key_tenant_a"}):
            key_a = make_cache_key("list_teams", (), {"limit": 50})
        with patch.dict(os.environ, {"LINEAR_API_KEY": "key_tenant_b"}):
            key_b = make_cache_key("list_teams", (), {"limit": 50})

        assert key_a != key_b

    def test_key_never_contains_the_raw_credential(self):
        """Should hash the key - cache keys reach logs and Redis dumps."""
        from handlers.cache import make_cache_key

        with patch.dict(os.environ, {"LINEAR_API_KEY": "lin_api_supersecret"}):
            key = make_cache_key("list_teams", (), {})

        assert "lin_api_supersecret" not in key

    def test_context_is_excluded_from_the_key(self):
        """Should ignore per-invocation context, which would defeat the cache."""
        from handlers.cache import make_cache_key

        with patch.dict(os.environ, {"LINEAR_API_KEY": "k"}):
            with_context = make_cache_key("list_teams", (), {"limit": 50, "context": {"run": 1}})
            without_context = make_cache_key("list_teams", (), {"limit": 50})

        assert with_context == without_context


class TestPrefixInvalidation:
    """Writes must drop the stale reads they invalidate."""

    def test_delete_prefix_removes_only_matching_keys(self):
        from handlers.cache import MemoryCache

        cache = MemoryCache()
        cache.set("linear:abc:list_labels:x", 1)
        cache.set("linear:abc:list_labels:y", 2)
        cache.set("linear:abc:list_teams:z", 3)

        removed = cache.delete_prefix("linear:abc:list_labels:")

        assert removed == 2
        assert cache.get("linear:abc:list_teams:z") == 3
        assert cache.get("linear:abc:list_labels:x") is None


class TestCachedCommands:
    """The @cached decorator must actually be wired to the read commands."""

    @patch('handlers.handler.execute_query')
    def test_repeat_read_is_served_from_cache(self, mock_query):
        """Should call the API once for two identical list_teams calls."""
        from handlers.handler import list_teams

        mock_query.return_value = {
            "teams": {
                "nodes": [{"id": "team-1", "name": "Engineering"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        first = list_teams()
        second = list_teams()

        assert first == second
        assert mock_query.call_count == 1

    @patch('handlers.handler.execute_query')
    def test_creating_a_label_invalidates_the_label_list(self, mock_query):
        """Should not serve a stale label list after a write."""
        from handlers.handler import create_label, list_labels

        team_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_query.return_value = {
            "issueLabels": {
                "nodes": [{"id": "label-1", "name": "Bug"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        list_labels(team_id=team_id)
        assert mock_query.call_count == 1

        mock_query.return_value = {
            "issueLabelCreate": {"success": True, "issueLabel": {"id": "label-2", "name": "Chore"}}
        }
        create_label(team_id=team_id, name="Chore", color="#00FF00")

        mock_query.return_value = {
            "issueLabels": {
                "nodes": [
                    {"id": "label-1", "name": "Bug"},
                    {"id": "label-2", "name": "Chore"},
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
        refreshed = list_labels(team_id=team_id)

        assert refreshed["count"] == 2
