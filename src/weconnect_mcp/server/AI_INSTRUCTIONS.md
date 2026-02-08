# AI Instructions for WeConnect MCP Server# AI Instructions for WeConnect MCP Server# AI Instructions for WeConnect MCP Ser## AVAILABLE RESOURCES (Read-Only Data)



Volkswagen WeConnect vehicle data access via MCP.



## ⚠️ IMPORTANT: VW API LIMITATION - LICENSE PLATESVolkswagen WeConnect vehicle data access via MCP.All resources are cached server-side for 5 minutes to avoid VW API rate limits. Cache is automatically invalidated after any control command.



**As of February 2026, the VW WeConnect API does NOT provide license plate information.**



This is a current limitation of Volkswagen's official API, not a limitation of this MCP server or the carconnectivity library. The API returns `null`/`None` for the `license_plate` field for all vehicles, regardless of whether a license plate is registered in the VW account.## IMPORTANT: HOW TO ACCESS DATA**Access method**: Use MCP `resources/read` operation with the resource URI below.



**What this means:**

- `get_vehicles()` will return `license_plate: null` for all vehicles

- You cannot search or filter vehicles by license plate**All vehicle data is available through TOOLS.**### Vehicle List

- License plates shown in test data are for demonstration purposes only

- This may change if VW updates their API in the future



## IMPORTANT: HOW TO ACCESS DATAUse these tools to read vehicle data:- **URI**: `data://vehicles`



**All vehicle data is available through TOOLS.**- `get_vehicles()` - List all available vehicles (start here!)- **Description**: List all vehicles with VIN, name, model, and license plate



Use these tools to read vehicle data:- `get_vehicle_info(vehicle_id)` - Basic vehicle information- **Parameters**: None

- `get_vehicles()` - List all available vehicles (start here!)

- `get_vehicle_info(vehicle_id)` - Basic vehicle information- `get_vehicle_state(vehicle_id)` - Complete vehicle state snapshot- **Example**: `resources/read("data://vehicles")`

- `get_vehicle_state(vehicle_id)` - Complete vehicle state snapshot

- `get_battery_status(vehicle_id)` - Battery status (BEV/PHEV only)- `get_battery_status(vehicle_id)` - Battery status (BEV/PHEV only)

- `get_charging_status(vehicle_id)` - Detailed charging info (BEV/PHEV only)

- `get_climate_status(vehicle_id)` - Climate control status- `get_charging_status(vehicle_id)` - Detailed charging info (BEV/PHEV only)### Vehicle Information

- `get_vehicle_doors(vehicle_id)` - Door lock/open status

- `get_vehicle_position(vehicle_id)` - GPS coordinates and heading- `get_climate_status(vehicle_id)` - Climate control status



## ARCHITECTURE- `get_vehicle_doors(vehicle_id)` - Door lock/open status- **URI**: `data://vehicle/{vehicle_id}/info`



This server provides:- `get_vehicle_position(vehicle_id)` - GPS coordinates and heading- **Description**: Basic info (manufacturer, model, software version, year, odometer, connection state)

- **Read Tools**: Access vehicle data (cached server-side for 5 minutes to respect VW API rate limits)

- **Control Tools**: Vehicle control commands (write operations that invalidate cache)- **Parameters**: `vehicle_id` - Vehicle name, VIN, or license plate



## WORKFLOW## ARCHITECTURE- **Example**: `resources/read("data://vehicle/Golf/info")`



1. **List vehicles first**: Call `get_vehicles()` to discover available vehicles

2. Identify vehicles by **name or VIN** in subsequent tool calls (NOT license plate - see limitation above)

3. Use read tools (get_*) for reading dataThis server provides:- **URI**: `data://vehicle/{vehicle_id}/state`

4. Use control tools (start_*/stop_*/lock_*/unlock_*) for vehicle control

- **Read Tools**: Access vehicle data (cached server-side for 5 minutes to respect VW API rate limits)- **Description**: Complete state snapshot (all systems combined)

