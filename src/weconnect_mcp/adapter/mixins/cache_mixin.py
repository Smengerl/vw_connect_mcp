"""Cache management mixin for adapter.

Provides data caching functionality so the adapter isn't hammering the
Tibber Data API on every tool call. Tracks last fetch time and ensures data
freshness.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

# Cache duration — Tibber's own API docs ask clients to be polite about
# polling frequency.
CACHE_DURATION_SECONDS = 300  # 5 minutes

logger = logging.getLogger(__name__)


class CacheMixin:
    """Mixin providing caching functionality for adapter.

    Manages data freshness by tracking last fetch time and providing a
    method to check if the cache is expired.

    Attributes:
        _last_fetch_time: Timestamp of last data fetch from server
        _cache_duration: How long data stays fresh before refresh
    """
    
    def __init__(self):
        """Initialize cache state."""
        self._last_fetch_time: Optional[datetime] = None
        self._cache_duration = timedelta(seconds=CACHE_DURATION_SECONDS)
    
    def _is_cache_expired(self) -> bool:
        """Check if cached data has expired and needs refresh.
        
        Returns:
            True if cache is expired or no data fetched yet
        """
        if self._last_fetch_time is None:
            return True
        
        time_since_fetch = datetime.now() - self._last_fetch_time
        is_expired = time_since_fetch >= self._cache_duration
        
        if is_expired:
            logger.info(f"Cache expired ({time_since_fetch.total_seconds():.1f}s since last fetch)")
        else:
            logger.debug(f"Using cached data ({time_since_fetch.total_seconds():.1f}s old)")
        
        return is_expired
    
    def _ensure_fresh_data(self) -> None:
        """Ensure data is fresh, fetching from server if cache expired.
        
        Calls _fetch_data() if cache is expired. Subclass must implement _fetch_data().
        """
        if self._is_cache_expired():
            self._fetch_data()
    
    def _mark_data_fetched(self) -> None:
        """Mark that fresh data was just fetched.
        
        Updates the cache timestamp to now. Should be called after _fetch_data().
        """
        self._last_fetch_time = datetime.now()
        logger.debug("Cache timestamp updated")
    
    def _fetch_data(self) -> None:
        """Fetch data from server and update cache timestamp.
        
        Must be implemented by subclass. Should fetch data and call _mark_data_fetched().
        """
        raise NotImplementedError("Subclass must implement _fetch_data()")
