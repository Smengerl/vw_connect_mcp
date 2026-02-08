"""CarConnectivity adapter for VW vehicles via WeConnect.

Depends on third-party carconnectivity library for:
- CarConnectivity initialization
- vehicles_getter callable

Uses mixin pattern to compose functionality:
- CacheMixin: Data caching and invalidation
- VehicleResolutionMixin: Resolve identifiers (VIN/name/plate) to VIN
- CommandMixin: All vehicle control commands
- StateExtractionMixin: Extract state from vehicle objects
"""

import json
import sys
import logging
from typing import List, Any, Optional
from datetime import datetime, timedelta

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem,
    VehicleDetailLevel, PhysicalStatusModel, EnergyStatusModel, ClimateStatusModel,
    RangeInfo, ElectricDriveInfo, CombustionDriveInfo, MaintenanceModel, PositionModel
)
from weconnect_mcp.adapter.mixins import (
    CacheMixin, VehicleResolutionMixin, CommandMixin, StateExtractionMixin
)
from carconnectivity.vehicle import GenericVehicle, ElectricVehicle, CombustionVehicle

# Cache duration to avoid VW API rate limits
CACHE_DURATION_SECONDS = 300  # in seconds

# Configure logging to stderr for MCP stdio compatibility
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)


class CarConnectivityAdapter(
    CacheMixin,
    VehicleResolutionMixin,
    CommandMixin,
    StateExtractionMixin,
    AbstractAdapter
):
    """Adapter for VW vehicles using carconnectivity library.
    
    Provides access to VW WeConnect service data via third-party library.
    Composed of multiple mixins for different functionality areas:
    - CacheMixin: Data caching to avoid API rate limits
    - VehicleResolutionMixin: Resolve vehicle identifiers to VIN
    - CommandMixin: Vehicle control commands (lock, climate, charging, etc.)
    - StateExtractionMixin: Extract state from vehicle objects
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
        self._mark_data_fetched()
        logger.info("Fetched fresh data from VW servers")

    def shutdown(self):
        """Clean up resources."""
        if self.car_connectivity is not None:
            try:
                self.car_connectivity.shutdown()
            except Exception:
                pass

    async def __aenter__(self) -> 'CarConnectivityAdapter':
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def __enter__(self) -> 'CarConnectivityAdapter':
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

    def get_maintenance_info(self, vehicle_id: str) -> Optional[MaintenanceModel]:
        """Get maintenance schedule info."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        return self._get_maintenance_info(vehicle)

    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """Get GPS location."""
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return None
        
        return self._get_position(vehicle)

    def _get_vehicle_for_vin(self, vehicle_id: str) -> Optional[GenericVehicle]:
        """Get vehicle by identifier (VIN, name, or license plate)."""
        if self.car_connectivity is None:
            return None
        
        # Ensure we have fresh data before accessing vehicle
        self._ensure_fresh_data()
            
        garage = self.car_connectivity.get_garage()
        if garage is None or not hasattr(garage, "get_vehicle"):
            return None
        
        # Try to resolve identifier to VIN (handles name/license plate)
        vin = self.resolve_vehicle_id(vehicle_id)
        if vin is None:
            vin = vehicle_id  # Assume it's already a VIN
            
        return garage.get_vehicle(vin)