## VEHICLE IDENTIFICATION

- **Control Tools**: Vehicle control commands (write operations that invalidate cache)

- **Preferred**: Use vehicle name (e.g., "Golf", "ID.7", "T7")

- **Alternative**: VIN (e.g., "WVWZZZED4SE003938")- **URI**: `data://vehicle/{vehicle_id}/type`

- **NOT AVAILABLE**: License plate (VW API does not provide this data)

- **System automatically resolves both name and VIN formats**## WORKFLOW- **Description**: Vehicle type (electric/BEV, combustion, hybrid/PHEV)en WeConnect vehicle data access via MCP.



## AVAILABLE READ TOOLS



All read tools return JSON data. Data is cached server-side for 5 minutes. Cache is automatically invalidated after any control command.1. **List vehicles first**: Call `get_vehicles()` to discover available vehicles## ARCHITECTURE



### Discovery & Overview2. Identify vehicles by name (preferred), VIN, or license plate in subsequent tool calls



**`get_vehicles()`**3. Use read tools (get_*) for reading dataThis server provides:

- Returns: List of all vehicles with VIN, name, model (license_plate will be null)

- Example: `get_vehicles()`4. Use control tools (start_*/stop_*/lock_*/unlock_*) for vehicle control- **Resources**: Read-only data access (cached server-side for 5 minutes to respect VW API rate limits)

- Use this first to discover available vehicles

- Note: license_plate field will always be null due to VW API limitation  - Use `resources/read` with the resource URI to access data



**`get_vehicle_info(vehicle_id)`**## VEHICLE IDENTIFICATION  - Resource URIs use the format `data://vehicles` or `data://vehicle/{vehicle_id}/...`

- Returns: Basic info (manufacturer, model, software version, year, odometer, connection state)

- Example: `get_vehicle_info("Golf")`- **Tools**: Vehicle control commands (write operations that invalidate cache)



**`get_vehicle_state(vehicle_id)`**- **Preferred**: Use vehicle name (e.g., "Golf", "ID.7")

- Returns: Complete state snapshot (all systems combined)

- Example: `get_vehicle_state("Golf")`- **Alternative**: VIN or license plate## WORKFLOW

- Use for comprehensive overview

- **System automatically resolves all three formats**

### Physical Components

1. **List vehicles first**: Use `resources/read` with URI `data://vehicles` to discover available vehicles

**`get_vehicle_doors(vehicle_id)`**

- Returns: Lock status and open/closed state for all doors## AVAILABLE READ TOOLS2. Identify vehicles by name (preferred), VIN, or license plate in all subsequent calls

- Example: `get_vehicle_doors("Golf")`

3. Use `resources/read` with appropriate URIs for reading data

### Energy & Range

All read tools return JSON data. Data is cached server-side for 5 minutes. Cache is automatically invalidated after any control command.4. Use tools for controlling the vehicle

**`get_battery_status(vehicle_id)`**

- Returns: Battery level, electric range, charging status

- Vehicle types: BEV/PHEV only

- Example: `get_battery_status("ID.7")`### Discovery & Overview## HOW TO USE RESOURCES

- Use for quick battery check



**`get_charging_status(vehicle_id)`**

- Returns: Detailed charging info (power, remaining time, cable status, target SOC)**`get_vehicles()`**Resources provide read-only data access through the MCP protocol. To access a resource:

- Vehicle types: BEV/PHEV only

- Example: `get_charging_status("ID.7")`- Returns: List of all vehicles with VIN, name, model, and license plate

- Use for detailed charging analysis

- Example: `get_vehicles()`**Method**: Use the MCP `resources/read` operation with the resource URI

### Climate & Comfort

- Use this first to discover available vehicles

**`get_climate_status(vehicle_id)`**

- Returns: Climate control state, target temperature, estimated time**Example URIs**:

- States: off, heating, cooling, ventilation

- Example: `get_climate_status("Golf")`**`get_vehicle_info(vehicle_id)`**- `data://vehicles` - List all vehicles (no parameters needed)



