from supabase import create_client, Client
from cachetools import cached, TTLCache
from app.config import settings

# Define a cache with a TTL of 300 seconds and a max size of 100 items
cache = TTLCache(maxsize=100, ttl=300)

_client: Client | None = None


@cached(cache)
def get_frequent_data(param1, param2):
    """Fetch frequently accessed data from the database."""
    supabase = get_supabase()
    result = supabase.table("frequent_data").select("*").eq("param1", param1).eq("param2", param2).execute()
    return result.data


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
