# AI Instructions for WeConnect MCP Server

Volkswagen WeConnect vehicle data access via MCP.

## WORKFLOW

1. Start with `list_vehicles` to discover available vehicles
2. Identify vehicles by name (preferred), VIN, or license plate in all subsequent calls
3. Use specific tools based on user needs

## VEHICLE IDENTIFICATION

- **Preferred**: Use vehicle name (e.g., "Golf", "ID.4")
- **Alternative**: VIN or license plate
- **System automatically resolves all three formats**

## AVAILABLE TOOLS

### Core Information

- `list_vehicles`: Discover all vehicles with VIN, name, model, license plate
- `get_vehicle_info`: Basic info (manufacturer, model, software version, year, odometer, connection state)
- `get_vehicle_state`: Complete state snapshot (all systems combined)
- `get_vehicle_type`: Vehicle type (electric/BEV, combustion, hybrid/PHEV)

### Physical Components

- `get_vehicle_doors`: Lock status and open/closed state for all doors
- `get_vehicle_windows`: Open/closed status for all windows
- `get_vehicle_tyres`: Pressure and temperature readings
- `get_lights_state`: Left/right light status (safety check)

### Energy & Range (vehicle-type aware)

- `get_range_info`: Total range + electric/combustion breakdown with battery/tank levels
- `get_battery_status`: Quick check for electric vehicles (level, range, charging)
- `get_charging_state`: Detailed charging info (power, time, cable status, target SOC)
  - Only for BEV/PHEV vehicles
  - Includes: is_charging, is_plugged_in, charging_power_kw, remaining_time_minutes

### Climate & Comfort

- `get_climatization_state`: Heating/cooling status, target temp, estimated time
  - States: off, heating, cooling, ventilation
  - Settings: window heating, seat heating, unlock behavior
- `get_window_heating_state`: Front/rear window heating status

### Maintenance & Service

- `get_maintenance_info`: Service schedules
  - Inspection due date and distance
  - Oil service due date and distance (combustion/hybrid only)

### Location

- `get_position`: GPS coordinates (lat, lon) and heading (0°=N, 90°=E, 180°=S, 270°=W)

### Vehicle Control Commands

- `lock_vehicle`: Lock all doors
- `unlock_vehicle`: Unlock all doors
- `start_climatization`: Start pre-heating/cooling
- `stop_climatization`: Stop pre-heating/cooling
- `start_charging`: Start charging session (BEV/PHEV only)
- `stop_charging`: Stop charging session (BEV/PHEV only)
- `flash_lights`: Flash headlights (with optional duration)
- `honk_and_flash`: Honk horn and flash lights (with optional duration)
- `start_window_heating`: Activate window heating
- `stop_window_heating`: Deactivate window heating

## USAGE PATTERNS

### Quick Status Check

1. `list_vehicles`
2. `get_battery_status` (electric) or `get_range_info` (all types)
3. `get_vehicle_doors` (security check)

### Full Status Report

1. `list_vehicles`
2. `get_vehicle_state` (comprehensive)
3. Optionally drill down with specific tools

### Charging Session

1. `get_charging_state` (detailed charging info)
2. `get_battery_status` (quick overview)

### Remote Climate Control

1. `get_climatization_state` (check current status)
2. `start_climatization` (pre-heat/cool)
3. `get_climatization_state` (verify activation)

### Vehicle Security

1. `get_vehicle_doors` (check lock status)
2. `lock_vehicle` or `unlock_vehicle` (as needed)
3. `get_vehicle_doors` (verify action)
4. `get_climatization_state` (check if using external power)

### Pre-Trip Check

1. `get_range_info` (sufficient range?)
2. `get_vehicle_doors` (all closed and locked?)
3. `get_vehicle_tyres` (pressure OK?)
4. `get_lights_state` (any lights left on?)

### Maintenance Planning

1. `get_maintenance_info` (when is service due?)
2. `get_vehicle_info` (current odometer reading)

## BEST PRACTICES

- Always start with `list_vehicles` to get correct identifiers
- Use vehicle names for better readability
- For electric vehicles, prefer `get_battery_status` for quick checks
- For detailed charging analysis, use `get_charging_state`
- Check `get_vehicle_type` first if vehicle type is unknown
- Combine tools for comprehensive reports (e.g., battery + doors + climate)

## ERROR HANDLING

- Tools return `{"error": "..."}` if vehicle not found
- BEV/PHEV-only tools return errors for combustion vehicles
- Always verify vehicle_id from `list_vehicles` first

## RESOURCES (alternative data access)

- `data://list_vehicles`: Direct vehicle list
- `data://state/{vehicle_id}`: Direct state access
