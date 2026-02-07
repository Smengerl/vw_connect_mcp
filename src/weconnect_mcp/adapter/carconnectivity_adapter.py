"""Adapter that wires the carconnectivity library into the generic MCP server.

This file depends on the third-party `carconnectivity` library; its responsibilities are:
- initialize CarConnectivity 
- provide a vehicles_getter callable returning the list of vehicles
"""

import json
import os
import sys
import logging
from typing import List, Any, Optional
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleModel, VehicleListItem, ChargingModel, PositionModel, DoorsModel, DoorModel, WindowsModel, WindowModel, TyreModel, TyresModel
from carconnectivity.vehicle import GenericVehicle, Length, ElectricVehicle, CombustionVehicle
from carconnectivity.doors import Doors
from carconnectivity.windows import Windows
from carconnectivity.attributes import GenericAttribute


# Configure logging to use stderr to avoid interfering with MCP stdio communication
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

from pydantic import BaseModel


class CarConnectivityAdapter(AbstractAdapter):

    def __init__(self, config_path: str, tokenstore_file: Optional[str] = None):
        self.tokenstore_file = tokenstore_file
        self.config_path = config_path
        self.vehicles: List[Any] = []
        self.car_connectivity = None
        # import the heavy third-party library lazily so tests (TEST_MODE)
        # don't require it to be installed when we only run with fake data
        try:
            from carconnectivity import carconnectivity as _carconnectivity
        except Exception:
            # re-raise so the caller gets the original import error
            raise
        with open(config_path, 'r', encoding='utf-8') as fh:
            config_dict = json.load(fh)
        self.car_connectivity = _carconnectivity.CarConnectivity(config=config_dict, tokenstore_file=tokenstore_file)
        self.car_connectivity.fetch_all()

    def shutdown(self):
        if self.car_connectivity is not None:
            try:
                self.car_connectivity.shutdown()
            except Exception:
                pass

    async def __aenter__(self) -> CarConnectivityAdapter:
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def __enter__(self) -> CarConnectivityAdapter:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    # vehicles getter used by the generic server
    def list_vehicles(self) -> list[VehicleListItem]:
        if self.car_connectivity is None:
            return []
        garage = self.car_connectivity.get_garage() if self.car_connectivity else None
        if garage is None or not hasattr(garage, "list_vehicle_vins"):
            return []
        
        vehicle_list = []
        for vin in garage.list_vehicle_vins():
            vehicle = garage.get_vehicle(vin)
            if vehicle:
                name_val = vehicle.name.value if vehicle.name is not None else None
                model_val = vehicle.model.value if vehicle.model is not None else None
                vehicle_list.append(VehicleListItem(
                    vin=vin,
                    name=name_val,
                    model=model_val
                ))
            else:
                # Fallback if vehicle can't be retrieved
                vehicle_list.append(VehicleListItem(vin=vin))
        
        return vehicle_list


    def _get_vehicle_for_vin(self, vehicle_id: str) -> Optional[GenericVehicle]:
        if self.car_connectivity is None:
            return None
        garage = self.car_connectivity.get_garage() if self.car_connectivity else None
        if garage is None or not hasattr(garage, "get_vehicle"):
            return None
        vehicle = garage.get_vehicle(vehicle_id)
        return vehicle


    def _get_doors_state(self, vehicle: GenericVehicle) -> Optional[DoorsModel]:
        doors = vehicle.doors
        if doors is None:
            return None
        
        lock_state = None
        if doors.lock_state is not None:
            if doors.lock_state.value == Doors.LockState.LOCKED:
                lock_state = True
            elif doors.lock_state.value == Doors.LockState.UNLOCKED:
                lock_state = False
        open_state = None
        if doors.open_state is not None:
            if doors.open_state.value == Doors.OpenState.OPEN:
                open_state = True
            elif doors.open_state.value == Doors.OpenState.CLOSED:
                open_state = False

        if doors.doors:
            door_models = {}
            for door_id, door in doors.doors.items():
                door_locked = None
                if door.lock_state is not None:
                    if door.lock_state.value == Doors.LockState.LOCKED:
                        door_locked = True
                    elif door.lock_state.value == Doors.LockState.UNLOCKED:
                        door_locked = False

                door_open = None
                if door.open_state is not None:
                    if door.open_state.value == Doors.OpenState.CLOSED:
                        door_open = False
                    elif door.open_state.value == Doors.OpenState.OPEN:
                        door_open = True
                door_models[door_id] = DoorModel(
                    locked=door_locked,
                    open=door_open,
                )
            return DoorsModel(
                lock_state=lock_state,
                open_state=open_state,
                front_left=door_models.get('frontLeft'),
                front_right=door_models.get('frontRight'),
                rear_left=door_models.get('rearLeft'),
                rear_right=door_models.get('rearRight'),
                trunk=door_models.get('trunk'),
                bonnet=door_models.get('bonnet'),
            )
        else:
            return DoorsModel(
                lock_state=lock_state,
                open_state=open_state
            )



    def _get_windows_state(self, vehicle: GenericVehicle) -> Optional[WindowsModel]:
        windows = vehicle.windows
        if windows is None:
            return None
        
        if windows.windows:
            window_models = {}
            for window_id, window in windows.windows.items():
                window_open = None
                if window.open_state is not None:
                    if window.open_state.value == Windows.OpenState.OPEN:
                        window_open = True
                    elif window.open_state.value == Windows.OpenState.CLOSED:
                        window_open = False
                window_models[window_id] = WindowModel(
                    open=window_open,
                )
            return WindowsModel(
                front_left=window_models.get('frontLeft'),
                front_right=window_models.get('frontRight'),
                rear_left=window_models.get('rearLeft'),
                rear_right=window_models.get('rearRight'),
            )
        return None


    def _get_tyres_state(self, vehicle: GenericVehicle) -> Optional[TyresModel]:
        tyres = getattr(vehicle, 'tyres', None)
        if tyres is None or not hasattr(tyres, 'tyres'):
            return None
        tyre_models = {}
        for tyre_id, tyre in getattr(tyres, 'tyres', {}).items():
            pressure = getattr(tyre, 'pressure', None)
            pressure_val = pressure.value if pressure is not None else None
            temperature = getattr(tyre, 'temperature', None)
            temperature_val = temperature.value if temperature is not None else None
            tyre_models[tyre_id] = TyreModel(
                pressure=pressure_val,
                temperature=temperature_val,
            )
        return TyresModel(
            front_left=tyre_models.get('frontLeft'),
            front_right=tyre_models.get('frontRight'),
            rear_left=tyre_models.get('rearLeft'),
            rear_right=tyre_models.get('rearRight'),
        )



    def _get_charging_state(self, vehicle: GenericVehicle) -> Optional[ChargingModel]:
        
        # Only electric and hybrid vehicles have charging capability
        if not isinstance(vehicle, ElectricVehicle):
            return None
        
        charging = getattr(vehicle, 'charging', None)
        if charging is None:
            return None
        
        # Extract charging state
        is_charging = None
        charging_state_str = None
        if charging.state is not None and charging.state.value is not None:
            from carconnectivity.charging import Charging
            if charging.state.value == Charging.ChargingState.CHARGING:
                is_charging = True
                charging_state_str = 'charging'
            elif charging.state.value == Charging.ChargingState.READY_FOR_CHARGING:
                is_charging = False
                charging_state_str = 'ready'
            elif charging.state.value == Charging.ChargingState.OFF:
                is_charging = False
                charging_state_str = 'off'
            elif charging.state.value == Charging.ChargingState.ERROR:
                is_charging = False
                charging_state_str = 'error'
            else:
                charging_state_str = str(charging.state.value.value) if hasattr(charging.state.value, 'value') else str(charging.state.value)
        
        # Check if plugged in via connector
        is_plugged_in = None
        connector = getattr(charging, 'connector', None)
        if connector is not None:
            connection_state = getattr(connector, 'connection_state', None)
            if connection_state is not None and connection_state.value is not None:
                from carconnectivity.charging_connector import ChargingConnector
                if connection_state.value == ChargingConnector.ChargingConnectorConnectionState.CONNECTED:
                    is_plugged_in = True
                elif connection_state.value == ChargingConnector.ChargingConnectorConnectionState.DISCONNECTED:
                    is_plugged_in = False
        
        # Get charging power
        charging_power_kw = None
        if charging.power is not None and charging.power.value is not None:
            charging_power_kw = float(charging.power.value)
        
        # Get estimated completion time
        remaining_time_minutes = None
        if charging.estimated_date_reached is not None and charging.estimated_date_reached.value is not None:
            from datetime import datetime, timezone
            try:
                estimated_date = charging.estimated_date_reached.value
                now = datetime.now(timezone.utc)
                if estimated_date > now:
                    time_diff = estimated_date - now
                    remaining_time_minutes = int(time_diff.total_seconds() / 60)
            except Exception:
                pass
        
        # Get target SOC and current SOC
        target_soc_percent = None
        settings = getattr(charging, 'settings', None)
        if settings is not None:
            target_level = getattr(settings, 'target_level', None)
            if target_level is not None and target_level.value is not None:
                target_soc_percent = int(target_level.value)
        
        current_soc_percent = None
        battery = getattr(vehicle, 'battery', None)
        if battery is not None:
            level = getattr(battery, 'level', None)
            if level is not None and level.value is not None:
                current_soc_percent = float(level.value)
        
        # Get charge mode (if available)
        charge_mode = None
        # The charge mode might be in different locations depending on the vehicle
        # This is a simplified implementation
        
        return ChargingModel(
            is_charging=is_charging,
            is_plugged_in=is_plugged_in,
            charging_power_kw=charging_power_kw,
            charging_state=charging_state_str,
            remaining_time_minutes=remaining_time_minutes,
            target_soc_percent=target_soc_percent,
            current_soc_percent=current_soc_percent,
            charge_mode=charge_mode
        )
    




    def get_doors_state(self, vehicle_id: str) -> Optional[DoorsModel]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_doors_state(vehicle)

    def get_windows_state(self, vehicle_id: str) -> Optional[WindowsModel]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_windows_state(vehicle)

    def get_tyres_state(self, vehicle_id: str) -> Optional[TyresModel]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_tyres_state(vehicle)

    def get_vehicle_type(self, vehicle_id: str) -> Optional[str]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        type_val = vehicle.type.value if vehicle.type is not None else None
        return type_val

    def get_charging_state(self, vehicle_id: str) -> Optional[ChargingModel]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_charging_state(vehicle)

    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleModel]:
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None

        doors_val = self._get_doors_state(vehicle)
        windows_val = self._get_windows_state(vehicle)
        tyres_val = self._get_tyres_state(vehicle)

        vin_val = vehicle.vin.value if vehicle.vin is not None else None
        model_val = vehicle.model.value if vehicle.model is not None else None
        name_val = vehicle.name.value if vehicle.name is not None else None
        manufacturer_val = vehicle.manufacturer.value if vehicle.manufacturer is not None else None
        odometer_val = vehicle.odometer.value if vehicle.odometer is not None else None
        state_val = vehicle.state.value if vehicle.state is not None else None
        type_val = vehicle.type.value if vehicle.type is not None else None

        position_val = None
        pos = vehicle.position
        if pos is not None:
            position_val = PositionModel(
                latitude=pos.latitude.value if pos.latitude is not None else None,
                longitude=pos.longitude.value if pos.longitude is not None else None,
                heading=pos.heading.value if pos.heading is not None else None,
            )

        return VehicleModel(
            vin=vin_val,
            model=model_val,
            name=name_val,
            manufacturer=manufacturer_val,
            odometer=odometer_val,
            state=state_val,
            type=type_val,
            position=position_val,
            doors=doors_val,
            windows=windows_val,
            tyres=tyres_val,
        )
    