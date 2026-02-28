"""No-op stub adapter used while the real VW adapter is still connecting.

In HTTP/cloud mode the MCP server starts immediately so that cloud
health-checks pass, while the actual VW OAuth login runs in a background
thread.  During that warm-up window every tool call is routed through this
stub, which returns safe "not ready yet" responses instead of crashing.

Once the background thread finishes, :class:`AdapterProxy` swaps the delegate
to the real :class:`CarConnectivityAdapter` and sets ``_ready = True``.
"""
from __future__ import annotations

from typing import Optional

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter

_NOT_READY: dict = {
    "success": False,
    "error": "Server is still starting – please retry in a few seconds",
}


class StartingAdapter(AbstractAdapter):
    """No-op stub used while VW OAuth login is in progress."""

    _ready: bool = False

    # ── read methods ─────────────────────────────────────────────────────────

    def list_vehicles(self):  # type: ignore[override]
        return []

    def get_vehicle(self, vehicle_id: str):  # type: ignore[override]
        return None

    def get_physical_status(self, vehicle_id: str):  # type: ignore[override]
        return None

    def get_climate_status(self, vehicle_id: str):  # type: ignore[override]
        return None

    def get_energy_status(self, vehicle_id: str):  # type: ignore[override]
        return None

    def get_position(self, vehicle_id: str):  # type: ignore[override]
        return None

    def get_maintenance_info(self, vehicle_id: str):  # type: ignore[override]
        return None

    def shutdown(self):  # type: ignore[override]
        pass

    # ── command methods ───────────────────────────────────────────────────────

    def lock_vehicle(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def unlock_vehicle(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def start_climatization(self, vehicle_id: str, target_temp_celsius: Optional[float] = None):  # type: ignore[override]
        return _NOT_READY

    def stop_climatization(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def start_charging(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def stop_charging(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def start_window_heating(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def stop_window_heating(self, vehicle_id: str):  # type: ignore[override]
        return _NOT_READY

    def flash_lights(self, vehicle_id: str, duration_seconds: Optional[int] = None):  # type: ignore[override]
        return _NOT_READY

    def honk_and_flash(self, vehicle_id: str, duration_seconds: Optional[int] = None):  # type: ignore[override]
        return _NOT_READY
