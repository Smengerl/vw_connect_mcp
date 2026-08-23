"""No-op stub adapter used while the real adapter is still connecting.

In HTTP/cloud mode the MCP server starts immediately so that cloud
health-checks pass, while the actual backend connect/login runs in a
background thread.  During that warm-up window every tool call is routed
through this stub, which returns safe "not ready yet" responses instead of
crashing.

Once the background thread finishes, the CLI's adapter proxy swaps the
delegate to the real (Tibber) adapter and sets ``_ready = True``.
"""
from __future__ import annotations

from typing import Optional

from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, EnergyStatusModel, VehicleModel, VehicleListItem


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
