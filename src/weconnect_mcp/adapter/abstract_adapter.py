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
    """Charging info for electric/hybrid vehicles"""
    is_charging: Optional[bool] = None
    is_plugged_in: Optional[bool] = None
    charging_power_kw: Optional[float] = None
    charging_state: Optional[str] = None
    remaining_time_minutes: Optional[int] = None
    target_soc_percent: Optional[int] = None
    current_soc_percent: Optional[float] = None
    charge_mode: Optional[str] = None

class VehicleModel(BaseModel):
    vin: Optional[str] # only mandatory field
    model: Optional[str] = None
    name: Optional[str] = None
    license_plate: Optional[str] = None
    odometer: Optional[float] = None
    manufacturer: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    software_version: Optional[str] = None
    model_year: Optional[int] = None
    connection_state: Optional[str] = None

class VehicleListItem(BaseModel):
    """Simplified vehicle info for listing"""
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None

class VehicleDetailLevel(str, Enum):
    """Detail level for vehicle information."""
    BASIC = "basic"      # VIN, name, model, type, manufacturer
    FULL = "full"        # BASIC + state, connection_state, odometer, year, software

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

class AbstractAdapter(ABC):
    """Base adapter interface for vehicle data providers."""

    @abstractmethod
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info with configurable detail level.

        Args:
            vehicle_id: VIN, name, or license plate
            details: BASIC, FULL, or ALL
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
