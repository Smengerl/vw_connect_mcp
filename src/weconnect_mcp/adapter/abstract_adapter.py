"""Abstract adapter interface for vehicle data providers.

Adapters implement a small surface for the MCP server with concrete types.

This interface was slimmed down when the carconnectivity (VW-direct)
backend was removed from main (see the permanent `carconnectivity` branch
for that adapter and its richer surface: doors, windows, tyres, lights,
climatization, window heating, GPS position, maintenance, and all vehicle
commands). Tibber's read-only Data API never supported any of that, so
those methods/models were dropped rather than kept as permanent
always-None/not-supported stubs.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class ChargingModel(BaseModel):
    """Charging info for electric/hybrid vehicles.

    charging_power_kw, remaining_time_minutes, and charge_mode were removed
    entirely (not just left None) -- Tibber's Data API never reports them
    for any backend/vehicle, confirmed via its OpenAPI schema (see
    ARCHITECTURE.md §3.1). Keeping always-empty fields in the response
    schema would just be noise for a client to parse around.
    """
    is_charging: Optional[bool] = None
    is_plugged_in: Optional[bool] = None
    charging_state: Optional[str] = None
    target_soc_percent: Optional[int] = None
    current_soc_percent: Optional[float] = None

class VehicleModel(BaseModel):
    """Basic vehicle identity.

    license_plate, odometer, state, type, software_version, and model_year
    were removed entirely (not just left None) -- Tibber's Data API never
    reports any of them, confirmed via its OpenAPI schema (see
    ARCHITECTURE.md §3.1/§5). Keeping always-empty fields in the response
    schema would just be noise for a client to parse around.
    """
    vin: Optional[str] # only mandatory field
    model: Optional[str] = None
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    connection_state: Optional[str] = None
    last_seen: Optional[str] = None  # ISO 8601; Tibber's status.lastSeen, same call as connection_state

class VehicleListItem(BaseModel):
    """Simplified vehicle info for listing.

    No ``license_plate`` field -- same reasoning as VehicleModel's
    docstring above: Tibber's Data API never reports it (confirmed via its
    OpenAPI schema), so it was removed entirely rather than kept as a
    permanently-``None`` field. This used to be the one exception to that
    rule (kept so identifier resolution could accept a license plate as
    input), but with the field always ``None`` for the only backend this
    project has, that input path could never actually match anything
    either -- removed along with it, see AbstractAdapter.resolve_vehicle_id.
    """
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None

class VehicleDetailLevel(str, Enum):
    """Detail level for vehicle information."""
    BASIC = "basic"      # VIN, name, model, manufacturer
    FULL = "full"        # BASIC + connection_state + last_seen (costs an extra Tibber API call)

class RangeInfo(BaseModel):
    """Range info.

    A single ``total_km`` field, not a electric/combustion split -- Tibber's
    vehicle integration is EV-only (confirmed live, ARCHITECTURE.md), so a
    combustion range can never be populated by the only backend this
    project has (or will have, per CLAUDE.md: no dual-backend plans). A
    previous version modeled electric_km/combustion_km separately for a
    hypothetical PHEV/combustion vehicle that could never actually occur
    here; that distinction was removed as dead weight rather than kept
    always-empty.
    """
    total_km: Optional[float] = None

class ElectricDriveInfo(BaseModel):
    """Electric drive info"""
    battery_level_percent: Optional[float] = None
    battery_temperature_kelvin: Optional[float] = None
    charging: Optional[ChargingModel] = None

class EnergyStatusModel(BaseModel):
    """Consolidated energy and range info.

    No ``vehicle_type``/combustion fields -- see RangeInfo's docstring for
    why: this project's only backend (Tibber) never reports anything but
    electric vehicles, so there is nothing to discriminate between.
    """
    range: RangeInfo
    electric: Optional[ElectricDriveInfo] = None
    last_seen: Optional[str] = None  # ISO 8601; Tibber's status.lastSeen

class AdapterUnavailableError(RuntimeError):
    """Raised when the adapter cannot serve any data right now, and fixing
    it needs an operator to take a step outside a single request (e.g.
    re-authorizing a backend whose credentials expired) -- unlike a single
    vehicle_id not being found, which is a normal per-request outcome, not
    an adapter-wide failure.

    Concrete adapters raise this (or a backend-specific subclass) so the
    MCP tool layer can report "server unavailable" without needing to know
    which backend-specific failure caused it. ``error_type`` carries a
    short, stable, machine-readable code (see the Tibber-specific
    TibberAuthError subclasses in tibber_client.py for the concrete codes
    this project produces) so a client -- ultimately the AI assistant on
    the other end of the MCP connection -- can branch on *which* failure
    this is instead of only having the free-text ``message`` to
    pattern-match.
    """

    def __init__(self, message: str, error_type: str = "unavailable") -> None:
        super().__init__(message)
        self.error_type = error_type


class AbstractAdapter(ABC):
    """Base adapter interface for vehicle data providers."""

    @abstractmethod
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info with configurable detail level.

        Args:
            vehicle_id: VIN or name
            details: BASIC or FULL
        """
        pass

    @abstractmethod
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info.

        Args:
            vehicle_id: VIN or name
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup resources."""

    @abstractmethod
    def list_vehicles(self) -> list[VehicleListItem]:
        """Return list of vehicles with VIN, name, model."""
        pass

    def health_status(self) -> dict[str, Any]:
        """Liveness/readiness info for the MCP server's /health endpoint.

        Default: always ready -- a plain working adapter (the real
        TibberAdapter, or a test double) has no "unavailable" state of its
        own to report. UnavailableAdapter and ReconnectingAdapter (see
        starting_adapter.py) override this with their actual state; for
        ReconnectingAdapter this also attempts a reconnect first if one is
        due, so /health participates in the same self-healing every real
        tool call already gets, instead of only reflecting whatever the
        last tool call (or the initial connect attempt) happened to see.

        Shape: ``{"ready": True}`` when healthy, or
        ``{"ready": False, "error_type": ..., "message": ...}`` when not.
        """
        return {"ready": True}

    def resolve_vehicle_id(self, identifier: str) -> Optional[str]:
        """Resolve identifier (name or VIN) to VIN.

        Search priority: 1) Name (partial), 2) VIN (exact)

        There used to be a third priority (license plate, exact) here, but
        VehicleListItem no longer has a license_plate field to match
        against -- Tibber's Data API never reports one, so that input path
        could never actually match anything for this project's only
        backend either. Removed along with the field itself rather than
        left as permanently-dead matching logic.
        """
        vehicles = self.list_vehicles()
        identifier_lower = identifier.lower().strip()

        # Priority 1: Name (case-insensitive, partial)
        for vehicle in vehicles:
            if vehicle.name and identifier_lower in vehicle.name.lower():
                return vehicle.vin

        # Priority 2: VIN (exact)
        for vehicle in vehicles:
            if vehicle.vin.lower() == identifier_lower:
                return vehicle.vin

        return None
