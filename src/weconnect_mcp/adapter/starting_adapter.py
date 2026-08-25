"""Stub adapters used when the real (Tibber) adapter isn't in play yet.

Two distinct situations, two distinct classes -- don't conflate them:

- UnavailableAdapter: the real backend could not be constructed at all --
  no cached Tibber tokens, or a refresh that failed with a genuine
  (non-race) rejection, see ARCHITECTURE.md §2.4 -- and won't become
  available without a human re-authorizing. Every call raises
  AdapterUnavailableError, which read_tools.py's _handle_unavailable turns
  into a clear "server_unavailable" tool response.

- ReconnectingAdapter: wraps a build function and retries it on the next
  call after any AdapterUnavailableError, instead of staying permanently
  stuck (or permanently broken again later) until a human restarts the
  whole MCP server process. This is what turns "run the login tool, then
  restart the server" into just "run the login tool" -- whether the fix
  is completing the one-time interactive login, finally setting
  TIBBER_CLIENT_ID/SECRET, or a refresh token going bad ~30 days into an
  otherwise-healthy run. See its own docstring below for the exact
  cooldown/retry mechanics.
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from typing import Any

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, AdapterUnavailableError, EnergyStatusModel, VehicleModel, VehicleListItem,
)

# How long to wait after a failed reconnect attempt before trying again --
# bounds the cost of a persistently broken backend to one build attempt per
# window, no matter how many tool calls (or /health probes) land in
# between, while still recovering promptly once the human actually fixes
# it. Doubles after each consecutive failure up to the cap: a backend
# that's still broken 5 failures in (a config that will never fix itself
# without a human editing it -- e.g. a bad client_secret, see
# ReconnectingAdapter's docstring) settles into checking every 5 minutes
# instead of hammering Tibber's API every 10 seconds forever.
_RECONNECT_BASE_COOLDOWN_SECONDS = 10.0
_RECONNECT_MAX_COOLDOWN_SECONDS = 300.0


class UnavailableAdapter(AbstractAdapter):
    """Stub used when the real backend could not be constructed at all and
    won't recover without a human re-authorizing (see module docstring).
    Every method raises AdapterUnavailableError with the original
    remediation message and error_type (see tibber_client.py's
    TibberAuthError subclasses for the codes this project produces --
    "unavailable" is the generic fallback for a non-Tibber-specific
    failure, e.g. a malformed credentials file).
    """

    def __init__(self, message: str, error_type: str = "unavailable") -> None:
        self._message = message
        self._error_type = error_type

    @property
    def message(self) -> str:
        return self._message

    @property
    def error_type(self) -> str:
        return self._error_type

    def health_status(self) -> dict[str, Any]:  # type: ignore[override]
        return {"ready": False, "error_type": self._error_type, "message": self._message}

    def list_vehicles(self) -> list[VehicleListItem]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message, error_type=self._error_type)

    def get_vehicle(self, vehicle_id: str, details=None) -> Optional[VehicleModel]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message, error_type=self._error_type)

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message, error_type=self._error_type)

    def shutdown(self) -> None:  # type: ignore[override]
        pass

    def __enter__(self) -> "UnavailableAdapter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.shutdown()


class ReconnectingAdapter(AbstractAdapter):
    """Delegates to a lazily-rebuilt backend adapter, retrying the build on
    the next call after any AdapterUnavailableError -- subject to an
    exponential-backoff cooldown (see module-level constants) so a
    persistently broken backend isn't hammered with a full rebuild attempt
    forever.

    ``build`` is a zero-arg callable with the same contract
    ``_build_tibber_adapter`` already has: return a working adapter, or
    raise. Kept backend-agnostic here (nothing Tibber-specific is
    imported) even though the sole caller today only ever wraps a Tibber
    build -- same convention as UnavailableAdapter above.
    Any exception ``build`` raises becomes the new delegate's
    UnavailableAdapter state, keyed off ``error_type`` if the exception
    happens to carry one (every TibberAuthError subclass does) or falling
    back to "unavailable" if not.

    Not limited to the initial "never connected yet" window: if a call
    against an already-live, previously-working delegate later raises
    AdapterUnavailableError too (e.g. the refresh token itself finally
    expires after ~30 days and TibberAdapter's own retry/refresh logic in
    ARCHITECTURE.md §2.4 gives up), the same rebuild-and-retry kicks in --
    a human who reruns the login tool at that point doesn't need to
    restart the server either. There's nothing to clean up on the
    replaced delegate either way: TibberAdapter.shutdown() is a documented
    no-op (the client holds no persistent connection), so dropping a
    superseded delegate in favor of a freshly built one is always safe.
    """

    def __init__(self, build: Callable[[], AbstractAdapter], initial: AbstractAdapter) -> None:
        self._build = build
        self._delegate = initial
        self._lock = threading.Lock()
        self._last_attempt = 0.0  # 0.0 so the very first call retries immediately, no initial cooldown
        self._consecutive_failures = 0

    def _current_cooldown(self) -> float:
        return min(
            _RECONNECT_BASE_COOLDOWN_SECONDS * (2 ** self._consecutive_failures),
            _RECONNECT_MAX_COOLDOWN_SECONDS,
        )

    def _reconnect_if_due(self) -> None:
        """Rebuild the delegate if the cooldown has elapsed. Callers are
        expected to already know a rebuild is worth attempting -- _call()
        only reaches this from inside an except AdapterUnavailableError
        block (i.e. a real call against the current delegate just
        failed), and health_status() checks isinstance(delegate,
        UnavailableAdapter) itself before calling this, so an
        already-healthy delegate is never rebuilt from a passive /health
        probe alone.
        """
        if time.monotonic() - self._last_attempt < self._current_cooldown():
            return
        with self._lock:
            # Re-check under the lock: a concurrent call may have already
            # retried (and possibly succeeded, or reset the cooldown clock)
            # while we were waiting for it.
            if time.monotonic() - self._last_attempt < self._current_cooldown():
                return
            self._last_attempt = time.monotonic()
            try:
                self._delegate = self._build()
                self._consecutive_failures = 0
            except Exception as exc:  # noqa: BLE001 -- any failure just becomes the new delegate's error state
                self._consecutive_failures += 1
                error_type = getattr(exc, "error_type", "unavailable")
                self._delegate = UnavailableAdapter(str(exc), error_type=error_type)

    def _call(self, method: str, *args, **kwargs) -> Any:
        try:
            return getattr(self._delegate, method)(*args, **kwargs)
        except AdapterUnavailableError:
            self._reconnect_if_due()
            # Retry once against whatever the delegate is now -- either the
            # freshly (re)built real adapter, or the same/a fresher
            # UnavailableAdapter if the rebuild also failed or was skipped
            # (still cooling down).
            return getattr(self._delegate, method)(*args, **kwargs)

    def health_status(self) -> dict[str, Any]:  # type: ignore[override]
        """Unlike every other call on this adapter, /health is meant to be
        polled cheaply and often by an orchestrator -- but it must still
        attempt a reconnect first if one is due. Without this, an
        orchestrator relying purely on /health for readiness (exactly how
        Dockerfile/docker-compose.yml/railway.toml wire it) could report
        "unavailable" forever after a human already fixed the underlying
        problem, simply because no real tool call ever landed to trigger
        the heal.

        Only attempts this when the delegate is already known-broken
        (UnavailableAdapter) -- unlike _call(), which only ever reaches
        _reconnect_if_due() after a real call just failed, this method has
        no such natural signal, so it must check explicitly rather than
        forcing a pointless rebuild attempt against an already-healthy
        delegate on every single passive probe.
        """
        if isinstance(self._delegate, UnavailableAdapter):
            self._reconnect_if_due()
        return self._delegate.health_status()

    def list_vehicles(self) -> list[VehicleListItem]:  # type: ignore[override]
        return self._call("list_vehicles")

    def get_vehicle(self, vehicle_id: str, *args, **kwargs) -> Optional[VehicleModel]:  # type: ignore[override]
        return self._call("get_vehicle", vehicle_id, *args, **kwargs)

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:  # type: ignore[override]
        return self._call("get_energy_status", vehicle_id)

    def shutdown(self) -> None:  # type: ignore[override]
        self._delegate.shutdown()

    def __enter__(self) -> "ReconnectingAdapter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.shutdown()
