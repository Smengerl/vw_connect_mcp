import os
import pytest
from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter, VehicleModel
from pathlib import Path
from collections.abc import AsyncIterator

import logging
logger = logging.getLogger(__name__)



@pytest.fixture(scope="module")
def config_path() -> Path:
    """ Returns the path to the config.json file located in ../src/ relative to this test file. Long lived, so module scope. """
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../src/config.json").resolve()

@pytest.fixture(scope="module")
def tokenstore_file() -> Path:
    """ Returns the path to the tokenstore file located in ../tmp/ relative to this test file. Long lived, so module scope. """
    current_dir = Path(__file__).resolve().parent
    return (current_dir / "../tmp/tokenstore").resolve()


@pytest.fixture(scope="module")
async def adapter(
    config_path: Path,
    tokenstore_file: Path,
) -> AsyncIterator[CarConnectivityAdapter]:
    """ Provides a CarConnectivityAdapter instance for testing. Long lived, so module scope. """
    logger.debug("1/7 Entering adapter fixture")
    async with CarConnectivityAdapter(
        config_path.as_posix(),
        tokenstore_file.as_posix(),
    ) as adapter:
        yield adapter
    logger.debug("7/7 Exiting adapter fixture")



def test_adapter_all_vehicles_basic_data(adapter: CarConnectivityAdapter):    
    # Liste der Fahrzeuge abrufen
    vins = adapter.list_vehicles()
    assert isinstance(vins, list)
    assert all(isinstance(v, str) for v in vins)
    # Es sollte mindestens ein Fahrzeug geben (abhängig von Testdaten)
    # assert len(vins) > 0

    # Für jedes Fahrzeug ein paar Felder prüfen
    for vin in vins:
        vehicle = adapter.get_vehicle(vin)
        assert isinstance(vehicle, VehicleModel)
        # VIN sollte übereinstimmen
        assert vehicle.vin == vin
        # Modell, Name, Hersteller können None sein, aber sollten als Attribute existieren
        assert hasattr(vehicle, "model")
        assert hasattr(vehicle, "name")
        assert hasattr(vehicle, "manufacturer")
        # Odometer kann None oder float sein
        assert hasattr(vehicle, "odometer")
        # Position, Batterie etc. sind optionale verschachtelte Modelle
        assert hasattr(vehicle, "position")
        assert hasattr(vehicle, "state")

        assert hasattr(vehicle, "doors")
        #assert vehicle.doors is not None

        assert hasattr(vehicle, "windows")
        #assert vehicle.windows is not None


@pytest.mark.parametrize(
    "vin",
    [
        "WVWZZZED4SE003938",
    ],
)
async def test_mcp_get_vehicle_doors_state(adapter, vin):
    """ Tests that the MCP client can get the state of a vehicle via the doors API. """
    doors = adapter.get_doors_state(vin)
    assert doors is not None
    assert doors.rear_left is not None
    assert doors.rear_left.locked is not None
    assert doors.rear_left.open is not None
    assert doors.rear_right is not None
    assert doors.rear_right.locked is not None
    assert doors.rear_right.open is not None
    assert doors.front_left is not None
    assert doors.front_left.locked is not None
    assert doors.front_left.open is not None
    assert doors.front_right is not None
    assert doors.front_right.locked is not None
    assert doors.front_right.open is not None
    assert doors.bonnet is not None
#    assert doors.bonnet.locked is not None
    assert doors.bonnet.open is not None
    assert doors.trunk is not None
    assert doors.trunk.locked is not None
    assert doors.trunk.open is not None


@pytest.mark.parametrize(
    "vin",
    [
        "WVWZZZED4SE003938",
    ],
)
async def test_mcp_get_vehicle_windows_state(adapter, vin):
    """ Tests that the MCP client can get the state of a vehicle via the windows API. """
    windows = adapter.get_windows_state(vin)
    assert windows is not None

    assert windows is not None
    assert windows.front_left is not None
    assert windows.front_left.open is not None
    assert windows.front_right is not None
    assert windows.front_right.open is not None
    assert windows.rear_left is not None
    assert windows.rear_left.open is not None
    assert windows.rear_right is not None
    assert windows.rear_right.open is not None


@pytest.mark.parametrize(
    "vin",
    [
        "WVWZZZED4SE003938",
    ],
)
async def test_mcp_get_vehicle_tyres_state(adapter, vin):
    """ Tests that the MCP client can get the state of a vehicle via the tyres API. """
    tyres = adapter.get_tyres_state(vin)
    assert tyres is not None

    assert tyres.front_left is not None
    assert tyres.front_left.pressure is not None
    assert tyres.front_left.temperature is not None
    assert tyres.front_right is not None
    assert tyres.front_right.pressure is not None
    assert tyres.front_right.temperature is not None
    assert tyres.rear_left is not None
    assert tyres.rear_left.pressure is not None
    assert tyres.rear_left.temperature is not None
    assert tyres.rear_right is not None
    assert tyres.rear_right.pressure is not None
    assert tyres.rear_right.temperature is not None