### Location- Returns: Basic info (manufacturer, model, software version, year, odometer, connection state)- `data://vehicle/Golf/battery` - Battery status for vehicle named "Golf"



**`get_vehicle_position(vehicle_id)`**- Example: `get_vehicle_info("Golf")`- `data://vehicle/WVWZZZAUZPW123456/doors` - Doors status using VIN

- Returns: GPS coordinates (lat, lon) and heading (0°=N, 90°=E, 180°=S, 270°=W)

- Example: `get_vehicle_position("Golf")`- `data://vehicle/B-AB-1234/climate` - Climate status using license plate



## AVAILABLE CONTROL TOOLS**`get_vehicle_state(vehicle_id)`**



Control tools modify vehicle state and automatically invalidate the cache to ensure fresh data on next read.- Returns: Complete state snapshot (all systems combined)**Note**: All vehicle-specific resources require a `{vehicle_id}` parameter in the URI. Replace `{vehicle_id}` with the actual vehicle identifier (name, VIN, or license plate).



### Door Control- Example: `get_vehicle_state("Golf")`



**`lock_vehicle(vehicle_id)`**- Use for comprehensive overview## VEHICLE IDENTIFICATION

- Action: Lock all doors

- Example: `lock_vehicle("Golf")`



**`unlock_vehicle(vehicle_id)`**### Physical Components- **Preferred**: Use vehicle name (e.g., "Golf", "ID.4")

- Action: Unlock all doors

- Example: `unlock_vehicle("Golf")`- **Alternative**: VIN or license plate



### Climate Control**`get_vehicle_doors(vehicle_id)`**- **System automatically resolves all three formats**



**`start_climatization(vehicle_id, target_temperature_celsius=None)`**- Returns: Lock status and open/closed state for all doors

- Action: Start pre-heating/cooling

- Optional: Set target temperature (otherwise uses last setting)- Example: `get_vehicle_doors("Golf")`## AVAILABLE RESOURCES (Read-Only Data)

- Example: `start_climatization("Golf", 22.0)`



**`stop_climatization(vehicle_id)`**

- Action: Stop pre-heating/cooling### Energy & RangeAll resources are cached server-side for 5 minutes to avoid VW API rate limits. Cache is automatically invalidated after any control command.

- Example: `stop_climatization("Golf")`



**`start_window_heating(vehicle_id)`**

- Action: Activate window heating/defrosting**`get_battery_status(vehicle_id)`**### Vehicle List

- Example: `start_window_heating("Golf")`

- Returns: Battery level, electric range, charging status

**`stop_window_heating(vehicle_id)`**

- Action: Deactivate window heating- Vehicle types: BEV/PHEV only- `data://vehicles`: List all vehicles with VIN, name, model, license plate

- Example: `stop_window_heating("Golf")`

- Example: `get_battery_status("ID.7")`

### Charging Control (BEV/PHEV only)

- Use for quick battery check### Vehicle Information

**`start_charging(vehicle_id)`**

- Action: Start charging session (vehicle must be plugged in)

- Example: `start_charging("ID.7")`

**`get_charging_status(vehicle_id)`**- `data://vehicle/{vehicle_id}/info`: Basic info (manufacturer, model, software version, year, odometer, connection state)

**`stop_charging(vehicle_id)`**

- Action: Stop charging session- Returns: Detailed charging info (power, remaining time, cable status, target SOC)- `data://vehicle/{vehicle_id}/state`: Complete state snapshot (all systems combined)

- Example: `stop_charging("ID.7")`

- Vehicle types: BEV/PHEV only- `data://vehicle/{vehicle_id}/type`: Vehicle type (electric/BEV, combustion, hybrid/PHEV)

### Locator Features

- Example: `get_charging_status("ID.7")`

**`flash_lights(vehicle_id, duration_seconds=None)`**

- Action: Flash headlights- Use for detailed charging analysis### Physical Components

- Optional: Duration in seconds

- Example: `flash_lights("Golf", 10)`



