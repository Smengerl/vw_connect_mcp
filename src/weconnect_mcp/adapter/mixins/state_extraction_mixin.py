"""State extraction mixin for adapter.

Provides methods to extract vehicle state information from carconnectivity
vehicle objects. Organized by category: physical, energy, climate, location.
"""

from typing import Optional

from carconnectivity.vehicle import GenericVehicle, ElectricVehicle, CombustionVehicle
from carconnectivity.doors import Doors
from carconnectivity.windows import Windows
from carconnectivity.drive import ElectricDrive, CombustionDrive, DieselDrive

from weconnect_mcp.adapter.abstract_adapter import (
    DoorsModel, DoorModel, WindowsModel, WindowModel,
    TyresModel, TyreModel, LightsModel, LightModel,
    ChargingModel, ClimatizationModel, MaintenanceModel,
    RangeModel, DriveModel, WindowHeatingsModel, WindowHeatingModel,
    PositionModel,
)


class StateExtractionMixin:
    """Mixin providing vehicle state extraction methods.
    
    All extraction methods follow naming convention _get_*_state() or _get_*_info()
    and return Optional[Model] objects from abstract_adapter.
    
    Categories:
    - Physical: doors, windows, tyres, lights
    - Energy: charging, range
    - Climate: climatization, window_heating
    - Location: position
    - Maintenance: maintenance schedule
    """
    
    # ==================== PHYSICAL STATE ====================
    
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
    
    # ==================== ENERGY STATE ====================
    
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
    
    def _get_range_info(self, vehicle: GenericVehicle) -> Optional[RangeModel]:
        """Extract range for electric and/or combustion drives.
        
        Drives are accessed via 'primary' and 'secondary' keys, not 'electric'/'combustion'.
        Drive type is determined by isinstance() checks:
        - ElectricDrive: has battery, battery_level, battery_temperature
        - DieselDrive: has tank, adblue_range, adblue_level (subclass of CombustionDrive)
        - CombustionDrive: has tank only
        """
        drives = getattr(vehicle, 'drives', None)
        if drives is None:
            return None
        
        # Total range across all drives
        total_range_km = None
        total_range_attr = getattr(drives, 'total_range', None)
        if total_range_attr is not None and total_range_attr.value is not None:
            total_range_km = float(total_range_attr.value)
        
        electric_drive = None
        combustion_drive = None
        
        drives_dict = getattr(drives, 'drives', {})
        
        # Process all drives (primary, secondary, etc.)
        for drive_key, drive in drives_dict.items():
            if drive is None:
                continue
                
            # Extract common attributes
            drive_range = None
            range_attr = getattr(drive, 'range', None)
            if range_attr is not None and range_attr.value is not None:
                drive_range = float(range_attr.value)
            
            # Check drive type and extract type-specific attributes
            if isinstance(drive, ElectricDrive):
                # Electric drive: has battery with level and temperature
                battery_level = None
                battery_temperature = None
                
                # Battery level from drive.level
                level_attr = getattr(drive, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    battery_level = float(level_attr.value)
                
                # Battery temperature from drive.battery.temperature
                battery = getattr(drive, 'battery', None)
                if battery is not None:
                    temp_attr = getattr(battery, 'temperature', None)
                    if temp_attr is not None and temp_attr.value is not None:
                        battery_temperature = float(temp_attr.value)
                
                electric_drive = DriveModel(
                    range_km=drive_range,
                    battery_level_percent=battery_level,
                    battery_temperature_kelvin=battery_temperature
                )
            
            elif isinstance(drive, DieselDrive):
                # Diesel drive: has tank + AdBlue attributes
                tank_level = None
                adblue_range = None
                adblue_level = None
                
                # Tank level from drive.level
                level_attr = getattr(drive, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    tank_level = float(level_attr.value)
                
                # AdBlue range
                adblue_range_attr = getattr(drive, 'adblue_range', None)
                if adblue_range_attr is not None and adblue_range_attr.value is not None:
                    adblue_range = float(adblue_range_attr.value)
                
                # AdBlue level
                adblue_level_attr = getattr(drive, 'adblue_level', None)
                if adblue_level_attr is not None and adblue_level_attr.value is not None:
                    adblue_level = float(adblue_level_attr.value)
                
                combustion_drive = DriveModel(
                    range_km=drive_range,
                    tank_level_percent=tank_level,
                    adblue_range_km=adblue_range,
                    adblue_level_percent=adblue_level
                )
            
            elif isinstance(drive, CombustionDrive):
                # Generic combustion drive: has tank only (no AdBlue)
                tank_level = None
                
                # Tank level from drive.level
                level_attr = getattr(drive, 'level', None)
                if level_attr is not None and level_attr.value is not None:
                    tank_level = float(level_attr.value)
                
                combustion_drive = DriveModel(
                    range_km=drive_range,
                    tank_level_percent=tank_level
                )
        
        return RangeModel(
            total_range_km=total_range_km,
            electric_drive=electric_drive,
            combustion_drive=combustion_drive
        )
    
    # ==================== CLIMATE STATE ====================
    
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
    
    # ==================== LOCATION STATE ====================
    
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
    
    # ==================== MAINTENANCE INFO ====================
    
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
