"""Adapter that wires the carconnectivity library into the generic MCP server.

Adapters should implement a small surface used by the MCP server. Types
are annotated so the server can rely on concrete return types.
"""

from abc import ABC, abstractmethod
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum



class PositionModel(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    heading: Optional[float]

class BatteryModel(BaseModel):
    soc: Optional[float]
    range_km: Optional[float]
    charging: Optional[bool]
    plugged_in: Optional[bool]
    charging_power: Optional[float]

class ChargingModel(BaseModel):
    """Detailed charging information for electric/hybrid vehicles"""
    is_charging: Optional[bool] = None  # True if currently charging
    is_plugged_in: Optional[bool] = None  # True if charging cable is connected
    charging_power_kw: Optional[float] = None  # Current charging power in kW
    charging_state: Optional[str] = None  # e.g., 'charging', 'complete', 'error', 'notReady'
    remaining_time_minutes: Optional[int] = None  # Estimated time to full charge in minutes
    target_soc_percent: Optional[int] = None  # Target state of charge percentage
    current_soc_percent: Optional[float] = None  # Current state of charge percentage
    charge_mode: Optional[str] = None  # e.g., 'manual', 'timer', 'preferredTime'

class ClimatizationModel(BaseModel):
    """Climate control and heating information"""
    state: Optional[str] = None  # Current state: 'off', 'heating', 'cooling', 'ventilation'
    is_active: Optional[bool] = None  # True if climatization is currently active
    target_temperature_celsius: Optional[float] = None  # Target temperature in Celsius
    estimated_time_remaining_minutes: Optional[int] = None  # Time until target temperature reached
    window_heating_enabled: Optional[bool] = None  # Is window heating enabled
    seat_heating_enabled: Optional[bool] = None  # Is seat heating enabled
    climatization_at_unlock_enabled: Optional[bool] = None  # Start climatization when unlocking
    using_external_power: Optional[bool] = None  # Is using external power (not battery)

class MaintenanceModel(BaseModel):
    """Vehicle maintenance and service information"""
    inspection_due_date: Optional[str] = None  # Next inspection due date (ISO format)
    inspection_due_distance_km: Optional[int] = None  # Remaining km until inspection
    oil_service_due_date: Optional[str] = None  # Next oil service due date (ISO format)
    oil_service_due_distance_km: Optional[int] = None  # Remaining km until oil service

class DriveModel(BaseModel):
    """Individual drive system (electric or combustion)"""
    range_km: Optional[float] = None  # Remaining range in kilometers
    battery_level_percent: Optional[float] = None  # Battery level (for electric)
    tank_level_percent: Optional[float] = None  # Tank level (for combustion)

class RangeModel(BaseModel):
    """Vehicle range and energy information"""
    total_range_km: Optional[float] = None  # Total remaining range
    electric_drive: Optional[DriveModel] = None  # Electric drive info (BEV/PHEV)
    combustion_drive: Optional[DriveModel] = None  # Combustion drive info (PHEV/Combustion)

class WindowHeatingModel(BaseModel):
    """Individual window heating status"""
    state: Optional[str] = None  # 'on' or 'off'

class WindowHeatingsModel(BaseModel):
    """Window heating information for all windows"""
    front: Optional[WindowHeatingModel] = None  # Front window heating
    rear: Optional[WindowHeatingModel] = None  # Rear window heating

class LightModel(BaseModel):
    """Individual light status"""
    state: Optional[str] = None  # 'on' or 'off'

class LightsModel(BaseModel):
    """Vehicle lights status"""
    left: Optional[LightModel] = None  # Left light
    right: Optional[LightModel] = None  # Right light

class BatteryStatusModel(BaseModel):
    """Simplified battery and range information for quick access"""
    battery_level_percent: Optional[float] = None  # Current battery charge percentage (0-100)
    range_km: Optional[float] = None  # Remaining electric range in kilometers
    is_charging: Optional[bool] = None  # True if currently charging
    charging_power_kw: Optional[float] = None  # Current charging power (only when charging)
    estimated_charge_time_minutes: Optional[int] = None  # Time to full charge (only when charging)

class DoorModel(BaseModel):
    locked: Optional[bool]
    open: Optional[bool]

class DoorsModel(BaseModel):
    lock_state: Optional[bool]=None
    open_state: Optional[bool]=None
    front_left: Optional[DoorModel]=None
    front_right: Optional[DoorModel]=None
    rear_left: Optional[DoorModel]=None
    rear_right: Optional[DoorModel]=None
    trunk: Optional[DoorModel]=None
    bonnet: Optional[DoorModel]=None

class WindowModel(BaseModel):
    open: Optional[bool]

class WindowsModel(BaseModel):
    front_left: Optional[WindowModel]
    front_right: Optional[WindowModel]
    rear_left: Optional[WindowModel]
    rear_right: Optional[WindowModel]

class ClimateModel(BaseModel):
    is_on: Optional[bool]
    target_temperature: Optional[float]
    inside_temperature: Optional[float]
    outside_temperature: Optional[float]

class TyreModel(BaseModel):
    pressure: Optional[float]
    temperature: Optional[float]

class TyresModel(BaseModel):
    front_left: Optional[TyreModel]
    front_right: Optional[TyreModel]
    rear_left: Optional[TyreModel]
    rear_right: Optional[TyreModel]

class VehicleModel(BaseModel):
    vin: Optional[str] # only mandatory field
    model: Optional[str] = None
    name: Optional[str] = None
    odometer: Optional[float] = None
    manufacturer: Optional[str] = None
    state: Optional[str] = None
    type: Optional[str] = None
    software_version: Optional[str] = None
    model_year: Optional[int] = None
    connection_state: Optional[str] = None
    battery: Optional[BatteryModel] = None
    climate: Optional[ClimateModel] = None

class VehicleListItem(BaseModel):
    """Simplified vehicle information for listing"""
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None

# New models for consolidated tools

class VehicleDetailLevel(str, Enum):
    """Detail level for vehicle information."""
    BASIC = "basic"      # VIN, name, model, type, manufacturer
    FULL = "full"        # BASIC + state, connection_state, odometer, year, software
    ALL = "all"          # Everything (reserved for future expansion)

class PhysicalStatusModel(BaseModel):
    """Consolidated physical component status."""
    doors: Optional[DoorsModel] = None
    windows: Optional[WindowsModel] = None
    tyres: Optional[TyresModel] = None
    lights: Optional[LightsModel] = None

class RangeInfo(BaseModel):
    """Consolidated range information."""
    total_km: Optional[float] = None
    electric_km: Optional[float] = None  # BEV/PHEV only
    combustion_km: Optional[float] = None  # PHEV/Combustion only

class ElectricDriveInfo(BaseModel):
    """Electric drive information."""
    battery_level_percent: Optional[float] = None
    charging: Optional[ChargingModel] = None

class CombustionDriveInfo(BaseModel):
    """Combustion drive information."""
    tank_level_percent: Optional[float] = None
    fuel_type: Optional[str] = None

class EnergyStatusModel(BaseModel):
    """Consolidated energy and range information."""
    vehicle_type: str  # electric, hybrid, combustion
    range: RangeInfo
    electric: Optional[ElectricDriveInfo] = None  # BEV/PHEV only
    combustion: Optional[CombustionDriveInfo] = None  # PHEV/Combustion only

class ClimateStatusModel(BaseModel):
    """Consolidated climate control information."""
    climatization: Optional[ClimatizationModel] = None
    window_heating: Optional[WindowHeatingsModel] = None

class AbstractAdapter(ABC):
    """Base adapter interface for vehicle data providers."""
    
    # New consolidated methods (optimized tool structure)
    
    @abstractmethod
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle information with configurable detail level.
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            details: Detail level (BASIC, FULL, or ALL)
            
        Returns:
            Vehicle information with requested detail level, or None if not found
        """
        pass
    
    @abstractmethod
    def get_physical_status(self, vehicle_id: str, components: Optional[List[str]] = None) -> Optional[PhysicalStatusModel]:
        """Get physical component status (doors, windows, tyres, lights).
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            components: Optional list to filter components (e.g., ["doors", "windows"])
                       If None, returns all available components
        
        Returns:
            Physical status with requested components, or None if vehicle not found
        """
        pass
    
    @abstractmethod
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get consolidated energy and range information.
        
        Combines battery status, charging state, and range info into a single,
        vehicle-type-aware response.
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            
        Returns:
            Energy status appropriate for vehicle type, or None if not found
        """
        pass
    
    @abstractmethod
    def get_climate_status(self, vehicle_id: str) -> Optional[ClimateStatusModel]:
        """Get climate control status (climatization + window heating).
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            
        Returns:
            Climate status, or None if vehicle not found
        """
        pass
    
    # Infrastructure methods
    
    @abstractmethod
    def shutdown(self) -> None:
        """Perform any cleanup required by the adapter."""

    @abstractmethod
    def list_vehicles(self) -> list[VehicleListItem]:
        """Return a list of vehicle dicts. Each dict should include an 'id' key."""
        pass

    def resolve_vehicle_id(self, identifier: str) -> Optional[str]:
        """
        Resolve a vehicle identifier (name, VIN, or license plate) to a VIN.
        
        Search priority:
        1. Name (case-insensitive, partial match)
        2. VIN (exact match)
        3. License plate (case-insensitive, exact match)
        
        Args:
            identifier: Vehicle name, VIN, or license plate
            
        Returns:
            VIN of the matched vehicle, or None if not found
        """
        vehicles = self.list_vehicles()
        identifier_lower = identifier.lower().strip()
        
        # Priority 1: Search by name (case-insensitive, partial match)
        for vehicle in vehicles:
            if vehicle.name and identifier_lower in vehicle.name.lower():
                return vehicle.vin
        
        # Priority 2: Search by VIN (exact match)
        for vehicle in vehicles:
            if vehicle.vin.lower() == identifier_lower:
                return vehicle.vin
        
        # Priority 3: Search by license plate (case-insensitive, exact match)
        for vehicle in vehicles:
            if vehicle.license_plate and vehicle.license_plate.lower() == identifier_lower:
                return vehicle.vin
        
        return None

    @abstractmethod
    def get_maintenance_info(self, vehicle_id: str) -> Optional[MaintenanceModel]:
        """Return the maintenance information for the given vehicle_id.
        
        Returns inspection and service due dates/distances.
        If the vehicle is not found, return None.
        """
        pass

    @abstractmethod
    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """Return the current position for the given vehicle_id.
        
        Returns GPS coordinates (latitude, longitude) and heading.
        If the vehicle is not found or position is unavailable, return None.
        """
        pass
