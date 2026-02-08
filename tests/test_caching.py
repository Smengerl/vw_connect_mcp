"""Tests for carconnectivity_adapter caching mechanism.

Tests verify that data fetching is properly cached to avoid VW API rate limits.
These tests use the real CarConnectivityAdapter (not the mock).
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter, CACHE_DURATION_SECONDS


def test_cache_duration_constant():
    """Test that cache duration constant is properly defined."""
    assert CACHE_DURATION_SECONDS == 60, "Cache duration should be 60 seconds"


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
    with patch.object(real_adapter.car_connectivity, 'fetch_all') as mock_fetch:
        # First call - cache just initialized, should not fetch again
        vehicles1 = real_adapter.list_vehicles()
        assert len(vehicles1) > 0
        mock_fetch.assert_not_called()
        
        # Second call immediately after - should still use cache
        vehicles2 = real_adapter.list_vehicles()
        assert vehicles1 == vehicles2
        mock_fetch.assert_not_called()


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
