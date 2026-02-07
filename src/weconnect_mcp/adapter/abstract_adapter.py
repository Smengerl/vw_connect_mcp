"""Adapter that wires the carconnectivity library into the generic MCP server.

Adapters should implement a small surface used by the MCP server. Types
are annotated so the server can rely on concrete return types.
"""

from abc import ABC, abstractmethod
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel
from typing import Optional



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
    position: Optional[PositionModel] = None
    battery: Optional[BatteryModel] = None
    doors: Optional[DoorsModel] = None
    windows: Optional[WindowsModel] = None
    climate: Optional[ClimateModel] = None
    tyres: Optional[TyresModel] = None

class VehicleListItem(BaseModel):
    """Simplified vehicle information for listing"""
    vin: str
    name: Optional[str] = None
    model: Optional[str] = None

class AbstractAdapter(ABC):
    @abstractmethod
    def shutdown(self) -> None:
        """Perform any cleanup required by the adapter."""

    @abstractmethod
    def list_vehicles(self) -> list[VehicleListItem]:
        """Return a list of vehicle dicts. Each dict should include an 'id' key."""
        pass


    @abstractmethod
    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleModel]:
        """Return the vehicle dict for the given vehicle_id.

        If the vehicle is not found, return a dict with an 'error' key.
        """
        pass

    @abstractmethod
    def get_doors_state(self, vehicle_id: str) -> Optional[DoorsModel]:
        """Return the doors state for the given vehicle_id.

        If the vehicle is not found, return None.
        """
        pass

    @abstractmethod
    def get_windows_state(self, vehicle_id: str) -> Optional[WindowsModel]:
        """Return the windows state for the given vehicle_id.

        If the vehicle is not found, return None.
        """
        pass

    @abstractmethod
    def get_tyres_state(self, vehicle_id: str) -> Optional[TyresModel]:
        """Return the tyres state for the given vehicle_id.

        If the vehicle is not found, return None.
        """
        pass

    @abstractmethod
    def get_vehicle_type(self, vehicle_id: str) -> Optional[str]:
        """Return the vehicle type for the given vehicle_id.
        
        Returns the vehicle type as a string, e.g., 'electric', 'combustion', 'hybrid'.
        If the vehicle is not found, return None.
        """
        pass

    @abstractmethod
    def get_charging_state(self, vehicle_id: str) -> Optional[ChargingModel]:
        """Return the charging state for the given vehicle_id.
        
        Returns detailed charging information if the vehicle supports it (BEV/PHEV).
        If the vehicle is not found or doesn't support charging, return None.
        """
        pass
