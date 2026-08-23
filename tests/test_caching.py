"""Tests for the CacheMixin caching mechanism.

Tests verify that data fetching is properly cached to avoid hammering the
Tibber Data API, using a minimal concrete subclass of CacheMixin directly
(TestAdapter itself doesn't use CacheMixin -- it has no caching at all).
"""

from datetime import datetime, timedelta

from weconnect_mcp.adapter.mixins.cache_mixin import CacheMixin, CACHE_DURATION_SECONDS


class _CachingProbe(CacheMixin):
    """Minimal concrete CacheMixin user for testing the mixin in isolation."""

    def __init__(self):
        super().__init__()
        self.fetch_count = 0

    def _fetch_data(self) -> None:
        self.fetch_count += 1
        self._mark_data_fetched()


# ==================== CACHE DURATION TESTS ====================

def test_cache_duration_constant():
    """Test that cache duration constant is properly defined."""
    assert CACHE_DURATION_SECONDS == 300, "Cache duration should be 300 seconds (5 minutes)"


# ==================== CACHE BEHAVIOR TESTS ====================

def test_cache_expired_before_first_fetch():
    """A freshly constructed mixin has no data yet, so cache is expired."""
    probe = _CachingProbe()
    assert probe._is_cache_expired() is True


def test_ensure_fresh_data_fetches_once_when_expired():
    """_ensure_fresh_data() triggers exactly one fetch when cache is expired."""
    probe = _CachingProbe()
    probe._ensure_fresh_data()
    assert probe.fetch_count == 1
    assert probe._is_cache_expired() is False


def test_ensure_fresh_data_does_not_refetch_within_cache_window():
    """A second call within the cache window must not trigger another fetch."""
    probe = _CachingProbe()
    probe._ensure_fresh_data()
    probe._ensure_fresh_data()
    assert probe.fetch_count == 1


def test_ensure_fresh_data_refetches_after_expiry():
    """Once the cache window has passed, the next access fetches again."""
    probe = _CachingProbe()
    probe._ensure_fresh_data()
    assert probe.fetch_count == 1

    # Simulate time passing beyond the cache window.
    probe._last_fetch_time = datetime.now() - timedelta(seconds=CACHE_DURATION_SECONDS + 1)
    probe._ensure_fresh_data()
    assert probe.fetch_count == 2
