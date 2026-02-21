from supabase import create_client, Client
from app.config import settings
from cachetools import cached, TTLCache

_client: Client | None = None

# Cache with a time-to-live of 300 seconds and a max size of 100 items
cache = TTLCache(maxsize=100, ttl=300)


@cached(cache)
def get_frequently_accessed_data(param1, param2):
    # existing database logic
    return {"param1": param1, "param2": param2}


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
