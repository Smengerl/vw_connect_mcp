"""
TestAdapter - Mock Implementation for Testing
==============================================

This module provides a mock adapter implementation for testing purposes.

Purpose:
- Provides deterministic test data without requiring actual API calls
- Implements all AbstractAdapter methods with realistic mock data
- Used by all tool tests in tests/tools/ directory

Mock vehicles (both electric -- Tibber's Enode-backed integration is
EV-only, confirmed live, see ARCHITECTURE.md; there is no combustion/PHEV
data to model for a second vehicle here, so the two exist purely to cover
multi-vehicle resolution, not a second energy-data shape). No license
plates either -- Tibber's Data API never reports one, so VehicleListItem
has no field for it (see abstract_adapter.py's docstring):
1. T7 Multivan eHybrid (VIN: WV2ZZZSTZNH009136) -- the *name* keeps its
   real-world "eHybrid" badge (still a realistic Tibber-paired vehicle
   name), but its energy data is the plain electric shape like any other
   vehicle Tibber reports -- 64% battery, plugged in, not charging.
2. ID.7 Tourer (VIN: WVWZZZED4SE003938) -- 80% battery, actively charging.

Test data characteristics:
- Realistic values (battery levels, SOC, etc.)
- Consistent state across methods
- Two vehicles with different values, to exercise identifier resolution
- Only the methods AbstractAdapter still declares (Tibber's surface)
"""
from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, VehicleDetailLevel,
    EnergyStatusModel, RangeInfo, ElectricDriveInfo, ChargingModel,
)

from typing import Optional


class TestAdapter(AbstractAdapter):

    v1 = VehicleModel(
        manufacturer='Volkswagen',
        model='Multivan eHybrid',
        name='T7',
        vin='WV2ZZZSTZNH009136',
        connection_state='online',
        last_seen='2024-01-15T10:30:00Z',
    )
    v2 = VehicleModel(
        manufacturer='Volkswagen',
        model='ID.7 Tourer',
        name='ID7',
        vin='WVWZZZED4SE003938',
        connection_state='online',
        last_seen='2024-01-15T10:31:00Z',
    )
    vehicles = [v1, v2]

    # Mock energy data, keyed by VIN -- both electric-shaped (see module
    # docstring), differing only in values so tests can tell the two
    # vehicles apart.
    energy_data = {
        'WV2ZZZSTZNH009136': EnergyStatusModel(  # T7
            range=RangeInfo(total_km=630.0),
            electric=ElectricDriveInfo(
                battery_level_percent=64.0,
                charging=ChargingModel(
                    is_charging=False,
                    is_plugged_in=True,
                    charging_state='idle',
                    target_soc_percent=80,
                    current_soc_percent=64.0,
                )
            ),
            last_seen='2024-01-15T10:30:00Z',
        ),
        'WVWZZZED4SE003938': EnergyStatusModel(  # ID7
            range=RangeInfo(total_km=312.0),
            electric=ElectricDriveInfo(
                battery_level_percent=77.0,
                charging=ChargingModel(
                    is_charging=True,
                    is_plugged_in=True,
                    charging_state='charging',
                    target_soc_percent=90,
                    current_soc_percent=77.0,
                )
            ),
            last_seen='2024-01-15T10:31:00Z',
        ),
    }

    def _resolve_to_vin(self, vehicle_id: str) -> Optional[str]:
        """Helper to resolve any identifier to VIN."""
        vin = self.resolve_vehicle_id(vehicle_id)
        return vin if vin else vehicle_id

    def shutdown(self):
        pass

    def list_vehicles(self) -> list[VehicleListItem]:
        # Return the list of vehicles with VIN, name, and model
        return [
            VehicleListItem(
                vin=v.vin if v.vin else "",
                name=v.name,
                model=v.model,
            )
            for v in self.vehicles if v.vin
        ]

    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle information with configurable detail level."""
        vin = self._resolve_to_vin(vehicle_id)

        for v in self.vehicles:
            if v.vin == vin:
                if details == VehicleDetailLevel.BASIC:
                    # BASIC: everything except connection_state
                    return VehicleModel(
                        vin=v.vin,
                        model=v.model,
                        name=v.name,
                        manufacturer=v.manufacturer,
                    )
                # FULL: BASIC + connection_state
                return v
        return None

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get consolidated energy and range information."""
        vin = self._resolve_to_vin(vehicle_id)
        return self.energy_data.get(vin)
