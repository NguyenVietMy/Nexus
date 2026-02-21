import unittest
from unittest.mock import patch, MagicMock
from cachetools import TTLCache
from backend.app.db import cache, get_frequent_data
from backend.app.services.graph_cache import invalidate_cache, refresh_cache_entry

class TestDataCachingLayer(unittest.TestCase):
    def setUp(self):
        # Set up a controlled cache environment for testing
        self.test_cache = TTLCache(maxsize=100, ttl=300)
        cache.clear()

    @patch('backend.app.db.get_supabase')
    def test_cache_hit_and_miss(self, mock_supabase):
        # Mock the Supabase client chain
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{'id': 1}]
        mock_supabase.return_value = mock_client
        # Simulate a cache miss
        result1 = get_frequent_data('param1', 'param2')
        self.assertIsNotNone(result1)
        # Simulate a cache hit
        result2 = get_frequent_data('param1', 'param2')
        self.assertEqual(result1, result2)

    @patch('backend.app.db.get_supabase')
    def test_cache_invalidation(self, mock_supabase):
        # Mock the Supabase client chain
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{'id': 1}]
        mock_supabase.return_value = mock_client
        # Populate cache
        get_frequent_data('param1', 'param2')
        self.assertIn(('param1', 'param2'), cache)
        # Invalidate cache
        invalidate_cache()
        self.assertNotIn(('param1', 'param2'), cache)

    def test_cache_refresh(self):
        # Refresh a specific cache entry
        refresh_cache_entry(('param1', 'param2'), 'new_value')
        self.assertEqual(cache[('param1', 'param2')], 'new_value')

if __name__ == '__main__':
    unittest.main()