**`honk_and_flash(vehicle_id, duration_seconds=None)`**### Climate & Comfort- **URI**: `data://vehicle/{vehicle_id}/doors`

- Action: Honk horn and flash lights

- Optional: Duration in seconds- **Description**: Lock status and open/closed state for all doors

- Example: `honk_and_flash("Golf", 5)`

**`get_climate_status(vehicle_id)`**

## USAGE PATTERNS

- Returns: Climate control state, target temperature, estimated time- **URI**: `data://vehicle/{vehicle_id}/windows`

### Quick Status Check

- States: off, heating, cooling, ventilation- **Description**: Open/closed status for all windows

1. `get_vehicles()` - discover vehicles

2. `get_battery_status("Golf")` - electric, or `get_vehicle_state("Golf")` - all types- Example: `get_climate_status("Golf")`

3. `get_vehicle_doors("Golf")` - security check

- **URI**: `data://vehicle/{vehicle_id}/tyres`

### Full Status Report

### Location- **Description**: Pressure and temperature readings

1. `get_vehicles()` - discover vehicles

2. `get_vehicle_state("Golf")` - comprehensive snapshot

3. Optionally use specific tools for detailed data

**`get_vehicle_position(vehicle_id)`**- **URI**: `data://vehicle/{vehicle_id}/lights`

### Charging Session

- Returns: GPS coordinates (lat, lon) and heading (0°=N, 90°=E, 180°=S, 270°=W)- **Description**: Left/right light status (safety check)

1. `get_charging_status("ID.7")` - detailed charging info

2. `get_battery_status("ID.7")` - quick overview- Example: `get_vehicle_position("Golf")`

3. Use `start_charging("ID.7")` or `stop_charging("ID.7")` to control

### Energy & Range (vehicle-type aware)

### Remote Climate Control

## AVAILABLE CONTROL TOOLS

1. `get_climate_status("Golf")` - check current status

2. `start_climatization("Golf", 22.0)` - pre-heat/cool to 22°C- **URI**: `data://vehicle/{vehicle_id}/range`

3. `get_climate_status("Golf")` - verify activation (cache auto-refreshed after command)

Control tools modify vehicle state and automatically invalidate the cache to ensure fresh data on next read.- **Description**: Total range + electric/combustion breakdown with battery/tank levels

### Vehicle Security



1. `get_vehicle_doors("Golf")` - check lock status

2. `lock_vehicle("Golf")` or `unlock_vehicle("Golf")` - as needed### Door Control- **URI**: `data://vehicle/{vehicle_id}/battery`

3. `get_vehicle_doors("Golf")` - verify action (cache auto-refreshed after command)

- **Description**: Quick check for electric vehicles (level, range, charging)

### Pre-Trip Check

**`lock_vehicle(vehicle_id)`**

1. `get_battery_status("ID.7")` - sufficient charge?

2. `get_vehicle_doors("Golf")` - all closed and locked?- Action: Lock all doors- **URI**: `data://vehicle/{vehicle_id}/charging`

3. `get_vehicle_position("Golf")` - where is the vehicle?

- Example: `lock_vehicle("Golf")`- **Description**: Detailed charging info (power, time, cable status, target SOC)

### Find Vehicle in Parking Lot

  - Only for BEV/PHEV vehicles

1. `get_vehicle_position("Golf")` - get GPS coordinates

2. `flash_lights("Golf", 10)` - flash lights for 10 seconds**`unlock_vehicle(vehicle_id)`**  - Includes: is_charging, is_plugged_in, charging_power_kw, remaining_time_minutes

3. Or: `honk_and_flash("Golf", 5)` - honk and flash for 5 seconds

- Action: Unlock all doors

## BEST PRACTICES

- Example: `unlock_vehicle("Golf")`### Climate & Comfort

- **Always start** with `get_vehicles()` to discover available vehicles

- **Use vehicle names** for better readability (e.g., "Golf" instead of VIN)

- **Cannot use license plates** to identify vehicles (VW API limitation)

