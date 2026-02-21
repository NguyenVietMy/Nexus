import pytest
from cachetools import TTLCache
from backend.app.db import get_frequently_accessed_data, cache
from backend.app.services.graph_cache import invalidate_cache_entry, refresh_cache


def test_cache_hits_and_misses():
    # Initially, the cache should be empty
    assert len(cache) == 0

    # Access the data, should result in a cache miss and populate the cache
    get_frequently_accessed_data('param1', 'param2')
    assert len(cache) == 1

    # Access the same data, should result in a cache hit
    get_frequently_accessed_data('param1', 'param2')
    assert len(cache) == 1  # Cache size should remain the same


def test_cache_invalidation():
    # Access data to populate the cache
    get_frequently_accessed_data('param1', 'param2')
    assert len(cache) == 1

    # Invalidate the cache entry
    invalidate_cache_entry(('param1', 'param2'))
    assert len(cache) == 0


def test_cache_refresh():
    # Populate cache with an entry
    get_frequently_accessed_data('param1', 'param2')
    assert len(cache) == 1

    # Refresh the cache
    refresh_cache()
    # Ensure the cache is still populated after refresh
    assert len(cache) == 1
    # Optionally check if the data is updated if possible