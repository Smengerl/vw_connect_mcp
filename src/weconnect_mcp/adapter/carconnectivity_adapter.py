"""Adapter that wires the carconnectivity library into the generic MCP server.

This file depends on the third-party `carconnectivity` library; its responsibilities are:
- initialize CarConnectivity 
- provide a vehicles_getter callable returning the list of vehicles
"""
from __future__ import annotations

import json
import os
from typing import List, Any, Optional
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
from carconnectivity.vehicle import GenericVehicle

import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel

class VehicleModel(BaseModel):
    vin: str
    model: Optional[str]
    name: Optional[str]


class CarConnectivityAdapter(AbstractAdapter):
    def __init__(self, config_path: str, tokenstore_file: Optional[str] = None):
        self.tokenstore_file = tokenstore_file
        self.config_path = config_path
        self.car_connectivity = None
        self.vehicles: List[Any] = []
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
    def list_vehicles(self) -> list[str]:
        if self.car_connectivity is not None:
            return self.car_connectivity.get_garage().list_vehicle_vins()
        return []


    def get_vehicle(self, vehicle_id: str) -> Optional[BaseModel]:
        if self.car_connectivity is not None:
            vehicle = self.car_connectivity.get_garage().get_vehicle(vehicle_id)
            
            if vehicle is None:
                return None                

            # Ensure vin is a non-None str (VehicleModel.vin expects str)
            vin_val: str = ""
            if vehicle.vin is not None and vehicle.vin.value is not None:
                vin_val = vehicle.vin.value

            # model and name are optional fields
            model_val: Optional[str] = None
            if vehicle.model is not None:
                model_val = vehicle.model.value

            name_val: Optional[str] = None
            if vehicle.name is not None:
                name_val = vehicle.name.value

            return VehicleModel(vin=vin_val, model=model_val, name=name_val)
        return None