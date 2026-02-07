# Vehicle Type Detection Feature

## Overview

The MCP server now includes a dedicated tool to identify the type of vehicle (electric, combustion, hybrid, etc.).

## New Tool: `get_vehicle_type`

### Description
Get the type of a specific vehicle (e.g., electric, combustion, hybrid).

### Parameters
- `vehicle_id` (str): The VIN of the vehicle to query

### Returns
A dictionary with:
- `vehicle_id`: The VIN that was queried
- `type`: The vehicle type as a string

Common vehicle types:
- `'electric'`: Battery Electric Vehicle (BEV) - Zero emissions, fully electric
- `'combustion'`: Internal Combustion Engine vehicle - Traditional gasoline/diesel
- `'hybrid'`: Hybrid Electric Vehicle (HEV/PHEV) - Combines electric and combustion engines
- `'plugin_hybrid'`: Plug-in Hybrid - Can be charged from external power source

### Example Usage with Claude

You can ask Claude questions like:

```
"What type of vehicle is the T7?"
```

Claude will call:
```python
get_vehicle_type(vehicle_id="WV2ZZZSTZNH009136")
```

And respond with something like:
```
The T7 (Transporter 7) is an electric vehicle (BEV).
```

Other example questions:
- "Is the ID7 electric or combustion?"
- "Which of my vehicles are electric?"
- "Do I have any hybrid vehicles?"
- "What kind of engine does my car have?"

## Technical Implementation

### New Methods Added

#### AbstractAdapter
```python
def get_vehicle_type(self, vehicle_id: str) -> Optional[str]:
    """Return the vehicle type for the given vehicle_id.
    
    Returns the vehicle type as a string, e.g., 'electric', 'combustion', 'hybrid'.
    If the vehicle is not found, return None.
    """
```

#### CarConnectivityAdapter
```python
def get_vehicle_type(self, vehicle_id: str) -> Optional[str]:
    vehicle = self._get_vehicle_for_vin(vehicle_id)
    if vehicle is None:
        return None
    type_val = vehicle.type.value if vehicle.type is not None else None
    return type_val
```

### MCP Tool Registration

The tool is automatically registered in the MCP server and documented in the server instructions:

```python
@mcp.tool()
def get_vehicle_type(vehicle_id: str) -> Dict[str, Any]:
    """Get the type of a specific vehicle (e.g., electric, combustion, hybrid).
    
    Args:
        vehicle_id: The ID of the vehicle to query
        
    Returns:
        Vehicle type information
    """
    logger.info("get vehicle type for id=%s", vehicle_id)
    vehicle_type = adapter.get_vehicle_type(vehicle_id)
    if vehicle_type is None:
        logger.warning("Vehicle '%s' not found or type not available", vehicle_id)
        return {"error": f"Vehicle {vehicle_id} not found or type not available"}
    
    return {"vehicle_id": vehicle_id, "type": vehicle_type}
```

## Testing

Run the tests to verify the implementation:

```bash
# Test the adapter method
pytest tests/test_vehicle_type.py -v

# Test the full MCP server
pytest tests/test_mcp_server.py -v

# Run the demo
PYTHONPATH=/Users/simon/Coding/weconnect_mvp python examples/vehicle_type_demo.py
```

## Integration with Existing Tools

The vehicle type is also included in the complete vehicle state returned by `get_vehicle_state()`, so you can access it there as well. The dedicated `get_vehicle_type()` tool provides a lightweight way to query just this information without fetching the entire vehicle state.
