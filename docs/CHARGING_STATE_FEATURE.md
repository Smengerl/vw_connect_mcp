# Charging State Feature

## Overview

The MCP server now includes a dedicated tool to query the current charging status of electric and plug-in hybrid vehicles.

## New Tool: `get_charging_state`

### Description
Get detailed charging information for electric (BEV) and plug-in hybrid (PHEV) vehicles.

### Parameters
- `vehicle_id` (str): The VIN of the vehicle to query

### Returns
A `ChargingModel` object with detailed charging information:

```python
{
    "is_charging": bool,              # True if currently charging
    "is_plugged_in": bool,            # True if charging cable is connected
    "charging_power_kw": float,       # Current charging power in kilowatts
    "charging_state": str,            # Current state (charging, ready, off, error)
    "remaining_time_minutes": int,    # Estimated minutes until fully charged
    "target_soc_percent": int,        # Target state of charge percentage
    "current_soc_percent": float,     # Current battery level percentage
    "charge_mode": str                # Charging mode (manual, timer, etc.)
}
```

### Example Response

```json
{
  "is_charging": true,
  "is_plugged_in": true,
  "charging_power_kw": 11.0,
  "charging_state": "charging",
  "remaining_time_minutes": 45,
  "target_soc_percent": 90,
  "current_soc_percent": 77.0,
  "charge_mode": "manual"
}
```

### Charging States

- `charging`: Vehicle is actively charging
- `ready`: Vehicle is plugged in and ready to charge
- `off`: Charging is off (not plugged in)
- `error`: There's an error with the charging system

### Example Usage with Claude

You can ask Claude questions like:

```
"Is the ID7 currently charging?"
```

Claude will call:
```python
get_charging_state(vehicle_id="WVWZZZED4SE003938")
```

And respond with something like:
```
Yes, the ID7 is currently charging at 11 kW. 
It's at 77% battery and will reach the target of 90% in about 45 minutes.
```

Other example questions:
- "When will my car finish charging?"
- "What's the battery level of the ID7?"
- "Is my electric car plugged in?"
- "How fast is the ID7 charging?"
- "Show me the charging status of all my vehicles"

## Technical Implementation

### ChargingModel (Data Model)

```python
class ChargingModel(BaseModel):
    """Detailed charging information for electric/hybrid vehicles"""
    is_charging: Optional[bool] = None
    is_plugged_in: Optional[bool] = None
    charging_power_kw: Optional[float] = None
    charging_state: Optional[str] = None
    remaining_time_minutes: Optional[int] = None
    target_soc_percent: Optional[int] = None
    current_soc_percent: Optional[float] = None
    charge_mode: Optional[str] = None
```

### AbstractAdapter

```python
@abstractmethod
def get_charging_state(self, vehicle_id: str) -> Optional[ChargingModel]:
    """Return the charging state for the given vehicle_id.
    
    Returns detailed charging information if the vehicle supports it (BEV/PHEV).
    If the vehicle is not found or doesn't support charging, return None.
    """
    pass
```

### CarConnectivityAdapter

The `CarConnectivityAdapter` implementation extracts charging information from the `carconnectivity` library:

```python
def get_charging_state(self, vehicle_id: str) -> Optional[ChargingModel]:
    vehicle = self._get_vehicle_for_vin(vehicle_id)
    if vehicle is None:
        return None
    
    # Only electric and hybrid vehicles have charging capability
    if not isinstance(vehicle, ElectricVehicle):
        return None
    
    # Extract charging information from vehicle.charging
    charging = getattr(vehicle, 'charging', None)
    if charging is None:
        return None
    
    # ... extract and map charging data ...
    
    return ChargingModel(...)
```

### MCP Tool Registration

```python
@mcp.tool()
def get_charging_state(vehicle_id: str) -> Dict[str, Any]:
    """Get the current charging status of an electric or hybrid vehicle.
    
    Args:
        vehicle_id: The ID of the vehicle to query
        
    Returns:
        Detailed charging information
        
    Note: Only available for electric (BEV) and plug-in hybrid (PHEV) vehicles.
    """
    logger.info("get charging state for id=%s", vehicle_id)
    charging_state = adapter.get_charging_state(vehicle_id)
    if charging_state is None:
        logger.warning("Vehicle '%s' not found or doesn't support charging", vehicle_id)
        return {"error": f"Vehicle {vehicle_id} not found or doesn't support charging"}
    
    return charging_state.model_dump()
```

## Data Sources

The implementation extracts data from the `carconnectivity` library:

- **Charging State**: From `vehicle.charging.state` enum
- **Plug Status**: From `vehicle.charging.connector.connection_state`
- **Charging Power**: From `vehicle.charging.power` (in kW)
- **Completion Time**: Calculated from `vehicle.charging.estimated_date_reached`
- **Target SOC**: From `vehicle.charging.settings.target_level`
- **Current SOC**: From `vehicle.battery.level`

## Testing

Run the tests to verify the implementation:

```bash
# Test the charging state functionality
pytest tests/test_charging_state.py -v

# Test the full MCP server
pytest tests/test_mcp_server.py -v

# Run the demo
PYTHONPATH=/Users/simon/Coding/weconnect_mvp python examples/charging_state_demo.py
```

## Limitations

- Only available for electric (BEV) and plug-in hybrid (PHEV) vehicles
- Returns `None` for combustion engine vehicles
- Charging time estimate depends on vehicle providing this information
- Some fields may be `None` if the vehicle doesn't provide that specific data

## Integration with Existing Tools

The charging state complements existing tools:

- Use `get_vehicle_type()` first to check if the vehicle supports charging
- Use `get_vehicle_state()` for a complete overview including charging (if available)
- Use `get_charging_state()` for detailed, focused charging information

## Example Workflow

```python
# 1. Check vehicle type
vehicle_type = get_vehicle_type(vin)

# 2. If electric/hybrid, get charging details
if vehicle_type in ['electric', 'hybrid', 'plugin_hybrid']:
    charging = get_charging_state(vin)
    
    if charging and charging.is_charging:
        print(f"Charging at {charging.charging_power_kw} kW")
        print(f"Will be ready in {charging.remaining_time_minutes} minutes")
```
