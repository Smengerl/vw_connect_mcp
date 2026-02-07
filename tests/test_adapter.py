from types import SimpleNamespace
from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter, VehicleModel, PositionModel, DoorsModel, DoorModel, WindowsModel, WindowModel, TyreModel, TyresModel
from weconnect_mcp.adapter.carconnectivity_adapter import VehicleModel

from pydantic import BaseModel
from typing import Optional



class TestAdapter(AbstractAdapter):

    v1 = VehicleModel(
        manufacturer='Volkswagen',
        model='Transporter 7',
        name='T7',
        state='unknown vehicle state',
        vin='WV2ZZZSTZNH009136',
        type='electric',
        odometer=12345.0,
        windows=WindowsModel(
            front_left=WindowModel(open=False),
            front_right=WindowModel(open=False),
            rear_left=WindowModel(open=True),
            rear_right=WindowModel(open=False),
        ),        
        doors=DoorsModel(
            lock_state=True,
            open_state=False,
            front_left=DoorModel(locked=True, open=False),
            front_right=DoorModel(locked=True, open=False),
            rear_left=DoorModel(locked=True, open=True),
            rear_right=DoorModel(locked=True, open=False),
            trunk=DoorModel(locked=True, open=False),
            bonnet=DoorModel(locked=True, open=False),
        ),
        #tyres=TyresModel(
        #    front_left=TyreModel(pressure=2.2, temperature=23.0),
        #    front_right=TyreModel(pressure=2.2, temperature=23.0),
        #    rear_left=TyreModel(pressure=2.4, temperature=22.0),
        #    rear_right=TyreModel(pressure=2.4, temperature=22.0),
        #)
        #position=None,
        #capabilities={'charging': {'state': 'charging'}}
    )
    v2 = VehicleModel(
        manufacturer='Volkswagen',
        model='ID.7 Tourer',
        name='ID7',
        state='parked',
        vin='WVWZZZED4SE003938',
        type='electric',
        odometer=31643.0,
        #position={'latitude': 52.418066, 'longitude': 10.593389},
        #capabilities={},

        windows=WindowsModel(
            front_left=WindowModel(open=False),
            front_right=WindowModel(open=False),
            rear_left=WindowModel(open=False),
            rear_right=WindowModel(open=False),
        ),        
        doors=DoorsModel(
            front_left=DoorModel(locked=False, open=False),
            front_right=DoorModel(locked=False, open=True),
            rear_left=DoorModel(locked=False, open=True),
            rear_right=DoorModel(locked=False, open=False),
            trunk=DoorModel(locked=False, open=False),
            bonnet=DoorModel(locked=False, open=False),
        ),
        tyres=TyresModel(
            front_left=TyreModel(pressure=2.3, temperature=25.0),
            front_right=TyreModel(pressure=2.3, temperature=25.0),
            rear_left=TyreModel(pressure=2.5, temperature=24.0),
            rear_right=TyreModel(pressure=2.5, temperature=24.0),
        )
    )
    vehicles = [v1, v2]

    def shutdown(self):
        pass

    def list_vehicles(self) -> list[str]:
        # Return the list of vehicle IDs (vin)
        return [v.vin for v in self.vehicles if isinstance(v.vin, str)]

    def get_vehicle(self, vehicle_id) -> Optional[VehicleModel]:
        # Return the vehicle object matching the vin
        for v in self.vehicles:
            if v.vin == vehicle_id:
                return v
        return None
    
    def get_doors_state(self, vehicle_id) -> Optional[DoorsModel]:
        # Return a mock doors state
        for v in self.vehicles:
            if v.vin == vehicle_id:
                return v.doors
        return None

    def get_windows_state(self, vehicle_id) -> Optional[WindowsModel]:
        # Return a mock windows state
        for v in self.vehicles:
            if v.vin == vehicle_id:
                return v.windows
        return None

    def get_tyres_state(self, vehicle_id) -> Optional[TyresModel]:
        # Return a mock tyres state
        for v in self.vehicles:
            if v.vin == vehicle_id:
                return v.tyres
        return None