"""
TestAdapter - Mock Implementation for Testing
==============================================

This module provides a mock adapter implementation for testing purposes.

Purpose:
- Provides deterministic test data without requiring actual API calls
- Implements all AbstractAdapter methods with realistic mock data
- Used by all tool tests in tests/tools/ directory

Mock vehicles:
1. Transporter 7 (VIN: WV2ZZZSTZNH009136)
   - Type: combustion
   - License plate: M-AB 1234
   - Features: Full tank (68%), diesel, parked in Berlin

2. ID.7 Tourer (VIN: WVWZZZED4SE003938)
   - Type: electric
   - License plate: M-XY 5678
   - Features: 80% battery, active heating, parked in Munich

Test data characteristics:
- Realistic values (battery levels, pressures, temperatures)
- Consistent state across methods
- Both vehicle types represented (electric & combustion)
- All consolidated methods implemented
"""
from types import SimpleNamespace
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, PositionModel, BatteryStatusModel, 
    DoorsModel, DoorModel, WindowsModel, WindowModel, TyreModel, TyresModel, 
    ChargingModel, ClimatizationModel, MaintenanceModel, RangeModel, DriveModel, 
    WindowHeatingsModel, WindowHeatingModel, LightsModel, LightModel,
    # New consolidated models
    VehicleDetailLevel, PhysicalStatusModel, EnergyStatusModel, ClimateStatusModel,
    RangeInfo, ElectricDriveInfo, CombustionDriveInfo
)
from weconnect_mcp.adapter.carconnectivity_adapter import VehicleModel

from pydantic import BaseModel
from typing import Optional



