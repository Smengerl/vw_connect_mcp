"""Stub adapters used when the real (Tibber) adapter isn't in play yet.

Two distinct situations, two distinct stubs -- don't conflate them:

- StartingAdapter: the real backend is still connecting (HTTP/cloud mode
  only, transient). The MCP server starts immediately so cloud
  health-checks pass while login runs in a background thread; during that
  window every tool call gets a safe "nothing yet" response, not an error.
  Once the background thread finishes, the CLI's adapter proxy swaps the
  delegate to the real adapter and sets ``_ready = True``.

- UnavailableAdapter: the real backend could not be constructed at all --
  no cached Tibber tokens, or a refresh that failed with a genuine
  (non-race) rejection, see ARCHITECTURE.md §2.4 -- and won't become
  available without a human re-authorizing and restarting. Used by both
  transports so the MCP server still starts and registers its tools
  instead of the whole process crashing before any client ever connects:
  every call raises AdapterUnavailableError, which read_tools.py's
  _handle_unavailable turns into a clear "server_unavailable" tool
  response.
"""
from __future__ import annotations

from typing import Optional

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, AdapterUnavailableError, EnergyStatusModel, VehicleModel, VehicleListItem,
)


class StartingAdapter(AbstractAdapter):
    """No-op stub used while the real backend is still connecting."""

    _ready: bool = False

    def list_vehicles(self) -> list[VehicleListItem]:  # type: ignore[override]
        return []

    def get_vehicle(self, vehicle_id: str, details=None) -> Optional[VehicleModel]:  # type: ignore[override]
        return None

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:  # type: ignore[override]
        return None

    def shutdown(self) -> None:  # type: ignore[override]
        pass


class UnavailableAdapter(AbstractAdapter):
    """Stub used when the real backend could not be constructed at all and
    won't recover without a human re-authorizing (see module docstring).
    Every method raises AdapterUnavailableError with the original
    remediation message.
    """

    def __init__(self, message: str) -> None:
        self._message = message

    def list_vehicles(self) -> list[VehicleListItem]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message)

    def get_vehicle(self, vehicle_id: str, details=None) -> Optional[VehicleModel]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message)

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:  # type: ignore[override]
        raise AdapterUnavailableError(self._message)

    def shutdown(self) -> None:  # type: ignore[override]
        pass

    def __enter__(self) -> "UnavailableAdapter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.shutdown()
