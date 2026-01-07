"""Adapter that wires the carconnectivity library into the generic MCP server.

Adapters should implement a small surface used by the MCP server. Types
are annotated so the server can rely on concrete return types.
"""

from abc import ABC, abstractmethod
from carconnectivity.vehicle import GenericVehicle
from pydantic import BaseModel



class AbstractAdapter(ABC):
    @abstractmethod
    def shutdown(self) -> None:
        """Perform any cleanup required by the adapter."""

    @abstractmethod
    def list_vehicles(self) -> list[str]:
        """Return a list of vehicle dicts. Each dict should include an 'id' key."""
        pass


    @abstractmethod
    def get_vehicle(self, vehicle_id: str) -> Optional[BaseModel]:
        """Return the vehicle dict for the given vehicle_id.

        If the vehicle is not found, return a dict with an 'error' key.
        """
        pass