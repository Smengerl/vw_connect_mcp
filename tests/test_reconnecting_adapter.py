"""
Tests for ReconnectingAdapter (starting_adapter.py)
======================================================

Covers the no-restart-needed self-healing behavior: when the current
delegate raises AdapterUnavailableError, ReconnectingAdapter retries
`build()` once (subject to a cooldown) and re-attempts the same call
against whatever that produces -- so completing the Tibber login (or the
refresh token going bad ~30 days into an otherwise-healthy run) heals on
the very next tool call instead of requiring a human to restart the whole
MCP server process.

No real Tibber/network calls: `build` is a plain test double.
"""
import time
from unittest.mock import MagicMock

import pytest

from weconnect_mcp.adapter.abstract_adapter import AdapterUnavailableError
from weconnect_mcp.adapter.starting_adapter import ReconnectingAdapter, UnavailableAdapter


class _WorkingAdapter:
    """Minimal stand-in for a successfully-connected real adapter."""

    def __init__(self, vin: str = "WVWZZZ") -> None:
        self.vin = vin
        self.shutdown = MagicMock()

    def list_vehicles(self):
        return [self.vin]

    def get_vehicle(self, vehicle_id, *args, **kwargs):
        return {"vin": self.vin, "args": args, "kwargs": kwargs}

    def get_energy_status(self, vehicle_id):
        return {"vin": self.vin}

    def health_status(self):
        return {"ready": True}


def _broken(message="broken", error_type="unavailable"):
    adapter = UnavailableAdapter(message, error_type=error_type)
    return adapter


def test_passthrough_when_delegate_already_works():
    working = _WorkingAdapter()
    build = MagicMock(side_effect=AssertionError("build() must not be called when the delegate already works"))
    adapter = ReconnectingAdapter(build, working)

    assert adapter.list_vehicles() == [working.vin]
    build.assert_not_called()


def test_heals_on_next_call_after_build_succeeds():
    working = _WorkingAdapter()
    build = MagicMock(return_value=working)
    adapter = ReconnectingAdapter(build, _broken())

    result = adapter.list_vehicles()

    assert result == [working.vin]
    build.assert_called_once()


def test_stays_broken_with_fresh_message_if_rebuild_also_fails():
    def build():
        raise RuntimeError("still not configured")

    adapter = ReconnectingAdapter(build, _broken("original failure"))

    with pytest.raises(AdapterUnavailableError) as exc_info:
        adapter.get_energy_status("some-vin")

    assert "still not configured" in str(exc_info.value)
    assert exc_info.value.error_type == "unavailable"


def test_rebuild_error_type_falls_back_to_unavailable_without_error_type_attr():
    def build():
        raise RuntimeError("plain exception, no .error_type")

    adapter = ReconnectingAdapter(build, _broken())

    with pytest.raises(AdapterUnavailableError) as exc_info:
        adapter.list_vehicles()

    assert exc_info.value.error_type == "unavailable"


def test_rebuild_error_type_is_preserved_when_exception_carries_one():
    class _TypedError(RuntimeError):
        error_type = "reauth_required"

    def build():
        raise _TypedError("still needs login")

    adapter = ReconnectingAdapter(build, _broken())

    with pytest.raises(AdapterUnavailableError) as exc_info:
        adapter.get_vehicle("some-vin")

    assert exc_info.value.error_type == "reauth_required"


def test_does_not_rebuild_again_within_cooldown():
    """Directly set _last_attempt to "just now" instead of relying on
    system uptime exceeding the cooldown -- avoids any flakiness on a
    freshly-booted CI runner/VM where time.monotonic() might otherwise be
    small."""
    import time as time_module

    build_calls = []

    def build():
        build_calls.append(1)
        raise RuntimeError("still broken")

    adapter = ReconnectingAdapter(build, _broken())
    adapter._last_attempt = time_module.monotonic()  # simulate "an attempt just happened"

    with pytest.raises(AdapterUnavailableError):
        adapter.list_vehicles()

    assert build_calls == []  # still within the cooldown -- must not retry yet


def test_rebuilds_again_after_cooldown_elapses():
    import time as time_module

    build_calls = []

    def build():
        build_calls.append(1)
        raise RuntimeError("still broken")

    adapter = ReconnectingAdapter(build, _broken())
    adapter._last_attempt = time_module.monotonic() - 9999.0  # long enough ago

    with pytest.raises(AdapterUnavailableError):
        adapter.list_vehicles()

    assert len(build_calls) == 1


def test_heals_a_previously_working_delegate_that_starts_failing():
    """Not just the initial not-yet-connected window: if an already-live
    delegate later raises AdapterUnavailableError too (e.g. a refresh
    token finally expiring), the same rebuild-and-retry must kick in."""
    healthy_again = _WorkingAdapter("new-vin-after-relogin")
    build = MagicMock(return_value=healthy_again)

    class _NowFailingAdapter:
        def list_vehicles(self):
            raise AdapterUnavailableError("refresh token expired", error_type="reauth_required")

    adapter = ReconnectingAdapter(build, _NowFailingAdapter())

    result = adapter.list_vehicles()

    assert result == ["new-vin-after-relogin"]
    build.assert_called_once()