class TestAdapter(AbstractAdapter):

    v1 = VehicleModel(
        manufacturer='Volkswagen',
        model='Transporter 7',
        name='T7',
        state='parked',
        vin='WV2ZZZSTZNH009136',
        type='combustion',
        odometer=12345.0,
        software_version='3.2.1',
        model_year=2023,
        connection_state='online',
    )
    v2 = VehicleModel(
        manufacturer='Volkswagen',
        model='ID.7 Tourer',
        name='ID7',
        state='parked',
        vin='WVWZZZED4SE003938',
        type='electric',
        odometer=31643.0,
        software_version='4.1.0',
        model_year=2024,
        connection_state='online',
    )
    vehicles = [v1, v2]
    
    # Mock license plates
    license_plates = {
        'WV2ZZZSTZNH009136': 'M-AB 1234',  # T7
        'WVWZZZED4SE003938': 'M-XY 5678',  # ID7
    }

    def _resolve_to_vin(self, vehicle_id: str) -> Optional[str]:
        """Helper to resolve any identifier to VIN."""
        vin = self.resolve_vehicle_id(vehicle_id)
        return vin if vin else vehicle_id

    def shutdown(self):
        pass

    def list_vehicles(self) -> list[VehicleListItem]:
        # Return the list of vehicles with VIN, name, model, and license plate
        return [
            VehicleListItem(
                vin=v.vin if v.vin else "",
                name=v.name,
                model=v.model,
                license_plate=self.license_plates.get(v.vin if v.vin else "")
            )
            for v in self.vehicles if v.vin
        ]

    # New consolidated methods (optimized tool structure)
    
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle information with configurable detail level."""
        vin = self._resolve_to_vin(vehicle_id)
        
        for v in self.vehicles:
            if v.vin == vin:
                if details == VehicleDetailLevel.BASIC:
                    # BASIC: only essential identifiers
                    return VehicleModel(
                        vin=v.vin,
                        model=v.model,
                        name=v.name,
                        manufacturer=v.manufacturer,
                        type=v.type,
                    )
                # FULL and ALL: return everything
                return v
        return None
    
    def get_physical_status(self, vehicle_id: str, components: Optional[list[str]] = None) -> Optional[PhysicalStatusModel]:
        """Get physical component status (doors, windows, tyres, lights)."""
        vin = self._resolve_to_vin(vehicle_id)
        
        for v in self.vehicles:
            if v.vin == vin:
                # Determine which components to include
                # Empty list should be treated as None (all components)
                include_all = components is None or len(components) == 0
                include_doors = include_all or (components is not None and "doors" in components)
                include_windows = include_all or (components is not None and "windows" in components)
                include_tyres = include_all or (components is not None and "tyres" in components)
                include_lights = include_all or (components is not None and "lights" in components)
                
                # Mock data - you can expand this with actual test data
                doors = DoorsModel(
                    lock_state=True,
                    open_state=False,
                    front_left=DoorModel(locked=True, open=False),
                    front_right=DoorModel(locked=True, open=False),
                    rear_left=DoorModel(locked=True, open=False),
                    rear_right=DoorModel(locked=True, open=False),
                    trunk=DoorModel(locked=True, open=False),
                    bonnet=DoorModel(locked=True, open=False),
                ) if include_doors else None
                
                windows = WindowsModel(
                    front_left=WindowModel(open=False),
                    front_right=WindowModel(open=False),
                    rear_left=WindowModel(open=False),
                    rear_right=WindowModel(open=False),
                ) if include_windows else None
                
                tyres = TyresModel(
                    front_left=TyreModel(pressure=2.3, temperature=20.0),
                    front_right=TyreModel(pressure=2.3, temperature=20.0),
                    rear_left=TyreModel(pressure=2.5, temperature=21.0),
                    rear_right=TyreModel(pressure=2.5, temperature=21.0),
                ) if include_tyres else None
                
                lights = LightsModel(
                    left=LightModel(state='ok'),
                    right=LightModel(state='ok'),
                ) if include_lights else None
                
                return PhysicalStatusModel(
                    doors=doors,
                    windows=windows,
                    tyres=tyres,
                    lights=lights,
                )
        return None
    
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get consolidated energy and range information."""
        vin = self._resolve_to_vin(vehicle_id)
        
        for v in self.vehicles:
            if v.vin == vin:
                if v.type == 'electric':
                    # Electric vehicle
                    return EnergyStatusModel(
                        vehicle_type='electric',
                        range=RangeInfo(
                            total_km=312.0,
                            electric_km=312.0,
                            combustion_km=None,
                        ),
                        electric=ElectricDriveInfo(
                            battery_level_percent=77.0,
                            charging=ChargingModel(
                                is_charging=True,
                                is_plugged_in=True,
                                charging_power_kw=11.0,
                                charging_state='charging',
                                remaining_time_minutes=45,
                                target_soc_percent=90,
                                current_soc_percent=77.0,
                                charge_mode='manual'
                            )
                        ),
                        combustion=None,
                    )
                else:
                    # Combustion vehicle
                    return EnergyStatusModel(
                        vehicle_type='combustion',
                        range=RangeInfo(
                            total_km=650.0,
                            electric_km=None,
                            combustion_km=650.0,
                        ),
                        electric=None,
                        combustion=CombustionDriveInfo(
                            tank_level_percent=68.0,
                            fuel_type='diesel',
                        ),
                    )
        return None
    
    def get_climate_status(self, vehicle_id: str) -> Optional[ClimateStatusModel]:
        """Get climate control status (climatization + window heating)."""
        vin = self._resolve_to_vin(vehicle_id)
        
        for v in self.vehicles:
            if v.vin == vin:
                # Mock climate data
                if 'ID7' in (v.name or ''):
                    climatization = ClimatizationModel(
                        state='heating',
                        is_active=True,
                        target_temperature_celsius=22.0,
                        estimated_time_remaining_minutes=8,
                        window_heating_enabled=True,
                        seat_heating_enabled=True,
                        climatization_at_unlock_enabled=True,
                        using_external_power=True
                    )
                    window_heating = WindowHeatingsModel(
                        front=WindowHeatingModel(state='on'),
                        rear=WindowHeatingModel(state='on'),
                    )
                else:
                    climatization = ClimatizationModel(
                        state='off',
                        is_active=False,
                        target_temperature_celsius=21.0,
                        estimated_time_remaining_minutes=None,
                        window_heating_enabled=False,
                        seat_heating_enabled=False,
                        climatization_at_unlock_enabled=False,
                        using_external_power=None
                    )
                    window_heating = WindowHeatingsModel(
                        front=WindowHeatingModel(state='off'),
                        rear=WindowHeatingModel(state='off'),
                    )
                
                return ClimateStatusModel(
                    climatization=climatization,
                    window_heating=window_heating,
                )
        return None

    def get_maintenance_info(self, vehicle_id) -> Optional[MaintenanceModel]:
        # Resolve identifier to VIN
        vin = self._resolve_to_vin(vehicle_id)
        
        # Return mock maintenance info
        for v in self.vehicles:
            if v.vin == vin:
                # Mock different maintenance schedules
                if 'ID7' in (v.name or ''):
                    # Electric vehicle - no oil service
                    return MaintenanceModel(
                        inspection_due_date='2026-08-15T00:00:00+00:00',
                        inspection_due_distance_km=8500,
                        oil_service_due_date=None,
                        oil_service_due_distance_km=None
                    )
                else:
                    # Combustion vehicle - has oil service
                    return MaintenanceModel(
                        inspection_due_date='2026-05-20T00:00:00+00:00',
                        inspection_due_distance_km=12000,
                        oil_service_due_date='2026-04-10T00:00:00+00:00',
                        oil_service_due_distance_km=8000
                    )
        return None

    def get_position(self, vehicle_id) -> Optional[PositionModel]:
        # Resolve identifier to VIN
        vin = self._resolve_to_vin(vehicle_id)
        
        # Return mock position data
        for v in self.vehicles:
            if v.vin == vin:
                # Mock different positions for different vehicles
                if v.name and 'ID7' in v.name:
                    # ID.7 in Munich
                    return PositionModel(
                        latitude=48.1351,
                        longitude=11.5820,
                        heading=270
                    )
                else:
                    # T7 in Berlin
                    return PositionModel(
                        latitude=52.5200,
                        longitude=13.4050,
                        heading=90
                    )
        return None
