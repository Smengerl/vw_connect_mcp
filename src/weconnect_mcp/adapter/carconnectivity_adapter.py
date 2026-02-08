"""CarConnectivity adapter for VW vehicles via WeConnect.

Depends on third-party carconnectivity library for:
- CarConnectivity initialization
- vehicles_getter callable
"""

import json
import os
import sys
import logging
from typing import List, Any, Optional
from datetime import datetime, timedelta
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, ChargingModel, ClimatizationModel, 
    MaintenanceModel, RangeModel, DriveModel, WindowHeatingsModel, WindowHeatingModel, 
    LightsModel, LightModel, PositionModel, BatteryStatusModel, DoorsModel, DoorModel, 
    WindowsModel, WindowModel, TyreModel, TyresModel,
    VehicleDetailLevel, PhysicalStatusModel, EnergyStatusModel, ClimateStatusModel,
    RangeInfo, ElectricDriveInfo, CombustionDriveInfo
)
from carconnectivity.vehicle import GenericVehicle, Length, ElectricVehicle, CombustionVehicle
from carconnectivity.doors import Doors
from carconnectivity.windows import Windows
from carconnectivity.attributes import GenericAttribute
from carconnectivity.command_impl import (
    LockUnlockCommand,
    ClimatizationStartStopCommand,
    ChargingStartStopCommand,
    HonkAndFlashCommand,
    WindowHeatingStartStopCommand,
)

# Cache duration to avoid VW API rate limits
# Data will be cached for this duration before fetching new data from server
CACHE_DURATION_SECONDS = 300  # in seconds 

# Configure logging to stderr for MCP stdio compatibility
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

from pydantic import BaseModel


