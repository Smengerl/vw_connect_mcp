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
from typing import Optional
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
    """Simplified vehicle info for listing"""
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None

class VehicleDetailLevel(str, Enum):
    """Detail level for vehicle information."""
    BASIC = "basic"      # VIN, name, model, manufacturer
    FULL = "full"        # BASIC + connection_state + last_seen (costs an extra Tibber API call)

class RangeInfo(BaseModel):
    """Consolidated range info"""
    total_km: Optional[float] = None
    electric_km: Optional[float] = None  # BEV/PHEV
    combustion_km: Optional[float] = None  # PHEV/Combustion

class ElectricDriveInfo(BaseModel):
    """Electric drive info"""
    battery_level_percent: Optional[float] = None
    battery_temperature_kelvin: Optional[float] = None
    charging: Optional[ChargingModel] = None

class CombustionDriveInfo(BaseModel):
    """Combustion drive info"""
    tank_level_percent: Optional[float] = None
    fuel_type: Optional[str] = None
    adblue_range_km: Optional[float] = None  # Diesel only
    adblue_level_percent: Optional[float] = None  # Diesel only

class EnergyStatusModel(BaseModel):
    """Consolidated energy and range info"""
    vehicle_type: str  # electric, hybrid, combustion
    range: RangeInfo
    electric: Optional[ElectricDriveInfo] = None  # BEV/PHEV
    combustion: Optional[CombustionDriveInfo] = None  # PHEV/Combustion
    last_seen: Optional[str] = None  # ISO 8601; Tibber's status.lastSeen

class AdapterUnavailableError(RuntimeError):
    """Raised when the adapter cannot serve any data right now, and fixing
    it needs an operator to take a step outside a single request (e.g.
    re-authorizing a backend whose credentials expired) -- unlike a single
    vehicle_id not being found, which is a normal per-request outcome, not
    an adapter-wide failure.

    Concrete adapters raise this (or a backend-specific subclass) so the
    MCP tool layer can report "server unavailable" without needing to know
    which backend-specific failure caused it.
    """


class AbstractAdapter(ABC):
    """Base adapter interface for vehicle data providers."""

    @abstractmethod
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info with configurable detail level.

        Args:
            vehicle_id: VIN, name, or license plate
            details: BASIC or FULL
        """
        pass

    @abstractmethod
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info (vehicle-type-aware).

        Args:
            vehicle_id: VIN, name, or license plate
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanup resources."""

    @abstractmethod
    def list_vehicles(self) -> list[VehicleListItem]:
        """Return list of vehicles with VIN, name, model, license plate."""
        pass

    def resolve_vehicle_id(self, identifier: str) -> Optional[str]:
        """Resolve identifier (name, VIN, license plate) to VIN.

        Search priority: 1) Name (partial), 2) VIN (exact), 3) License plate (exact)
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

        # Priority 3: License plate (exact)
        for vehicle in vehicles:
            if vehicle.license_plate and vehicle.license_plate.lower() == identifier_lower:
                return vehicle.vin

        return None