- **For electric vehicles**, use `get_battery_status()` for quick checks### Climate Control- **URI**: `data://vehicle/{vehicle_id}/climate`

- **For detailed charging analysis**, use `get_charging_status()`

- **Data is cached** for 5 minutes - cache automatically refreshes after any control command- **Description**: Heating/cooling status, target temp, estimated time

- **Combine read tools** for comprehensive reports

- **Vehicle identifiers**: name or VIN (license plate NOT supported)**`start_climatization(vehicle_id, target_temperature_celsius=None)`**  - States: off, heating, cooling, ventilation



## ERROR HANDLING- Action: Start pre-heating/cooling  - Settings: window heating, seat heating, unlock behavior



- Tools return `{"error": "..."}` JSON if vehicle not found or data unavailable- Optional: Set target temperature (otherwise uses last setting)

- BEV/PHEV-only tools return errors for combustion vehicles

- Always verify vehicle exists with `get_vehicles()` first- Example: `start_climatization("Golf", 22.0)`- **URI**: `data://vehicle/{vehicle_id}/window-heating`

- Control tools return error dictionaries if operation fails

- If vehicle cannot be found by name, try using the VIN instead- **Description**: Front/rear window heating status



## CACHING BEHAVIOR**`stop_climatization(vehicle_id)`**



- All read tools access cached data (5 minutes / 300 seconds)- Action: Stop pre-heating/cooling### Maintenance & Service

- Cache prevents excessive VW API calls and respects rate limits

- **Cache is automatically invalidated** after any control tool executes- Example: `stop_climatization("Golf")`

- Next read tool call after a control command will fetch fresh data from VW servers

- No manual cache management needed- **URI**: `data://vehicle/{vehicle_id}/maintenance`



## KNOWN LIMITATIONS**`start_window_heating(vehicle_id)`**- **Description**: Service schedules



### VW API Limitations (not fixable by this server)- Action: Activate window heating/defrosting  - Inspection due date and distance



1. **No License Plate Data** (as of February 2026)- Example: `start_window_heating("Golf")`  - Oil service due date and distance (combustion/hybrid only)

   - The VW API does not provide license plate information

   - All vehicles will show `license_plate: null`

   - Use vehicle name or VIN for identification instead

**`stop_window_heating(vehicle_id)`**### Location

2. **Rate Limiting**

   - VW API has rate limits (handled by 5-minute cache)- Action: Deactivate window heating

   - Too many requests may be temporarily blocked

- Example: `stop_window_heating("Golf")`- **URI**: `data://vehicle/{vehicle_id}/position`

3. **Token Expiration**

   - After several hours, re-authentication is required- **Description**: GPS coordinates (lat, lon) and heading (0°=N, 90°=E, 180°=S, 270°=W)

   - Server will automatically re-authenticate when needed

### Charging Control (BEV/PHEV only)

4. **API Availability**

   - VW servers can be temporarily unavailable## AVAILABLE TOOLS (Vehicle Control Commands)

   - First connection after server start can take 10-30 seconds

**`start_charging(vehicle_id)`**

## EXAMPLES

- Action: Start charging session (vehicle must be plugged in)Tools modify vehicle state and automatically invalidate the cache to ensure fresh data on next read.

```python

# Discover vehicles- Example: `start_charging("ID.7")`

get_vehicles()

# Returns: [{"vin": "...", "name": "Golf", "model": "Golf 8", "license_plate": null}, ...]### Door Control

# Note: license_plate will always be null due to VW API limitation

**`stop_charging(vehicle_id)`**

# Check battery

get_battery_status("Golf")- Action: Stop charging session- `lock_vehicle`: Lock all doors

# Returns: {"battery_level_percent": 85, "range_km": 320, "is_charging": false}

- Example: `stop_charging("ID.7")`- `unlock_vehicle`: Unlock all doors

# Start climate control

start_climatization("Golf", 22.0)

# Returns: {"success": true, "message": "Climatization started"}

### Locator Features### Climate Control

# Verify climate is running

get_climate_status("Golf")

# Returns: {"state": "heating", "target_temperature_celsius": 22.0, ...}

**`flash_lights(vehicle_id, duration_seconds=None)`**- `start_climatization`: Start pre-heating/cooling

# Lock vehicle

lock_vehicle("Golf")- Action: Flash headlights- `stop_climatization`: Stop pre-heating/cooling

# Returns: {"success": true, "message": "Vehicle locked"}

- Optional: Duration in seconds- `start_window_heating`: Activate window heating

# Verify doors are locked

get_vehicle_doors("Golf")- Example: `flash_lights("Golf", 10)`- `stop_window_heating`: Deactivate window heating

# Returns: {"lock_status": "locked", "front_left": "closed", ...}

```


