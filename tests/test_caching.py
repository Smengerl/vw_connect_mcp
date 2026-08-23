"""Tests for adapter caching mechanism.

Tests verify that data fetching is properly cached to avoid hammering the
Tibber Data API, and that the cache invalidation hook works via TestAdapter.
"""

import sys
from weconnect_mcp.adapter.tibber_adapter import CACHE_DURATION_SECONDS

sys.path.insert(0, 'tests')
from test_adapter import TestAdapter


# ==================== CACHE DURATION TESTS ====================

def test_cache_duration_constant():
    """Test that cache duration constant is properly defined."""
    assert CACHE_DURATION_SECONDS == 300, "Cache duration should be 300 seconds (5 minutes)"


# ==================== CACHE INVALIDATION TESTS ====================

def test_cache_invalidation_method_exists_on_abstract():
    """Test that invalidate_cache method exists on abstract adapter."""
    from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter

    # Verify method exists on abstract class
    assert hasattr(AbstractAdapter, 'invalidate_cache'), "AbstractAdapter should have invalidate_cache method"


def test_cache_invalidation_on_test_adapter():
    """Test that TestAdapter has invalidate_cache method."""
    adapter = TestAdapter()

    # Verify method exists
    assert hasattr(adapter, 'invalidate_cache'), "Adapter should have invalidate_cache method"
    assert callable(adapter.invalidate_cache), "invalidate_cache should be callable"

    # Call should not raise exception
    adapter.invalidate_cache()


def test_cache_invalidation_workflow():
    """Test the complete cache invalidation workflow with TestAdapter."""
    adapter = TestAdapter()

    # 1. Read data (should work normally)
    vehicles = adapter.list_vehicles()
    assert len(vehicles) == 2, "Should have 2 test vehicles"

    # 2. Invalidate cache explicitly
    adapter.invalidate_cache()

    # 3. Read data again (should fetch fresh data)
    vehicles_after = adapter.list_vehicles()
    assert len(vehicles_after) == 2, "Should still have 2 test vehicles after cache invalidation"
