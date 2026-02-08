"""Abstract adapter interface for vehicle data providers.

Adapters implement a small surface for the MCP server with concrete types.
"""

from abc import ABC, abstractmethod
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
    """Charging info for electric/hybrid vehicles"""
    is_charging: Optional[bool] = None
    is_plugged_in: Optional[bool] = None
    charging_power_kw: Optional[float] = None
    charging_state: Optional[str] = None
    remaining_time_minutes: Optional[int] = None
    target_soc_percent: Optional[int] = None
    current_soc_percent: Optional[float] = None
    charge_mode: Optional[str] = None

class ClimatizationModel(BaseModel):
    """Climate control and heating"""
    state: Optional[str] = None
    is_active: Optional[bool] = None
    target_temperature_celsius: Optional[float] = None
    estimated_time_remaining_minutes: Optional[int] = None
    window_heating_enabled: Optional[bool] = None
    seat_heating_enabled: Optional[bool] = None
    climatization_at_unlock_enabled: Optional[bool] = None
    using_external_power: Optional[bool] = None

class MaintenanceModel(BaseModel):
    """Maintenance and service info"""
    inspection_due_date: Optional[str] = None
    inspection_due_distance_km: Optional[int] = None
    oil_service_due_date: Optional[str] = None
    oil_service_due_distance_km: Optional[int] = None

class DriveModel(BaseModel):
    """Individual drive system (electric or combustion)"""
    range_km: Optional[float] = None
    battery_level_percent: Optional[float] = None  # electric only
    tank_level_percent: Optional[float] = None  # combustion only
    battery_temperature_kelvin: Optional[float] = None  # electric only
    adblue_range_km: Optional[float] = None  # diesel only
    adblue_level_percent: Optional[float] = None  # diesel only

class RangeModel(BaseModel):
    """Range and energy info"""
    total_range_km: Optional[float] = None
    electric_drive: Optional[DriveModel] = None  # BEV/PHEV
    combustion_drive: Optional[DriveModel] = None  # PHEV/Combustion

class WindowHeatingModel(BaseModel):
    """Individual window heating status"""
    state: Optional[str] = None

class WindowHeatingsModel(BaseModel):
    """Window heating for all windows"""
    front: Optional[WindowHeatingModel] = None
    rear: Optional[WindowHeatingModel] = None

class LightModel(BaseModel):
    """Individual light status"""
    state: Optional[str] = None

class LightsModel(BaseModel):
    """Vehicle lights status"""
    left: Optional[LightModel] = None
    right: Optional[LightModel] = None

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
    license_plate: Optional[str] = None
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
    """Simplified vehicle info for listing"""
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None
    license_plate: Optional[str] = None

class VehicleDetailLevel(str, Enum):
    """Detail level for vehicle information."""
    BASIC = "basic"      # VIN, name, model, type, manufacturer
    FULL = "full"        # BASIC + state, connection_state, odometer, year, software
    ALL = "all"          # Everything

class PhysicalStatusModel(BaseModel):
    """Consolidated physical component status"""
    doors: Optional[DoorsModel] = None
    windows: Optional[WindowsModel] = None
    tyres: Optional[TyresModel] = None
    lights: Optional[LightsModel] = None

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

class ClimateStatusModel(BaseModel):
    """Consolidated climate control info"""
    climatization: Optional[ClimatizationModel] = None
    window_heating: Optional[WindowHeatingsModel] = None

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
    def get_physical_status(self, vehicle_id: str, components: Optional[List[str]] = None) -> Optional[PhysicalStatusModel]:
        """Get physical components: doors, windows, tyres, lights.
        
        Args:
            vehicle_id: VIN, name, or license plate
            components: Filter e.g., ["doors", "windows"] or None for all
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
    def get_climate_status(self, vehicle_id: str) -> Optional[ClimateStatusModel]:
        """Get climate control: climatization + window heating.
        
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

    @abstractmethod
    def get_maintenance_info(self, vehicle_id: str) -> Optional[MaintenanceModel]:
        """Get maintenance: inspection and service schedules."""
        pass

    @abstractmethod
    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """Get GPS position: latitude, longitude, heading."""
        pass

    @abstractmethod
    def lock_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Lock the vehicle doors."""
        pass

    @abstractmethod
    def unlock_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Unlock the vehicle doors."""
        pass

    @abstractmethod
    def start_climatization(self, vehicle_id: str, target_temp_celsius: Optional[float] = None) -> Dict[str, Any]:
        """Start climate control.
        
        Args:
            vehicle_id: VIN, name, or license plate
            target_temp_celsius: Optional target temperature in Celsius (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        pass

    @abstractmethod
    def stop_climatization(self, vehicle_id: str) -> Dict[str, Any]:
        """Stop climate control."""
        pass

    @abstractmethod
    def start_charging(self, vehicle_id: str) -> Dict[str, Any]:
        """Start charging."""
        pass

    @abstractmethod
    def stop_charging(self, vehicle_id: str) -> Dict[str, Any]:
        """Stop charging."""
        pass

    @abstractmethod
    def flash_lights(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Flash the vehicle lights.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
        """
        pass

    @abstractmethod
    def honk_and_flash(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Honk and flash the vehicle.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
        """
        pass

    @abstractmethod
    def start_window_heating(self, vehicle_id: str) -> Dict[str, Any]:
        """Start window heating."""
        pass

    @abstractmethod
    def stop_window_heating(self, vehicle_id: str) -> Dict[str, Any]:
        """Stop window heating."""
        pass

    def invalidate_cache(self) -> None:
        """Invalidate cached data to force fresh fetch on next access.
        
        Should be called after state-changing operations (commands) to ensure
        subsequent reads get updated data reflecting the new state.
        
        Default implementation does nothing (for adapters without caching).
        """
        pass