**`honk_and_flash(vehicle_id, duration_seconds=None)`**### Charging Control (BEV/PHEV only)

- Action: Honk horn and flash lights

- Optional: Duration in seconds- `start_charging`: Start charging session

- Example: `honk_and_flash("Golf", 5)`- `stop_charging`: Stop charging session



## USAGE PATTERNS### Locator Features



### Quick Status Check- `flash_lights`: Flash headlights (with optional duration)

- `honk_and_flash`: Honk horn and flash lights (with optional duration)

1. `get_vehicles()` - discover vehicles

2. `get_battery_status("Golf")` - electric, or `get_vehicle_state("Golf")` - all types## USAGE PATTERNS

3. `get_vehicle_doors("Golf")` - security check

### Quick Status Check

### Full Status Report

1. `resources/read("data://vehicles")` - discover vehicles

1. `get_vehicles()` - discover vehicles2. `resources/read("data://vehicle/Golf/battery")` - electric, or `resources/read("data://vehicle/Golf/range")` - all types

2. `get_vehicle_state("Golf")` - comprehensive snapshot3. `resources/read("data://vehicle/Golf/doors")` - security check

3. Optionally use specific tools for detailed data

### Full Status Report

### Charging Session

1. `resources/read("data://vehicles")` - discover vehicles

1. `get_charging_status("ID.7")` - detailed charging info2. `resources/read("data://vehicle/Golf/state")` - comprehensive snapshot

2. `get_battery_status("ID.7")` - quick overview3. Optionally drill down with specific resource URIs

3. Use `start_charging("ID.7")` or `stop_charging("ID.7")` to control

### Charging Session

### Remote Climate Control

1. `resources/read("data://vehicle/Golf/charging")` - detailed charging info

1. `get_climate_status("Golf")` - check current status2. `resources/read("data://vehicle/Golf/battery")` - quick overview

2. `start_climatization("Golf", 22.0)` - pre-heat/cool to 22°C3. Use `start_charging`/`stop_charging` tools to control

3. `get_climate_status("Golf")` - verify activation (cache auto-refreshed after command)

### Remote Climate Control

### Vehicle Security

1. `resources/read("data://vehicle/Golf/climate")` - check current status

1. `get_vehicle_doors("Golf")` - check lock status2. `start_climatization` tool - pre-heat/cool

2. `lock_vehicle("Golf")` or `unlock_vehicle("Golf")` - as needed3. `resources/read("data://vehicle/Golf/climate")` - verify activation (cache auto-refreshed after command)

3. `get_vehicle_doors("Golf")` - verify action (cache auto-refreshed after command)

### Vehicle Security

### Pre-Trip Check

1. `resources/read("data://vehicle/Golf/doors")` - check lock status

1. `get_battery_status("ID.7")` - sufficient charge?2. `lock_vehicle` or `unlock_vehicle` tool - as needed

2. `get_vehicle_doors("Golf")` - all closed and locked?3. `resources/read("data://vehicle/Golf/doors")` - verify action (cache auto-refreshed after command)

3. `get_vehicle_position("Golf")` - where is the vehicle?4. `resources/read("data://vehicle/Golf/climate")` - check if using external power



### Find Vehicle in Parking Lot### Pre-Trip Check



