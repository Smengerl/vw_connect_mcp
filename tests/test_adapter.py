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
- Realistic values (battery levels, SOC, etc.)
- Consistent state across methods
- Both vehicle types represented (electric & combustion)
- Only the methods AbstractAdapter still declares (Tibber's surface)
"""
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, VehicleDetailLevel,
    EnergyStatusModel, RangeInfo, ElectricDriveInfo, CombustionDriveInfo,
    ChargingModel,
)

from typing import Optional


class TestAdapter(AbstractAdapter):

    v1 = VehicleModel(
        manufacturer='Volkswagen',
        model='Transporter 7',
        name='T7',
        license_plate='M-AB 1234',
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
        license_plate='M-XY 5678',
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
                        license_plate=v.license_plate,
                        manufacturer=v.manufacturer,
                        type=v.type,
                    )
                # FULL and ALL: return everything
                return v
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
