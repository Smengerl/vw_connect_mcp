"""Command execution mixin for adapter.

Provides vehicle control commands: lock, unlock, climatization, charging,
lights/horn, and window heating.
"""

import sys
import logging
from typing import Any, Optional

from carconnectivity.vehicle import GenericVehicle
from carconnectivity.command_impl import (
    LockUnlockCommand,
    ClimatizationStartStopCommand,
    ChargingStartStopCommand,
    HonkAndFlashCommand,
    WindowHeatingStartStopCommand,
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)


class CommandMixin:
    """Mixin providing vehicle control commands.
    
    All command methods follow the pattern:
    1. Get vehicle by ID
    2. Validate vehicle supports command
    3. Execute command
    4. Invalidate cache
    5. Return result dict
    """
    
    def lock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
        """Lock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
            return {"success": False, "error": "Vehicle does not support door commands"}
        
        if not vehicle.doors.commands.contains_command("lock-unlock"):
            return {"success": False, "error": "Vehicle does not support lock/unlock command"}
        
        try:
            vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.LOCK
            self.invalidate_cache()
            logger.info(f"Vehicle {vehicle_id} locked successfully, cache invalidated")
            return {"success": True, "message": "Vehicle locked"}
        except Exception as e:
            logger.error(f"Failed to lock vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def unlock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
        """Unlock the vehicle doors.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'doors') or vehicle.doors is None or vehicle.doors.commands is None:
            return {"success": False, "error": "Vehicle does not support door commands"}
        
        if not vehicle.doors.commands.contains_command("lock-unlock"):
            return {"success": False, "error": "Vehicle does not support lock/unlock command"}
        
        try:
            vehicle.doors.commands.commands["lock-unlock"].value = LockUnlockCommand.Command.UNLOCK
            self.invalidate_cache()
            logger.info(f"Vehicle {vehicle_id} unlocked successfully, cache invalidated")
            return {"success": True, "message": "Vehicle unlocked"}
        except Exception as e:
            logger.error(f"Failed to unlock vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_climatization(self, vehicle_id: str, target_temp_celsius: Optional[float] = None) -> dict[str, Any]:
        """Start climate control.
        
        Args:
            vehicle_id: VIN, name, or license plate
            target_temp_celsius: Optional target temperature in Celsius (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
            return {"success": False, "error": "Vehicle does not support climatization commands"}
        
        if not vehicle.climatization.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support climatization start/stop command"}
        
        try:
            # Build command dict with temperature if provided
            command_dict = {"command": ClimatizationStartStopCommand.Command.START}
            if target_temp_celsius is not None:
                command_dict["target_temperature"] = target_temp_celsius
                command_dict["target_temperature_unit"] = "C"  # Always use Celsius
            
            vehicle.climatization.commands.commands["start-stop"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Climatization started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Climatization started"}
        except Exception as e:
            logger.error(f"Failed to start climatization for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_climatization(self, vehicle_id: str) -> dict[str, Any]:
        """Stop climate control.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'climatization') or vehicle.climatization is None or vehicle.climatization.commands is None:
            return {"success": False, "error": "Vehicle does not support climatization commands"}
        
        if not vehicle.climatization.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support climatization start/stop command"}
        
        try:
            vehicle.climatization.commands.commands["start-stop"].value = ClimatizationStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Climatization stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Climatization stopped"}
        except Exception as e:
            logger.error(f"Failed to stop climatization for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_charging(self, vehicle_id: str) -> dict[str, Any]:
        """Start charging.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
            return {"success": False, "error": "Vehicle does not support charging commands"}
        
        if not vehicle.charging.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support charging start/stop command"}
        
        try:
            vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.START
            self.invalidate_cache()
            logger.info(f"Charging started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Charging started"}
        except Exception as e:
            logger.error(f"Failed to start charging for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_charging(self, vehicle_id: str) -> dict[str, Any]:
        """Stop charging.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'charging') or vehicle.charging is None or vehicle.charging.commands is None:
            return {"success": False, "error": "Vehicle does not support charging commands"}
        
        if not vehicle.charging.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support charging start/stop command"}
        
        try:
            vehicle.charging.commands.commands["start-stop"].value = ChargingStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Charging stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Charging stopped"}
        except Exception as e:
            logger.error(f"Failed to stop charging for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def flash_lights(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> dict[str, Any]:
        """Flash the vehicle lights.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
            return {"success": False, "error": "Vehicle does not support control commands"}
        
        if not vehicle.controls.commands.contains_command("honk-and-flash"):
            return {"success": False, "error": "Vehicle does not support honk/flash command"}
        
        try:
            # Build command dict with duration if provided
            command_dict = {"command": HonkAndFlashCommand.Command.FLASH}
            if duration_seconds is not None:
                command_dict["duration"] = duration_seconds
            
            vehicle.controls.commands.commands["honk-and-flash"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Lights flashed for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Lights flashed"}
        except Exception as e:
            logger.error(f"Failed to flash lights for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def honk_and_flash(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> dict[str, Any]:
        """Honk and flash the vehicle.
        
        Args:
            vehicle_id: VIN, name, or license plate
            duration_seconds: Optional duration in seconds (if supported by vehicle)
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'controls') or vehicle.controls is None or vehicle.controls.commands is None:
            return {"success": False, "error": "Vehicle does not support control commands"}
        
        if not vehicle.controls.commands.contains_command("honk-and-flash"):
            return {"success": False, "error": "Vehicle does not support honk/flash command"}
        
        try:
            # Build command dict with duration if provided
            command_dict = {"command": HonkAndFlashCommand.Command.HONK_AND_FLASH}
            if duration_seconds is not None:
                command_dict["duration"] = duration_seconds
            
            vehicle.controls.commands.commands["honk-and-flash"].value = command_dict
            self.invalidate_cache()
            logger.info(f"Honk and flash executed for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Honk and flash executed"}
        except Exception as e:
            logger.error(f"Failed to honk and flash for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def start_window_heating(self, vehicle_id: str) -> dict[str, Any]:
        """Start window heating.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
            return {"success": False, "error": "Vehicle does not support window heating commands"}
        
        if not vehicle.window_heating.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support window heating start/stop command"}
        
        try:
            vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.START
            self.invalidate_cache()
            logger.info(f"Window heating started for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Window heating started"}
        except Exception as e:
            logger.error(f"Failed to start window heating for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_window_heating(self, vehicle_id: str) -> dict[str, Any]:
        """Stop window heating.
        
        Args:
            vehicle_id: VIN, name, or license plate
            
        Returns:
            Result dict with success/error status
        """
        vehicle = self._get_vehicle_for_vin(vehicle_id)
        if vehicle is None:
            return {"success": False, "error": f"Vehicle {vehicle_id} not found"}
        
        if not hasattr(vehicle, 'window_heating') or vehicle.window_heating is None or vehicle.window_heating.commands is None:
            return {"success": False, "error": "Vehicle does not support window heating commands"}
        
        if not vehicle.window_heating.commands.contains_command("start-stop"):
            return {"success": False, "error": "Vehicle does not support window heating start/stop command"}
        
        try:
            vehicle.window_heating.commands.commands["start-stop"].value = WindowHeatingStartStopCommand.Command.STOP
            self.invalidate_cache()
            logger.info(f"Window heating stopped for vehicle {vehicle_id}, cache invalidated")
            return {"success": True, "message": "Window heating stopped"}
        except Exception as e:
            logger.error(f"Failed to stop window heating for vehicle {vehicle_id}: {e}")
            return {"success": False, "error": str(e)}