1. `get_vehicle_position("Golf")` - get GPS coordinates1. `resources/read("data://vehicle/Golf/range")` - sufficient range?

2. `flash_lights("Golf", 10)` - flash lights for 10 seconds2. `resources/read("data://vehicle/Golf/doors")` - all closed and locked?

3. Or: `honk_and_flash("Golf", 5)` - honk and flash for 5 seconds3. `resources/read("data://vehicle/Golf/tyres")` - pressure OK?

4. `resources/read("data://vehicle/Golf/lights")` - any lights left on?

## BEST PRACTICES

### Maintenance Planning

- **Always start** with `get_vehicles()` to discover available vehicles

- **Use vehicle names** for better readability (e.g., "Golf" instead of VIN)1. `resources/read("data://vehicle/Golf/maintenance")` - when is service due?

- **For electric vehicles**, use `get_battery_status()` for quick checks2. `resources/read("data://vehicle/Golf/info")` - current odometer reading

- **For detailed charging analysis**, use `get_charging_status()`

- **Data is cached** for 5 minutes - cache automatically refreshes after any control command## BEST PRACTICES

- **Combine read tools** for comprehensive reports

- **Vehicle identifiers**: name, VIN, or license plate all work- **Always start** with `resources/read("data://vehicles")` to discover available vehicles

- **Use vehicle names** for better readability (e.g., "Golf" instead of VIN) in resource URIs

## ERROR HANDLING- **For electric vehicles**, prefer `resources/read("data://vehicle/{name}/battery")` for quick checks

- **For detailed charging analysis**, use `resources/read("data://vehicle/{name}/charging")`

- Tools return `{"error": "..."}` JSON if vehicle not found or data unavailable- **Check vehicle type first** if unknown: `resources/read("data://vehicle/{name}/type")`

- BEV/PHEV-only tools return errors for combustion vehicles- **Resources are cached** for 5 minutes - cache automatically refreshes after any tool command

- Always verify vehicle exists with `get_vehicles()` first- **Combine resources** for comprehensive reports (e.g., battery + doors + climate)

- Control tools return error dictionaries if operation fails- **Remember**: Resources use `resources/read(uri)`, Tools use direct function calls



## CACHING BEHAVIOR## ERROR HANDLING



- All read tools access cached data (5 minutes / 300 seconds)- Resources return `{"error": "..."}` JSON if vehicle not found or data unavailable

- Cache prevents excessive VW API calls and respects rate limits- BEV/PHEV-only resources return errors for combustion vehicles

- **Cache is automatically invalidated** after any control tool executes- Always verify vehicle_id from `resources/read("data://vehicles")` first

- Next read tool call after a control command will fetch fresh data from VW servers- Tools return error dictionaries if operation fails

- No manual cache management needed- If a resource URI is not found, check that `{vehicle_id}` is correctly replaced with actual identifier



## EXAMPLES## CACHING BEHAVIOR



```python- All resources are cached server-side for 5 minutes (300 seconds)

# Discover vehicles- Cache prevents excessive VW API calls and respects rate limits

get_vehicles()- **Cache is automatically invalidated** after any tool command executes

# Returns: [{"vin": "...", "name": "Golf", "model": "Golf 8", "license_plate": "B-AB 1234"}, ...]- Next resource read after a command will fetch fresh data from VW servers

- No manual cache management needed

# Check battery
get_battery_status("Golf")
# Returns: {"battery_level_percent": 85, "range_km": 320, "is_charging": false}

# Start climate control
start_climatization("Golf", 22.0)
# Returns: {"success": true, "message": "Climatization started"}

# Verify climate is running
get_climate_status("Golf")
# Returns: {"state": "heating", "target_temperature_celsius": 22.0, ...}

# Lock vehicle
lock_vehicle("Golf")
# Returns: {"success": true, "message": "Vehicle locked"}

# Verify doors are locked
get_vehicle_doors("Golf")
# Returns: {"lock_status": "locked", "front_left": "closed", ...}
```
