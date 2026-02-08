"""Tests for adapter caching mechanism.

Tests verify that data fetching is properly cached to avoid VW API rate limits,
and that cache is properly invalidated after command execution.

These tests use both TestAdapter (for cache invalidation workflow) and 
real CarConnectivityAdapter (for actual caching behavior).
"""

import pytest
import time
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter, CACHE_DURATION_SECONDS

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
    
    # 2. Execute a command (should invalidate cache)
    result = adapter.execute_command("WVWZZZED4SE003938", "lock")
    assert result["success"] is True
    
    # 3. Invalidate cache explicitly
    adapter.invalidate_cache()
    
    # 4. Read data again (should fetch fresh data)
    vehicles_after = adapter.list_vehicles()
    assert len(vehicles_after) == 2, "Should still have 2 test vehicles after cache invalidation"


# ==================== CACHE BEHAVIOR TESTS (Real Adapter) ====================


@pytest.mark.carconnectivity
def test_initial_fetch_on_init(real_adapter):
    """Test that data is fetched on adapter initialization."""
    # Adapter from fixture already initialized, check that last_fetch_time is set
    assert real_adapter._last_fetch_time is not None
    assert isinstance(real_adapter._last_fetch_time, datetime)


@pytest.mark.carconnectivity
def test_cache_not_expired_within_duration(real_adapter):
    """Test that cache is not expired immediately after fetch."""
    # Just initialized, cache should be fresh
    assert not real_adapter._is_cache_expired()
    
    # Still fresh after short wait
    time.sleep(0.1)
    assert not real_adapter._is_cache_expired()


@pytest.mark.carconnectivity
def test_cache_expires_after_duration(real_adapter):
    """Test that cache expires after configured duration."""
    # Manually set last fetch time to past
    past_time = datetime.now() - timedelta(seconds=CACHE_DURATION_SECONDS + 1)
    real_adapter._last_fetch_time = past_time
    
    # Cache should be expired
    assert real_adapter._is_cache_expired()


@pytest.mark.carconnectivity
def test_list_vehicles_uses_cache(real_adapter):
    """Test that list_vehicles() reuses cached data within cache duration."""
    # Note: real_adapter is module-scoped and may have been used by previous tests,
    # so cache might be expired. We test that SUBSEQUENT calls use the cache.
    with patch.object(real_adapter.car_connectivity, 'fetch_all') as mock_fetch:
        # First call - might fetch if cache is expired
        vehicles1 = real_adapter.list_vehicles()
        assert len(vehicles1) > 0
        first_call_count = mock_fetch.call_count
        
        # Second call immediately after - should use cache, no additional fetch
        vehicles2 = real_adapter.list_vehicles()
        assert vehicles1 == vehicles2
        assert mock_fetch.call_count == first_call_count, "Second call should not fetch again"


@pytest.mark.carconnectivity
def test_list_vehicles_fetches_when_expired(real_adapter):
    """Test that list_vehicles() fetches new data when cache expired."""
    with patch.object(real_adapter.car_connectivity, 'fetch_all') as mock_fetch:
        # Expire cache
        past_time = datetime.now() - timedelta(seconds=CACHE_DURATION_SECONDS + 1)
        real_adapter._last_fetch_time = past_time
        
        # Call should trigger fetch
        vehicles = real_adapter.list_vehicles()
        assert len(vehicles) > 0
        mock_fetch.assert_called_once()


@pytest.mark.carconnectivity
def test_get_vehicle_uses_cache(real_adapter):
    """Test that get_vehicle() reuses cached data within cache duration."""
    vehicles = real_adapter.list_vehicles()
    test_vin = vehicles[0].vin if vehicles else None
    
    if test_vin is None:
        pytest.skip("No vehicles available in test data")
    
    with patch.object(real_adapter.car_connectivity, 'fetch_all') as mock_fetch:
        # First call - cache fresh, should not fetch
        vehicle1 = real_adapter.get_vehicle(test_vin)
        assert vehicle1 is not None
        mock_fetch.assert_not_called()
        
        # Second call - should still use cache
        vehicle2 = real_adapter.get_vehicle(test_vin)
        assert vehicle1.vin == vehicle2.vin
        mock_fetch.assert_not_called()


@pytest.mark.carconnectivity
def test_get_vehicle_fetches_when_expired(real_adapter):
    """Test that get_vehicle() fetches new data when cache expired."""
    vehicles = real_adapter.list_vehicles()
    test_vin = vehicles[0].vin if vehicles else None
    
    if test_vin is None:
        pytest.skip("No vehicles available in test data")
    
    with patch.object(real_adapter.car_connectivity, 'fetch_all') as mock_fetch:
        # Expire cache
        past_time = datetime.now() - timedelta(seconds=CACHE_DURATION_SECONDS + 1)
        real_adapter._last_fetch_time = past_time
        
        # Call should trigger fetch
        vehicle = real_adapter.get_vehicle(test_vin)
        assert vehicle is not None
        mock_fetch.assert_called_once()


@pytest.mark.carconnectivity
def test_ensure_fresh_data_updates_timestamp(real_adapter):
    """Test that _ensure_fresh_data updates last_fetch_time."""
    # Expire cache
    past_time = datetime.now() - timedelta(seconds=CACHE_DURATION_SECONDS + 1)
    real_adapter._last_fetch_time = past_time
    
    # Trigger fresh data
    real_adapter._ensure_fresh_data()
    
    # Timestamp should be updated to now
    time_diff = datetime.now() - real_adapter._last_fetch_time
    assert time_diff.total_seconds() < 1  # Should be very recent
