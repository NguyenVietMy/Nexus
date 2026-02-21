## Feature: Data Caching Layer

### Description
Implement a caching layer to reduce database load and improve data retrieval times by storing frequently accessed data in memory. Use a caching library to manage cache storage, invalidation, and refreshing.

### Files to Modify
1. `backend/app/db.py`
2. `backend/app/services/graph_cache.py`

### Implementation Steps

#### 1. Modify `backend/app/db.py`
- **Import Statements**: Add the necessary import for the caching library.
  ```python
  from cachetools import cached, TTLCache
  ```

- **Global Cache Instance**: Define a global cache instance.
  ```python
  # Cache with a time-to-live of 300 seconds and a max size of 100 items
  cache = TTLCache(maxsize=100, ttl=300)
  ```

- **Decorate Functions**: Identify and decorate functions that will benefit from caching.
  ```python
  @cached(cache)
  def get_frequently_accessed_data(param1, param2):
      # existing database logic
      pass
  ```
  
#### 2. Modify `backend/app/services/graph_cache.py`
- **Import Statements**: Add imports related to cache invalidation.
  ```python
  from backend.app.db import cache
  ```

- **Cache Invalidation Function**: Implement a function to clear specific cache entries.
  ```python
  def invalidate_cache_entry(key):
      if key in cache:
          del cache[key]
  ```

- **Cache Refresh Strategy**: Implement a basic cache refreshing strategy.
  ```python
  def refresh_cache():
      # Logic to refresh cache entries
      # Iterate over keys and refresh data
      for key in list(cache.keys()):
          # Refresh logic, possibly involving re-fetching data
          cache[key] = fetch_new_data_for_key(key)
  ```

### Verification
After implementing the above changes, run the following test file to confirm the feature works as expected:
- `pytest tests/test_data-caching-layer.py`

Ensure that cache hits and misses are logged correctly, cache invalidation works as intended, and performance improvements are verified.