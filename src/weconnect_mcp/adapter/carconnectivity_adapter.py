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
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, ChargingModel, ClimatizationModel, 
    MaintenanceModel, RangeModel, DriveModel, WindowHeatingsModel, WindowHeatingModel, 
    LightsModel, LightModel, PositionModel, BatteryStatusModel, DoorsModel, DoorModel, 
    WindowsModel, WindowModel, TyreModel, TyresModel,
    # New consolidated models
    VehicleDetailLevel, PhysicalStatusModel, EnergyStatusModel, ClimateStatusModel,
    RangeInfo, ElectricDriveInfo, CombustionDriveInfo
)
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
    """Adapter for Volkswagen vehicles using the carconnectivity library.
    
    This adapter provides access to vehicle data from Volkswagen's WeConnect service
    through the carconnectivity third-party library. It handles authentication,
    data fetching, and transformation into standardized models.
    """

    def __init__(self, config_path: str, tokenstore_file: Optional[str] = None):
        """Initialize the CarConnectivity adapter.
        
        Args:
            config_path: Path to JSON config file containing VW account credentials
            tokenstore_file: Optional path to store authentication tokens
        """
        self.tokenstore_file = tokenstore_file
        self.config_path = config_path
        self.vehicles: List[Any] = []
        self.car_connectivity = None
        
        # Import carconnectivity lazily to allow tests without the library installed
        try:
            from carconnectivity import carconnectivity as _carconnectivity
        except Exception:
            raise  # Re-raise to provide original import error
            
        # Load configuration and initialize connection
        with open(config_path, 'r', encoding='utf-8') as fh:
            config_dict = json.load(fh)
        self.car_connectivity = _carconnectivity.CarConnectivity(
            config=config_dict, 
            tokenstore_file=tokenstore_file
        )
        self.car_connectivity.fetch_all()

    def shutdown(self):
        """Clean up resources and close connections."""
        if self.car_connectivity is not None:
            try:
                self.car_connectivity.shutdown()
            except Exception:
                pass  # Ignore errors during shutdown

    async def __aenter__(self) -> CarConnectivityAdapter:
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def __enter__(self) -> CarConnectivityAdapter:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def list_vehicles(self) -> list[VehicleListItem]:
        """Get list of all vehicles with VIN, name, model, and license plate.
        
        Returns:
            List of VehicleListItem objects containing basic vehicle information
        """
        if self.car_connectivity is None:
            return []
            
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
                # Fallback: only VIN available if vehicle data can't be retrieved
                vehicle_list.append(VehicleListItem(vin=vin))
        
        return vehicle_list

    # New consolidated methods (optimized tool structure)
    
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle information with configurable detail level.
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            details: Detail level (BASIC, FULL, or ALL)
            
        Returns:
            Vehicle information with requested detail level, or None if not found
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None

        vin_val = vehicle.vin.value if vehicle.vin is not None else None
        model_val = vehicle.model.value if vehicle.model is not None else None
        name_val = vehicle.name.value if vehicle.name is not None else None
        manufacturer_val = vehicle.manufacturer.value if vehicle.manufacturer is not None else None
        type_val = vehicle.type.value if vehicle.type is not None else None
        
        # BASIC level: just essential identifiers
        if details == VehicleDetailLevel.BASIC:
            return VehicleModel(
                vin=vin_val,
                model=model_val,
                name=name_val,
                manufacturer=manufacturer_val,
                type=type_val,
            )
        
        # FULL and ALL levels include additional data
        odometer_val = vehicle.odometer.value if vehicle.odometer is not None else None
        state_val = vehicle.state.value if vehicle.state is not None else None
        software_version_val = vehicle.software.version.value if vehicle.software is not None and vehicle.software.version is not None else None
        model_year_val = vehicle.model_year.value if vehicle.model_year is not None else None
        connection_state_val = vehicle.connection_state.value if vehicle.connection_state is not None else None

        return VehicleModel(
            vin=vin_val,
            model=model_val,
            name=name_val,
            manufacturer=manufacturer_val,
            odometer=odometer_val,
            state=state_val,
            type=type_val,
            software_version=software_version_val,
            model_year=model_year_val,
            connection_state=connection_state_val,
        )
    
    def get_physical_status(self, vehicle_id: str, components: Optional[List[str]] = None) -> Optional[PhysicalStatusModel]:
        """Get physical component status (doors, windows, tyres, lights).
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            components: Optional list to filter components (e.g., ["doors", "windows"])
                       If None, returns all available components
        
        Returns:
            Physical status with requested components, or None if vehicle not found
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        # Determine which components to include
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
        """Get consolidated energy and range information.
        
        Combines battery status, charging state, and range info into a single,
        vehicle-type-aware response.
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            
        Returns:
            Energy status appropriate for vehicle type, or None if not found
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        vehicle_type = vehicle.type.value if vehicle.type is not None else "unknown"
        
        # Get range information using existing helper
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
        
        # Electric/PHEV-specific data
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
        
        # Combustion-specific data  
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
        """Get climate control status (climatization + window heating).
        
        Args:
            vehicle_id: Vehicle identifier (VIN, name, or license plate)
            
        Returns:
            Climate status, or None if vehicle not found
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        return ClimateStatusModel(
            climatization=self._get_climatization_state(vehicle),
            window_heating=self._get_window_heating_state(vehicle),
        )

    # Internal helper methods

    def _get_vehicle_for_vin(self, vehicle_id: str) -> Optional[GenericVehicle]:
        """Internal helper to retrieve a vehicle object by identifier.
        
        Accepts vehicle name, VIN, or license plate. Will automatically resolve
        to the correct VIN using resolve_vehicle_id().
        
        Args:
            vehicle_id: Vehicle name, VIN, or license plate
            
        Returns:
            GenericVehicle object or None if not found
        """
        if self.car_connectivity is None:
            return None
            
        garage = self.car_connectivity.get_garage()
        if garage is None or not hasattr(garage, "get_vehicle"):
            return None
        
        # Resolve identifier to VIN (supports name, VIN, license plate)
        vin = self.resolve_vehicle_id(vehicle_id)
        if vin is None:
            # Fallback: try direct VIN lookup in case resolve failed
            vin = vehicle_id
            
        return garage.get_vehicle(vin)

    def _get_doors_state(self, vehicle: GenericVehicle) -> Optional[DoorsModel]:
        """Extract door states from vehicle object.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            DoorsModel with lock and open states for all doors, or None
        """
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
        """Extract window states from vehicle object.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            WindowsModel with open/closed state for all windows, or None
        """
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
        """Extract tyre pressure and temperature data from vehicle object.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            TyresModel with pressure and temperature for all tyres, or None
        """
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
        """Extract charging information from electric or hybrid vehicle.
        
        Retrieves detailed charging state including charging status, power,
        estimated completion time, battery level, and target charge level.
        
        Args:
            vehicle: GenericVehicle object (must be ElectricVehicle for charging data)
            
        Returns:
            ChargingModel with charging details, or None for non-electric vehicles
        """
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
    
    def _get_climatization_state(self, vehicle: GenericVehicle) -> Optional[ClimatizationModel]:
        """Extract climatization state and settings from vehicle.
        
        Retrieves current climatization status (heating/cooling/ventilation/off),
        target temperature, estimated completion time, and various climate settings.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            ClimatizationModel with climate control state and settings, or None
        """
        climatization = getattr(vehicle, 'climatization', None)
        if climatization is None:
            return None
        
        # Extract climatization state
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
        
        # Get settings
        target_temperature = None
        window_heating_enabled = None
        seat_heating_enabled = None
        climatization_at_unlock_enabled = None
        using_external_power = None
        
        settings = getattr(climatization, 'settings', None)
        if settings is not None:
            # Target temperature
            target_temp_attr = getattr(settings, 'target_temperature', None)
            if target_temp_attr is not None and target_temp_attr.value is not None:
                target_temperature = float(target_temp_attr.value)
            
            # Window heating
            window_heating_attr = getattr(settings, 'window_heating', None)
            if window_heating_attr is not None and window_heating_attr.value is not None:
                window_heating_enabled = bool(window_heating_attr.value)
            
            # Seat heating
            seat_heating_attr = getattr(settings, 'seat_heating', None)
            if seat_heating_attr is not None and seat_heating_attr.value is not None:
                seat_heating_enabled = bool(seat_heating_attr.value)
            
            # Climatization at unlock
            at_unlock_attr = getattr(settings, 'climatization_at_unlock', None)
            if at_unlock_attr is not None and at_unlock_attr.value is not None:
                climatization_at_unlock_enabled = bool(at_unlock_attr.value)
            
            # External power
            external_power_attr = getattr(settings, 'climatization_without_external_power', None)
            if external_power_attr is not None and external_power_attr.value is not None:
                # Note: this setting is "without" external power, so we invert it
                using_external_power = not bool(external_power_attr.value)
        
        # Get estimated time remaining
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
        """Extract maintenance schedule information from vehicle.
        
        Retrieves inspection and oil service due dates/distances, and calculates
        days/kilometers remaining until next service.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            MaintenanceModel with service schedule details, or None
        """
        maintenance = getattr(vehicle, 'maintenance', None)
        if maintenance is None:
            return None
        
        # Inspection due date
        inspection_due_date = None
        inspection_due_at = getattr(maintenance, 'inspection_due_at', None)
        if inspection_due_at is not None and inspection_due_at.value is not None:
            try:
                inspection_due_date = inspection_due_at.value.isoformat()
            except Exception:
                inspection_due_date = str(inspection_due_at.value)
        
        # Inspection due distance
        inspection_due_distance_km = None
        inspection_due_after = getattr(maintenance, 'inspection_due_after', None)
        if inspection_due_after is not None and inspection_due_after.value is not None:
            try:
                # Convert to km if needed (value might be in different units)
                inspection_due_distance_km = int(inspection_due_after.value)
            except Exception:
                pass
        
        # Oil service due date
        oil_service_due_date = None
        oil_service_due_at = getattr(maintenance, 'oil_service_due_at', None)
        if oil_service_due_at is not None and oil_service_due_at.value is not None:
            try:
                oil_service_due_date = oil_service_due_at.value.isoformat()
            except Exception:
                oil_service_due_date = str(oil_service_due_at.value)
        
        # Oil service due distance
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
        """Extract range information for electric and/or combustion drives.
        
        Retrieves total driving range, electric range with battery level,
        and combustion range with fuel tank level for hybrid vehicles.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            RangeModel with range details for available drive types, or None
        """
        drives = getattr(vehicle, 'drives', None)
        if drives is None:
            return None
        
        # Get total range
        total_range_km = None
        total_range_attr = getattr(drives, 'total_range', None)
        if total_range_attr is not None and total_range_attr.value is not None:
            total_range_km = float(total_range_attr.value)
        
        # Get individual drives
        electric_drive = None
        combustion_drive = None
        
        drives_dict = getattr(drives, 'drives', {})
        
        # Electric drive
        if 'electric' in drives_dict:
            electric = drives_dict['electric']
            electric_range = None
            battery_level = None
            
            range_attr = getattr(electric, 'range', None)
            if range_attr is not None and range_attr.value is not None:
                electric_range = float(range_attr.value)
            
            # Get battery level
            battery = getattr(electric, 'battery', None)
            if battery is not None:
                level_attr = getattr(battery, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    battery_level = float(level_attr.value)
            
            electric_drive = DriveModel(
                range_km=electric_range,
                battery_level_percent=battery_level
            )
        
        # Combustion drive
        if 'combustion' in drives_dict:
            combustion = drives_dict['combustion']
            combustion_range = None
            tank_level = None
            
            range_attr = getattr(combustion, 'range', None)
            if range_attr is not None and range_attr.value is not None:
                combustion_range = float(range_attr.value)
            
            # Get tank level
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
        """Extract window heating state for front and rear windows.
        
        Retrieves heating status (on/off) for front and rear window defrosters.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            WindowHeatingsModel with front/rear heating states, or None
        """
        window_heating = getattr(vehicle, 'window_heating', None)
        if window_heating is None:
            return None
        
        front_heating = None
        rear_heating = None
        
        # Get heating state
        heating_state_attr = getattr(window_heating, 'heating_state', None)
        if heating_state_attr is not None and heating_state_attr.value is not None:
            from carconnectivity.window_heating import WindowHeatings
            # The global state might indicate if any window heating is on
            pass
        
        # Get individual window heatings
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
        """Extract exterior lights state (left and right).
        
        Retrieves current status (on/off) of left and right exterior lights.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            LightsModel with left/right light states, or None
        """
        lights = getattr(vehicle, 'lights', None)
        if lights is None:
            return None
        
        left_light = None
        right_light = None
        
        # Get individual lights
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
        """Get maintenance schedule and service information."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_maintenance_info(vehicle)

    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """Get current vehicle position (GPS coordinates and heading)."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        return self._get_position(vehicle)

    def _get_position(self, vehicle: GenericVehicle) -> Optional[PositionModel]:
        """Extract GPS position from vehicle object.
        
        Retrieves current GPS coordinates (latitude, longitude) and heading direction.
        
        Args:
            vehicle: GenericVehicle object
            
        Returns:
            PositionModel with GPS coordinates and heading, or None if unavailable
        """
        pos = vehicle.position
        if pos is None:
            return None
        
        latitude = pos.latitude.value if pos.latitude is not None else None
        longitude = pos.longitude.value if pos.longitude is not None else None
        heading = pos.heading.value if pos.heading is not None else None
        
        # Only return position if we have at least coordinates
        if latitude is None and longitude is None:
            return None
        
        return PositionModel(
            latitude=latitude,
            longitude=longitude,
            heading=heading
        )