def test_get_vehicle_forwards_extra_args_and_kwargs():
    working = _WorkingAdapter()
    adapter = ReconnectingAdapter(MagicMock(), working)

    result = adapter.get_vehicle("some-vin", "extra-positional", details="FULL")

    assert result == {"vin": working.vin, "args": ("extra-positional",), "kwargs": {"details": "FULL"}}


def test_shutdown_delegates_to_current_adapter():
    working = _WorkingAdapter()
    adapter = ReconnectingAdapter(MagicMock(), working)

    adapter.shutdown()

    working.shutdown.assert_called_once()


def test_context_manager_calls_shutdown_on_exit():
    working = _WorkingAdapter()
    with ReconnectingAdapter(MagicMock(), working) as adapter:
        assert adapter.list_vehicles() == [working.vin]

    working.shutdown.assert_called_once()


# ==================== exponential backoff ====================

def test_cooldown_doubles_after_each_consecutive_failure():
    adapter = ReconnectingAdapter(MagicMock(), _broken())

    assert adapter._current_cooldown() == 10.0
    adapter._consecutive_failures = 1
    assert adapter._current_cooldown() == 20.0
    adapter._consecutive_failures = 2
    assert adapter._current_cooldown() == 40.0
    adapter._consecutive_failures = 3
    assert adapter._current_cooldown() == 80.0


def test_cooldown_is_capped_so_it_never_grows_unbounded():
    adapter = ReconnectingAdapter(MagicMock(), _broken())

    adapter._consecutive_failures = 10  # would be 10240s uncapped
    assert adapter._current_cooldown() == 300.0


def test_repeated_failures_use_a_growing_cooldown_not_a_flat_one():
    """A backend that can never self-heal without a human editing config
    (e.g. a permanently wrong client_secret) must not be hammered with a
    fresh build attempt every fixed 10s forever -- each consecutive
    failure should push the next retry further out."""
    import time as time_module

    build_calls = []

    def build():
        build_calls.append(1)
        raise RuntimeError("still broken")

    adapter = ReconnectingAdapter(build, _broken())

    # First failure: consumes the "always retry immediately" sentinel.
    adapter._last_attempt = time_module.monotonic() - 9999.0
    with pytest.raises(AdapterUnavailableError):
        adapter.list_vehicles()
    assert len(build_calls) == 1
    assert adapter._consecutive_failures == 1

    # 15s later: still within the now-doubled 20s cooldown -- no retry yet.
    adapter._last_attempt = time_module.monotonic() - 15.0
    with pytest.raises(AdapterUnavailableError):
        adapter.list_vehicles()
    assert len(build_calls) == 1

    # 25s later: past the 20s cooldown -- retries, and fails again.
    adapter._last_attempt = time_module.monotonic() - 25.0
    with pytest.raises(AdapterUnavailableError):
        adapter.list_vehicles()
    assert len(build_calls) == 2
    assert adapter._consecutive_failures == 2


def test_consecutive_failure_count_resets_after_a_successful_reconnect():
    working = _WorkingAdapter()
    build = MagicMock(return_value=working)
    adapter = ReconnectingAdapter(build, _broken())
    adapter._consecutive_failures = 3  # pretend it had already backed off

    adapter._last_attempt = 0.0
    result = adapter.list_vehicles()

    assert result == [working.vin]
    assert adapter._consecutive_failures == 0
    assert adapter._current_cooldown() == 10.0  # back to the base cooldown


# ==================== health_status() ====================

def test_health_status_passes_through_when_already_working():
    working = _WorkingAdapter()
    build = MagicMock(side_effect=AssertionError("must not rebuild when already working"))
    adapter = ReconnectingAdapter(build, working)

    assert adapter.health_status() == {"ready": True}
    build.assert_not_called()


def test_health_status_reports_unavailable_delegate_state():
    adapter = ReconnectingAdapter(MagicMock(), _broken("still broken", error_type="invalid_client"))
    adapter._last_attempt = time.monotonic()  # inside cooldown -- no rebuild attempt

    assert adapter.health_status() == {
        "ready": False,
        "error_type": "invalid_client",
        "message": "still broken",
    }


def test_health_status_attempts_reconnect_if_due():
    """health_status() must retry a due rebuild itself, not just report
    the stale delegate -- this is what lets a passive /health probe
    self-heal without needing a real tool call first."""
    healed = _WorkingAdapter()
    build = MagicMock(return_value=healed)
    adapter = ReconnectingAdapter(build, _broken())
    adapter._last_attempt = 0.0  # cooldown long elapsed

    assert adapter.health_status() == {"ready": True}
    build.assert_called_once()