class CarConnectivityAdapter(AbstractAdapter):
    """Adapter for VW vehicles using carconnectivity library.
    
    Provides access to VW WeConnect service data via third-party library.
    """

    def __init__(self, config_path: str, tokenstore_file: Optional[str] = None):
        """Initialize adapter.
        
        Args:
            config_path: JSON config file with VW credentials
            tokenstore_file: Optional token storage path
        """
        self.tokenstore_file = tokenstore_file
        self.config_path = config_path
        self.vehicles: List[Any] = []
        self.car_connectivity = None
        
        # Caching to avoid VW API rate limits
        self._last_fetch_time: Optional[datetime] = None
        self._cache_duration = timedelta(seconds=CACHE_DURATION_SECONDS)
        
        try:
            from carconnectivity import carconnectivity as _carconnectivity
        except Exception:
            raise
            
        with open(config_path, 'r', encoding='utf-8') as fh:
            config_dict = json.load(fh)
        self.car_connectivity = _carconnectivity.CarConnectivity(
            config=config_dict, 
            tokenstore_file=tokenstore_file
        )
        self._fetch_data()  # Initial fetch

    def _fetch_data(self) -> None:
        """Fetch data from VW servers and update cache timestamp."""
        if self.car_connectivity is None:
            return
        
        self.car_connectivity.fetch_all()
        self._last_fetch_time = datetime.now()
        logger.info("Fetched fresh data from VW servers")

    def _is_cache_expired(self) -> bool:
        """Check if cached data has expired and needs refresh."""
        if self._last_fetch_time is None:
            return True
        
        time_since_fetch = datetime.now() - self._last_fetch_time
        is_expired = time_since_fetch >= self._cache_duration
        
        if is_expired:
            logger.info(f"Cache expired ({time_since_fetch.total_seconds():.1f}s since last fetch)")
        else:
            logger.debug(f"Using cached data ({time_since_fetch.total_seconds():.1f}s old)")
        
        return is_expired

    def _ensure_fresh_data(self) -> None:
        """Ensure data is fresh, fetching from server if cache expired."""
        if self._is_cache_expired():
            self._fetch_data()

    def invalidate_cache(self) -> None:
        """Invalidate cache to force fresh data fetch on next access.
        
        Should be called after state-changing operations (commands) to ensure
        subsequent reads get updated data reflecting the new state.
        """
        logger.info("Cache invalidated - next data access will fetch fresh data from server")
        self._last_fetch_time = None

    def shutdown(self):
        """Clean up resources."""
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

    def list_vehicles(self) -> list[VehicleListItem]:
        """Get list of vehicles with VIN, name, model, license plate."""
        if self.car_connectivity is None:
            return []
        
        # Ensure we have fresh data before accessing garage
        self._ensure_fresh_data()
            
        garage = self.car_connectivity.get_garage()
        if garage is None or not hasattr(garage, "list_vehicle_vins"):
            return []
        
        vehicle_list = []
        for vin in garage.list_vehicle_vins():
            vehicle = garage.get_vehicle(vin)
            if vehicle:
                name_val = vehicle.name.value if vehicle.name is not None else None
                model_val = vehicle.model.value if vehicle.model is not None else None
                license_plate_val = vehicle.license_plate.value if vehicle.license_plate is not None else None
                vehicle_list.append(VehicleListItem(
                    vin=vin,
                    name=name_val,
                    model=model_val,
                    license_plate=license_plate_val
                ))
            else:
                vehicle_list.append(VehicleListItem(vin=vin))
        
        return vehicle_list
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info with configurable detail level."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None

        vin_val = vehicle.vin.value if vehicle.vin is not None else None
        model_val = vehicle.model.value if vehicle.model is not None else None
        name_val = vehicle.name.value if vehicle.name is not None else None
        license_plate_val = vehicle.license_plate.value if vehicle.license_plate is not None else None
        manufacturer_val = vehicle.manufacturer.value if vehicle.manufacturer is not None else None
        type_val = vehicle.type.value if vehicle.type is not None else None
        
        if details == VehicleDetailLevel.BASIC:
            return VehicleModel(
                vin=vin_val,
                model=model_val,
                name=name_val,
                license_plate=license_plate_val,
                manufacturer=manufacturer_val,
                type=type_val,
            )
        
        # FULL and ALL include additional data
        odometer_val = vehicle.odometer.value if vehicle.odometer is not None else None
        state_val = vehicle.state.value if vehicle.state is not None else None
        software_version_val = vehicle.software.version.value if vehicle.software is not None and vehicle.software.version is not None else None
        model_year_val = vehicle.model_year.value if vehicle.model_year is not None else None
        connection_state_val = vehicle.connection_state.value if vehicle.connection_state is not None else None

        return VehicleModel(
            vin=vin_val,
            model=model_val,
            name=name_val,
            license_plate=license_plate_val,
            manufacturer=manufacturer_val,
            odometer=odometer_val,
            state=state_val,
            type=type_val,
            software_version=software_version_val,
            model_year=model_year_val,
            connection_state=connection_state_val,
        )
    
    def get_physical_status(self, vehicle_id: str, components: Optional[List[str]] = None) -> Optional[PhysicalStatusModel]:
        """Get physical components: doors, windows, tyres, lights."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        include_all = components is None
        include_doors = include_all or "doors" in components
        include_windows = include_all or "windows" in components
        include_tyres = include_all or "tyres" in components
        include_lights = include_all or "lights" in components
        
        return PhysicalStatusModel(
            doors=self._get_doors_state(vehicle) if include_doors else None,
            windows=self._get_windows_state(vehicle) if include_windows else None,
            tyres=self._get_tyres_state(vehicle) if include_tyres else None,
            lights=self._get_lights_state(vehicle) if include_lights else None,
        )
    
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info (vehicle-type-aware)."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        vehicle_type = vehicle.type.value if vehicle.type is not None else "unknown"
        
        range_info = self._get_range_info(vehicle)
        electric_km = None
        combustion_km = None
        if range_info:
            if range_info.electric_drive:
                electric_km = range_info.electric_drive.range_km
            if range_info.combustion_drive:
                combustion_km = range_info.combustion_drive.range_km
        
        range_model = RangeInfo(
            total_km=range_info.total_range_km if range_info else None,
            electric_km=electric_km,
            combustion_km=combustion_km,
        )
        
        # Electric/PHEV
        electric_info = None
        if isinstance(vehicle, ElectricVehicle):
            charging_state = self._get_charging_state(vehicle)
            battery_level = None
            if range_info and range_info.electric_drive:
                battery_level = range_info.electric_drive.battery_level_percent
            
            electric_info = ElectricDriveInfo(
                battery_level_percent=battery_level,
                charging=charging_state,
            )
        
        # Combustion
        combustion_info = None
        if isinstance(vehicle, CombustionVehicle):
            tank_level = None
            fuel_type = None
            if range_info and range_info.combustion_drive:
                tank_level = range_info.combustion_drive.tank_level_percent
            
            combustion_info = CombustionDriveInfo(
                tank_level_percent=tank_level,
                fuel_type=fuel_type,
            )
        
        return EnergyStatusModel(
            vehicle_type=vehicle_type or "unknown",
            range=range_model,
            electric=electric_info,
            combustion=combustion_info,
        )
    
    def get_climate_status(self, vehicle_id: str) -> Optional[ClimateStatusModel]:
        """Get climate control: climatization + window heating."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        return ClimateStatusModel(
            climatization=self._get_climatization_state(vehicle),
            window_heating=self._get_window_heating_state(vehicle),
        )

    def _get_vehicle_for_vin(self, vehicle_id: str) -> Optional[GenericVehicle]:
        """Get vehicle by identifier (VIN, name, or license plate)."""
        if self.car_connectivity is None:
            return None
        
        # Ensure we have fresh data before accessing vehicle
        self._ensure_fresh_data()
            
        garage = self.car_connectivity.get_garage()
        if garage is None or not hasattr(garage, "get_vehicle"):
            return None
        
        vin = self.resolve_vehicle_id(vehicle_id)
        if vin is None:
            vin = vehicle_id
            
        return garage.get_vehicle(vin)

    def _get_doors_state(self, vehicle: GenericVehicle) -> Optional[DoorsModel]:
        """Extract door states from vehicle."""
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
        """Extract window states from vehicle."""
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
        """Extract tyre pressure and temperature."""
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
        """Extract charging info from electric/hybrid vehicle."""
        if not isinstance(vehicle, ElectricVehicle):
            return None
        
        charging = getattr(vehicle, 'charging', None)
        if charging is None:
            return None
        
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
        
        charging_power_kw = None
        if charging.power is not None and charging.power.value is not None:
            charging_power_kw = float(charging.power.value)
        
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
        
        charge_mode = None
        
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
    
    def _get_climatization_state(self, vehicle: GenericVehicle) -> Optional[ClimatizationModel]:
        """Extract climatization state and settings."""
        climatization = getattr(vehicle, 'climatization', None)
        if climatization is None:
            return None
        
        state_str = None
        is_active = None
        if climatization.state is not None and climatization.state.value is not None:
            from carconnectivity.climatization import Climatization
            state_value = climatization.state.value
            if state_value == Climatization.ClimatizationState.OFF:
                state_str = 'off'
                is_active = False
            elif state_value == Climatization.ClimatizationState.HEATING:
                state_str = 'heating'
                is_active = True
            elif state_value == Climatization.ClimatizationState.COOLING:
                state_str = 'cooling'
                is_active = True
            elif state_value == Climatization.ClimatizationState.VENTILATION:
                state_str = 'ventilation'
                is_active = True
            else:
                state_str = str(state_value.value) if hasattr(state_value, 'value') else str(state_value)
                is_active = (state_str != 'off')
        
        target_temperature = None
        window_heating_enabled = None
        seat_heating_enabled = None
        climatization_at_unlock_enabled = None
        using_external_power = None
        
        settings = getattr(climatization, 'settings', None)
        if settings is not None:
            target_temp_attr = getattr(settings, 'target_temperature', None)
            if target_temp_attr is not None and target_temp_attr.value is not None:
                target_temperature = float(target_temp_attr.value)
            
            window_heating_attr = getattr(settings, 'window_heating', None)
            if window_heating_attr is not None and window_heating_attr.value is not None:
                window_heating_enabled = bool(window_heating_attr.value)
            
            seat_heating_attr = getattr(settings, 'seat_heating', None)
            if seat_heating_attr is not None and seat_heating_attr.value is not None:
                seat_heating_enabled = bool(seat_heating_attr.value)
            
            at_unlock_attr = getattr(settings, 'climatization_at_unlock', None)
            if at_unlock_attr is not None and at_unlock_attr.value is not None:
                climatization_at_unlock_enabled = bool(at_unlock_attr.value)
            
            external_power_attr = getattr(settings, 'climatization_without_external_power', None)
            if external_power_attr is not None and external_power_attr.value is not None:
                using_external_power = not bool(external_power_attr.value)
        
        estimated_time_remaining_minutes = None
        estimated_date = getattr(climatization, 'estimated_date_reached', None)
        if estimated_date is not None and estimated_date.value is not None:
            from datetime import datetime, timezone
            try:
                target_date = estimated_date.value
                now = datetime.now(timezone.utc)
                if target_date > now:
                    time_diff = target_date - now
                    estimated_time_remaining_minutes = int(time_diff.total_seconds() / 60)
            except Exception:
                pass
        
        return ClimatizationModel(
            state=state_str,
            is_active=is_active,
            target_temperature_celsius=target_temperature,
            estimated_time_remaining_minutes=estimated_time_remaining_minutes,
            window_heating_enabled=window_heating_enabled,
            seat_heating_enabled=seat_heating_enabled,
            climatization_at_unlock_enabled=climatization_at_unlock_enabled,
            using_external_power=using_external_power
        )

    def _get_maintenance_info(self, vehicle: GenericVehicle) -> Optional[MaintenanceModel]:
        """Extract maintenance schedule."""
        maintenance = getattr(vehicle, 'maintenance', None)
        if maintenance is None:
            return None
        
        inspection_due_date = None
        inspection_due_at = getattr(maintenance, 'inspection_due_at', None)
        if inspection_due_at is not None and inspection_due_at.value is not None:
            try:
                inspection_due_date = inspection_due_at.value.isoformat()
            except Exception:
                inspection_due_date = str(inspection_due_at.value)
        
        inspection_due_distance_km = None
        inspection_due_after = getattr(maintenance, 'inspection_due_after', None)
        if inspection_due_after is not None and inspection_due_after.value is not None:
            try:
                inspection_due_distance_km = int(inspection_due_after.value)
            except Exception:
                pass
        
        oil_service_due_date = None
        oil_service_due_at = getattr(maintenance, 'oil_service_due_at', None)
        if oil_service_due_at is not None and oil_service_due_at.value is not None:
            try:
                oil_service_due_date = oil_service_due_at.value.isoformat()
            except Exception:
                oil_service_due_date = str(oil_service_due_at.value)
        
        oil_service_due_distance_km = None
        oil_service_due_after = getattr(maintenance, 'oil_service_due_after', None)
        if oil_service_due_after is not None and oil_service_due_after.value is not None:
            try:
                oil_service_due_distance_km = int(oil_service_due_after.value)
            except Exception:
                pass
        
        return MaintenanceModel(
            inspection_due_date=inspection_due_date,
            inspection_due_distance_km=inspection_due_distance_km,
            oil_service_due_date=oil_service_due_date,
            oil_service_due_distance_km=oil_service_due_distance_km
        )

    def _get_range_info(self, vehicle: GenericVehicle) -> Optional[RangeModel]:
        """Extract range for electric and/or combustion drives."""
        drives = getattr(vehicle, 'drives', None)
        if drives is None:
            return None
        
        total_range_km = None
        total_range_attr = getattr(drives, 'total_range', None)
        if total_range_attr is not None and total_range_attr.value is not None:
            total_range_km = float(total_range_attr.value)
        
        electric_drive = None
        combustion_drive = None
        
        drives_dict = getattr(drives, 'drives', {})
        
        if 'electric' in drives_dict:
            electric = drives_dict['electric']
            electric_range = None
            battery_level = None
            
            range_attr = getattr(electric, 'range', None)
            if range_attr is not None and range_attr.value is not None:
                electric_range = float(range_attr.value)
            
            battery = getattr(electric, 'battery', None)
            if battery is not None:
                level_attr = getattr(battery, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    battery_level = float(level_attr.value)
            
            electric_drive = DriveModel(
                range_km=electric_range,
                battery_level_percent=battery_level
            )
        
        if 'combustion' in drives_dict:
            combustion = drives_dict['combustion']
            combustion_range = None
            tank_level = None
            
            range_attr = getattr(combustion, 'range', None)
            if range_attr is not None and range_attr.value is not None:
                combustion_range = float(range_attr.value)
            
            tank = getattr(combustion, 'tank', None)
            if tank is not None:
                level_attr = getattr(tank, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    tank_level = float(level_attr.value)
            
            combustion_drive = DriveModel(
                range_km=combustion_range,
                tank_level_percent=tank_level
            )
        
        return RangeModel(
            total_range_km=total_range_km,
            electric_drive=electric_drive,
            combustion_drive=combustion_drive
        )

    def _get_window_heating_state(self, vehicle: GenericVehicle) -> Optional[WindowHeatingsModel]:
        """Extract window heating state."""
        window_heating = getattr(vehicle, 'window_heating', None)
        if window_heating is None:
            return None
        
        front_heating = None
        rear_heating = None
        
        heating_state_attr = getattr(window_heating, 'heating_state', None)
        if heating_state_attr is not None and heating_state_attr.value is not None:
            from carconnectivity.window_heating import WindowHeatings
            pass
        
        window_heatings_dict = getattr(window_heating, 'window_heatings', {})
        
        for location, heating in window_heatings_dict.items():
            state_attr = getattr(heating, 'heating_state', None)
            state_str = None
            
            if state_attr is not None and state_attr.value is not None:
                from carconnectivity.window_heating import WindowHeatings
                if state_attr.value == WindowHeatings.HeatingState.ON:
                    state_str = 'on'
                elif state_attr.value == WindowHeatings.HeatingState.OFF:
                    state_str = 'off'
                else:
                    state_str = str(state_attr.value.value) if hasattr(state_attr.value, 'value') else str(state_attr.value)
            
            if location == 'front':
                front_heating = WindowHeatingModel(state=state_str)
            elif location == 'rear':
                rear_heating = WindowHeatingModel(state=state_str)
        
        return WindowHeatingsModel(
            front=front_heating,
            rear=rear_heating
        )

    def _get_lights_state(self, vehicle: GenericVehicle) -> Optional[LightsModel]:
        """Extract exterior lights state."""
        lights = getattr(vehicle, 'lights', None)
        if lights is None:
            return None
        
        left_light = None
        right_light = None
        
        lights_dict = getattr(lights, 'lights', {})
        
        for light_id, light in lights_dict.items():
            state_attr = getattr(light, 'light_state', None)
            state_str = None
            
            if state_attr is not None and state_attr.value is not None:
                from carconnectivity.lights import Lights
                if state_attr.value == Lights.LightState.ON:
                    state_str = 'on'
                elif state_attr.value == Lights.LightState.OFF:
                    state_str = 'off'
                else:
                    state_str = str(state_attr.value.value) if hasattr(state_attr.value, 'value') else str(state_attr.value)
            
            if light_id == 'left':
                left_light = LightModel(state=state_str)
            elif light_id == 'right':
                right_light = LightModel(state=state_str)
        
        return LightsModel(
            left=left_light,
            right=right_light
        )
    def get_maintenance_info(self, vehicle_id: str) -> Optional[MaintenanceModel]:
        """Get maintenance schedule."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_maintenance_info(vehicle)

    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """Get GPS position."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_position(vehicle)

    def _get_position(self, vehicle: GenericVehicle) -> Optional[PositionModel]:
        """Extract GPS position."""
        pos = vehicle.position
        if pos is None:
            return None
        
        latitude = pos.latitude.value if pos.latitude is not None else None
        longitude = pos.longitude.value if pos.longitude is not None else None
        heading = pos.heading.value if pos.heading is not None else None
        
        if latitude is None and longitude is None:
            return None
        
        return PositionModel(
            latitude=latitude,
            longitude=longitude,
            heading=heading
        )

    def lock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
        """Lock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
            return {"success": False, "error": "Vehicle does not support door commands"}
        
        if not vehicle.doors.commands.contains_command("lock-unlock"):
            return {"success": False, "error": "Vehicle does not support lock/unlock command"}
        
        try:
            vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.LOCK
            self.invalidate_cache()
            logger.info(f"Vehicle {vehicle_id} locked successfully, cache invalidated")
            return {"success": True, "message": "Vehicle locked"}
        except Exception as e:
            logger.error(f"Failed to lock vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def unlock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
        """Unlock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
            return {"success": False, "error": "Vehicle does not support door commands"}
        
        if not vehicle.doors.commands.contains_command("lock-unlock"):
            return {"success": False, "error": "Vehicle does not support lock/unlock command"}
        
        try:
            vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.UNLOCK
            self.invalidate_cache()
            logger.info(f"Vehicle {vehicle_id} unlocked successfully, cache invalidated")
            return {"success": True, "message": "Vehicle unlocked"}
        except Exception as e:
            logger.error(f"Failed to unlock vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_climatization(self, vehicle_id: str, target_temp_celsius: Optional[float] = None) -> dict[str, Any]:
        """Start climate control.
        
        Args:
            vehicle_id: VIN, name, or license plate
            target_temp_celsius: Optional target temperature in Celsius (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
            return {"success": False, "error": "Vehicle does not support climatization commands"}
        
        if not vehicle.climatization.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support climatization start/stop command"}
        
        try:
            # Build command dict with temperature if provided
            command_dict = {"command": ClimatizationStartStopCommand.Command.START}
            if target_temp_celsius is not None:
                command_dict["target_temperature"] = target_temp_celsius
                command_dict["target_temperature_unit"] = "C"  # Always use Celsius
            
            vehicle.climatization.commands.commands["start-stop"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Climatization started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Climatization started"}
        except Exception as e:
            logger.error(f"Failed to start climatization for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_climatization(self, vehicle_id: str) -> dict[str, Any]:
        """Stop climate control.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
            return {"success": False, "error": "Vehicle does not support climatization commands"}
        
        if not vehicle.climatization.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support climatization start/stop command"}
        
        try:
            vehicle.climatization.commands.commands["start-stop"].value = ClimatizationStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Climatization stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Climatization stopped"}
        except Exception as e:
            logger.error(f"Failed to stop climatization for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_charging(self, vehicle_id: str) -> dict[str, Any]:
        """Start charging.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
            return {"success": False, "error": "Vehicle does not support charging commands"}
        
        if not vehicle.charging.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support charging start/stop command"}
        
        try:
            vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.START
            self.invalidate_cache()
            logger.info(f"Charging started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Charging started"}
        except Exception as e:
            logger.error(f"Failed to start charging for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_charging(self, vehicle_id: str) -> dict[str, Any]:
        """Stop charging.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
            return {"success": False, "error": "Vehicle does not support charging commands"}
        
        if not vehicle.charging.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support charging start/stop command"}
        
        try:
            vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Charging stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Charging stopped"}
        except Exception as e:
            logger.error(f"Failed to stop charging for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def flash_lights(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> dict[str, Any]:
        """Flash the vehicle lights.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
            return {"success": False, "error": "Vehicle does not support control commands"}
        
        if not vehicle.controls.commands.contains_command("honk-and-flash"):
            return {"success": False, "error": "Vehicle does not support honk/flash command"}
        
        try:
            # Build command dict with duration if provided
            command_dict = {"command": HonkAndFlashCommand.Command.FLASH}
            if duration_seconds is not None:
                command_dict["duration"] = duration_seconds
            
            vehicle.controls.commands.commands["honk-and-flash"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Lights flashed for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Lights flashed"}
        except Exception as e:
            logger.error(f"Failed to flash lights for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def honk_and_flash(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> dict[str, Any]:
        """Honk and flash the vehicle.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
            return {"success": False, "error": "Vehicle does not support control commands"}
        
        if not vehicle.controls.commands.contains_command("honk-and-flash"):
            return {"success": False, "error": "Vehicle does not support honk/flash command"}
        
        try:
            # Build command dict with duration if provided
            command_dict = {"command": HonkAndFlashCommand.Command.HONK_AND_FLASH}
            if duration_seconds is not None:
                command_dict["duration"] = duration_seconds
            
            vehicle.controls.commands.commands["honk-and-flash"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Honk and flash executed for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Honk and flash executed"}
        except Exception as e:
            logger.error(f"Failed to honk and flash for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_window_heating(self, vehicle_id: str) -> dict[str, Any]:
        """Start window heating.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
            return {"success": False, "error": "Vehicle does not support window heating commands"}
        
        if not vehicle.window_heating.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support window heating start/stop command"}
        
        try:
            vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.START
            self.invalidate_cache()
            logger.info(f"Window heating started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Window heating started"}
        except Exception as e:
            logger.error(f"Failed to start window heating for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_window_heating(self, vehicle_id: str) -> dict[str, Any]:
        """Stop window heating.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
            return {"success": False, "error": "Vehicle does not support window heating commands"}
        
        if not vehicle.window_heating.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support window heating start/stop command"}
        
        try:
            vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Window heating stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Window heating stopped"}
        except Exception as e:
            logger.error(f"Failed to stop window heating for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

