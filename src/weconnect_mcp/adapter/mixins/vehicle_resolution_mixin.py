"""Vehicle resolution mixin for adapter.

Provides methods to resolve vehicle identifiers (VIN, name, license plate)
to actual VIN for API calls.
"""

from typing import Optional


class VehicleResolutionMixin:
    """Mixin providing vehicle identifier resolution.
    
    Allows users to specify vehicles by VIN, name, or license plate.
    All identifiers are resolved to VIN for API calls.
    """
    
    def resolve_vehicle_id(self, vehicle_id: str) -> Optional[str]:
        """Resolve vehicle identifier (VIN, name, or license plate) to VIN.
        
        Args:
            vehicle_id: VIN, vehicle name, or license plate
            
        Returns:
            VIN if found, None otherwise
        """
        vehicles = self.list_vehicles()
        
        # Direct VIN match
        for vehicle in vehicles:
            if vehicle.vin == vehicle_id:
                return vehicle.vin
        
        # Name match (case-insensitive)
        for vehicle in vehicles:
            if vehicle.name and vehicle.name.lower() == vehicle_id.lower():
                return vehicle.vin
        
        # License plate match (case-insensitive)
        for vehicle in vehicles:
            if vehicle.license_plate and vehicle.license_plate.lower() == vehicle_id.lower():
                return vehicle.vin
        
        return None
