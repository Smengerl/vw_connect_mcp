from types import SimpleNamespace
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter

from pydantic import BaseModel

class MockVehicle(BaseModel):
    manufacturer: str
    model: str
    name: str
    state: str
    vin: str
    type: str
    odometer: float
    position: dict | None
    capabilities: dict

class TestAdapter(AbstractAdapter):

    v1 = MockVehicle(
        manufacturer='Volkswagen',
        model='Transporter 7',
        name='T7',
        state='unknown vehicle state',
        vin='WV2ZZZSTZNH009136',
        type='electric',
        odometer=12345.0,
        position=None,
        capabilities={'charging': {'state': 'charging'}}
    )
    v2 = MockVehicle(
        manufacturer='Volkswagen',
        model='ID.7 Tourer',
        name='ID7',
        state='parked',
        vin='WVWZZZED4SE003938',
        type='electric',
        odometer=31643.0,
        position={'latitude': 52.418066, 'longitude': 10.593389},
        capabilities={}
    )
    vehicles = [v1, v2]

    def shutdown(self):
        pass

    def list_vehicles(self):
        # Return the list of vehicle IDs (vin)
        return [v.vin for v in self.vehicles]

    def get_vehicle(self, vehicle_id):
        # Return the vehicle object matching the vin
        for v in self.vehicles:
            if v.vin == vehicle_id:
                return v
        return None