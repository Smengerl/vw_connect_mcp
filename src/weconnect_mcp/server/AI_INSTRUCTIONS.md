# AI Instructions for WeConnect MCP Server

**Purpose**: Access Volkswagen WeConnect vehicle data and control via Model Context Protocol (MCP)

**Key Features**:
- Read vehicle data (battery, doors, climate, position, etc.)
- Control vehicle remotely (lock, climate, charging, lights)
- Automatic caching (5 minutes) to respect VW API rate limits
- Support for BEV (electric), PHEV (hybrid), and combustion vehicles

**Critical Limitation** ⚠️:
As of February 2026, the VW WeConnect API does **NOT** provide license plate information. This is a Volkswagen API limitation, not a limitation of this server. All vehicles return `license_plate: null`. You cannot search or filter by license plate.

---

## MCP Server Architecture

This server provides **both Tools and Resources** via the Model Context Protocol:

### **MCP Tools** (Preferred for AI Assistants)
- **18 total tools**: 8 read-only tools + 10 command tools
- **Read tools** (`readOnlyHint: true`, `idempotentHint: true`):
  - `get_vehicles()` - List all vehicles
  - `get_vehicle_info(vehicle_id)` - Basic vehicle info
  - `get_vehicle_state(vehicle_id)` - Complete state snapshot
  - `get_vehicle_doors(vehicle_id)` - Door status
  - `get_battery_status(vehicle_id)` - Battery quick check (BEV/PHEV)
  - `get_climatization_status(vehicle_id)` - Climate control status
  - `get_charging_status(vehicle_id)` - Charging details (BEV/PHEV)
  - `get_vehicle_position(vehicle_id)` - GPS location
- **Command tools** (`readOnlyHint: false`):
  - `lock_vehicle(vehicle_id)`, `unlock_vehicle(vehicle_id)` - Door control
  - `start_climatization(vehicle_id, target_temp_celsius)`, `stop_climatization(vehicle_id)` - Climate control
  - `start_charging(vehicle_id)`, `stop_charging(vehicle_id)` - Charging control (BEV/PHEV)
  - `flash_lights(vehicle_id, duration_seconds)`, `honk_and_flash(vehicle_id, duration_seconds)` - Locator
  - `start_window_heating(vehicle_id)`, `stop_window_heating(vehicle_id)` - Window defrost

### **MCP Resources** (Alternative Access Pattern)
- **URI-based data access** with server-side caching
- **14 resources** (all read-only, prefixed with `res_` to distinguish from tools):
  - `data://vehicles` (`res_get_vehicles`) - List all vehicles
  - `data://vehicle/{vehicle_id}/info` (`res_get_vehicle_info`) - Basic vehicle information
  - `data://vehicle/{vehicle_id}/state` (`res_get_vehicle_state`) - Complete vehicle state snapshot
  - `data://vehicle/{vehicle_id}/doors` (`res_get_vehicle_doors`) - Door lock/open status
  - `data://vehicle/{vehicle_id}/windows` (`res_get_vehicle_windows`) - Window open/closed status
  - `data://vehicle/{vehicle_id}/tyres` (`res_get_vehicle_tyres`) - Tyre pressure and temperature
  - `data://vehicle/{vehicle_id}/type` (`res_get_vehicle_type`) - Vehicle propulsion type (BEV/PHEV/ICE)
  - `data://vehicle/{vehicle_id}/charging` (`res_get_charging_state`) - Detailed charging status (BEV/PHEV)
  - `data://vehicle/{vehicle_id}/climate` (`res_get_climatization_state`) - Climate control status
  - `data://vehicle/{vehicle_id}/maintenance` (`res_get_maintenance_info`) - Service schedule information
  - `data://vehicle/{vehicle_id}/range` (`res_get_range_info`) - Range and fuel/battery levels
  - `data://vehicle/{vehicle_id}/window-heating` (`res_get_window_heating_state`) - Window heating/defrost status
  - `data://vehicle/{vehicle_id}/lights` (`res_get_lights_state`) - Lights status
  - `data://vehicle/{vehicle_id}/position` (`res_get_position`) - GPS location
  - `data://vehicle/{vehicle_id}/battery` (`res_get_battery_status`) - Quick battery check (BEV/PHEV)
- **When to use**: When you need declarative data references or server-side caching semantics
- **When NOT to use**: Most AI interactions should use Tools (more intuitive function-call interface)

### **Recommendation for AI Assistants**
**Always use Tools** (not Resources) for interactive conversations. Tools provide:
- Better error handling with JSON responses
- Clearer intent (read vs. command)
- Consistent return format
- Automatic cache invalidation after commands

---

## Quick Start Guide (for AI Assistants)

### 1. Discover Available Vehicles
**Always start here!** Call `get_vehicles()` to see what vehicles are available.

```python
# First command in any conversation about vehicles
get_vehicles()
# Returns: [{"vin": "WVWZZZ...", "name": "Golf", "model": "Golf 8", "license_plate": null}, ...]
```

### 2. Identify Vehicles
Use either:
- **Vehicle name** (preferred): `"Golf"`, `"ID.7"`, `"T7"` - easier for humans to read
- **VIN**: `"WVWZZZAUZPW123456"` - unique identifier

Both formats work automatically. The system resolves them internally.

### 3. Read Vehicle Data
Use the `get_*` tools to access cached vehicle data.

### 4. Control Vehicle
Use the command tools (`lock_*`, `start_*`, `stop_*`) to control the vehicle. These automatically invalidate the cache.

---
---

## Available Tools (Complete Reference)

All tools return JSON data. Data is cached for 5 minutes. Cache auto-refreshes after control commands.

### Discovery & Basic Info

**`get_vehicles()`**
- **Purpose**: List all available vehicles
- **Returns**: Array of vehicles with VIN, name, model (license_plate always null)
- **When to use**: Always use this first to discover what vehicles exist
- **Example**: `get_vehicles()` → `[{"vin": "WVWZZZ...", "name": "Golf", "model": "Golf 8", "license_plate": null}]`

**`get_vehicle_info(vehicle_id)`**
- **Purpose**: Get basic vehicle information
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Manufacturer, model, software version, year, odometer, connection state
- **Example**: `get_vehicle_info("Golf")` → `{"model": "Golf 8", "odometer": 15432, ...}`

**`get_vehicle_state(vehicle_id)`**
- **Purpose**: Complete state snapshot (all systems combined)
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Comprehensive overview of all vehicle systems
- **When to use**: When you need everything at once, or user asks for "full status"
- **Example**: `get_vehicle_state("Golf")` → `{doors: {...}, windows: {...}, battery: {...}, ...}`

### Physical Components

**`get_vehicle_doors(vehicle_id)`**
- **Purpose**: Door lock and open/closed status
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Lock state (locked/unlocked) and open state for each door
- **Example**: `get_vehicle_doors("Golf")` → `{"lock_state": "locked", "front_left": {"open": false, "locked": true}, ...}`

### Energy & Range

**`get_battery_status(vehicle_id)`**
- **Purpose**: Quick battery check for electric vehicles
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Vehicle types**: BEV/PHEV only (returns error for combustion)
- **Returns**: Battery level (%), electric range (km), charging status
- **When to use**: Quick check before departure, or user asks "how much charge?"
- **Example**: `get_battery_status("ID.7")` → `{"battery_level_percent": 85, "range_km": 320, "is_charging": false}`

**`get_charging_status(vehicle_id)`**
- **Purpose**: Detailed charging analysis
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Vehicle types**: BEV/PHEV only
- **Returns**: Power (kW), remaining time, cable status, target SOC, charging state
- **When to use**: User asks about charging details, or monitoring active charging session
- **Example**: `get_charging_status("ID.7")` → `{"is_charging": true, "charging_power_kw": 11.0, "remaining_time_minutes": 45, ...}`

### Climate & Comfort

**`get_climate_status(vehicle_id)`**
- **Purpose**: Climate control system status
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: State (off/heating/cooling/ventilation), target temperature, estimated time
- **Example**: `get_climate_status("Golf")` → `{"state": "heating", "target_temperature_celsius": 22.0, "is_active": true, ...}`

### Location

**`get_vehicle_position(vehicle_id)`**
- **Purpose**: GPS location and heading
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Latitude, longitude, heading (0°=North, 90°=East, 180°=South, 270°=West)
- **Example**: `get_vehicle_position("Golf")` → `{"latitude": 48.1351, "longitude": 11.5820, "heading": 45.0}`

### Maintenance

**`get_maintenance_info(vehicle_id)`**
- **Purpose**: Service schedule information
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Inspection and oil service due dates/distances
- **Example**: `get_maintenance_info("Golf")` → `{"inspection_due_date": "2026-06-15", "inspection_due_distance_km": 5000, ...}`

---

## Available Resources (URI-Based Data Access)

Resources provide **alternative access** to vehicle data via URIs. They return the **same data** as tools but use a different access pattern. All resource names are prefixed with `res_` to distinguish them from tools. Most AI assistants should prefer **Tools** for better integration.

### Discovery & Basic Info Resources

**`data://vehicles`** (res_get_vehicles)
- **Purpose**: List all available vehicles
- **Returns**: Array of vehicles with VIN, name, model (license_plate always null)
- **Equivalent Tool**: `get_vehicles()`

**`data://vehicle/{vehicle_id}/info`** (res_get_vehicle_info)
- **Purpose**: Basic vehicle information
- **Returns**: Manufacturer, model, software version, year, odometer, connection state
- **Equivalent Tool**: `get_vehicle_info(vehicle_id)`

**`data://vehicle/{vehicle_id}/state`** (res_get_vehicle_state)
- **Purpose**: Complete state snapshot
- **Returns**: All vehicle systems combined
- **Equivalent Tool**: `get_vehicle_state(vehicle_id)`

**`data://vehicle/{vehicle_id}/type`** (res_get_vehicle_type)
- **Purpose**: Vehicle propulsion type
- **Returns**: Type: `"electric"` (BEV), `"combustion"`, or `"plug-in_hybrid"` (PHEV)
- **When to use**: Determine if battery/charging features are available

### Physical Components Resources

**`data://vehicle/{vehicle_id}/doors`** (res_get_vehicle_doors)
- **Purpose**: Door lock and open/closed status
- **Returns**: Lock state and status for each door
- **Equivalent Tool**: `get_vehicle_doors(vehicle_id)`

**`data://vehicle/{vehicle_id}/windows`** (res_get_vehicle_windows)
- **Purpose**: Window open/closed status
- **Returns**: Status for all windows

**`data://vehicle/{vehicle_id}/tyres`** (res_get_vehicle_tyres)
- **Purpose**: Tyre pressure and temperature
- **Returns**: Pressure (bar/psi) and temperature for all tyres

**`data://vehicle/{vehicle_id}/lights`** (res_get_lights_state)
- **Purpose**: Vehicle lights status
- **Returns**: Left/right light on/off status

### Energy & Range Resources

**`data://vehicle/{vehicle_id}/battery`** (res_get_battery_status)
- **Purpose**: Quick battery check
- **Vehicle types**: BEV/PHEV only
- **Returns**: Battery level (%), electric range (km), charging status
- **Equivalent Tool**: `get_battery_status(vehicle_id)`

**`data://vehicle/{vehicle_id}/charging`** (res_get_charging_state)
- **Purpose**: Detailed charging status
- **Vehicle types**: BEV/PHEV only
- **Returns**: Power (kW), remaining time, cable status, target SOC, charging state
- **Equivalent Tool**: `get_charging_status(vehicle_id)`

**`data://vehicle/{vehicle_id}/range`** (res_get_range_info)
- **Purpose**: Range and fuel/battery levels
- **Returns**: Total range, electric range (BEV/PHEV), combustion range (PHEV/ICE), battery/tank levels

### Climate & Comfort Resources

**`data://vehicle/{vehicle_id}/climate`** (res_get_climatization_state)
- **Purpose**: Climate control status
- **Returns**: State (off/heating/cooling), target temperature, window/seat heating
- **Equivalent Tool**: `get_climatization_status(vehicle_id)` (note: tools use different naming)

**`data://vehicle/{vehicle_id}/window-heating`** (res_get_window_heating_state)
- **Purpose**: Window heating/defrost status
- **Returns**: Front and rear window heating state

### Location Resources

**`data://vehicle/{vehicle_id}/position`** (res_get_position)
- **Purpose**: GPS location
- **Returns**: Latitude, longitude, heading (0°=North, 90°=East, 180°=South, 270°=West)
- **Equivalent Tool**: `get_vehicle_position(vehicle_id)`

### Maintenance Resources

**`data://vehicle/{vehicle_id}/maintenance`** (res_get_maintenance_info)
- **Purpose**: Service schedule information
- **Returns**: Inspection and oil service due dates/distances
- **Note**: Also available as tool `get_maintenance_info(vehicle_id)`

---

## Control Commands (Write Operations)

All control commands return `{"success": true/false, "message": "...", "error": "..."}` and automatically invalidate the cache.

### Door Control

**`lock_vehicle(vehicle_id)`**
- **Action**: Lock all doors
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `lock_vehicle("Golf")` → `{"success": true, "message": "Vehicle locked"}`

**`unlock_vehicle(vehicle_id)`**
- **Action**: Unlock all doors
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `unlock_vehicle("Golf")` → `{"success": true, "message": "Vehicle unlocked"}`

### Climate Control

**`start_climatization(vehicle_id, target_temp_celsius=None)`**
- **Action**: Start pre-heating or pre-cooling
- **Parameters**:
  - `vehicle_id` - Vehicle name or VIN
  - `target_temp_celsius` (optional) - Target temperature in Celsius (if supported by vehicle)
- **Examples**:
  - `start_climatization("Golf")` - Uses last temperature setting
  - `start_climatization("Golf", 22.0)` - Sets target to 22°C

**`stop_climatization(vehicle_id)`**
- **Action**: Stop climate control
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `stop_climatization("Golf")`

**`start_window_heating(vehicle_id)`**
- **Action**: Activate window heating/defrosting
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `start_window_heating("Golf")`

**`stop_window_heating(vehicle_id)`**
- **Action**: Deactivate window heating
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `stop_window_heating("Golf")`

### Charging Control (BEV/PHEV only)

**`start_charging(vehicle_id)`**
- **Action**: Start charging session
- **Requirements**: 
  - ⚠️ **CRITICAL**: Vehicle must be plugged in (cable connected)
  - ⚠️ **CRITICAL**: Current SOC (State of Charge) must be below target SOC
  - ⚠️ **CRITICAL**: Always verify charging actually started after sending command (VW API may fail silently)
- **Pre-command validation workflow**:
  1. Call `get_charging_status(vehicle_id)` to check:
     - `is_plugged_in` must be `true` (or `plug_connection_state` is `"connected"`)
     - `current_soc_percent` must be less than `target_soc_percent`
  2. If not plugged in: Inform user "Cannot start charging - vehicle not plugged in"
  3. If SOC >= target: Inform user "Cannot start charging - battery already at/above target SOC ({current}% >= {target}%)"
  4. Only if both conditions met: Send `start_charging()` command
- **Post-command verification workflow**:
  1. Send `start_charging()` command
  2. Wait 10-15 seconds for command to propagate
  3. Call `get_charging_status(vehicle_id)` again
  4. Verify `is_charging` is `true` and `charging_state` is `"charging"`
  5. If NOT charging: Inform user "Charging command sent but vehicle did not start charging - check vehicle display for errors"
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: See "Charging Session Management (Safe Workflow)" in Common Usage Patterns below

**`stop_charging(vehicle_id)`**
- **Action**: Stop charging session
- **Requirements**:
  - ⚠️ **CRITICAL**: Vehicle must be currently charging
  - ⚠️ **WARNING**: Check SOC before stopping - warn user if stopping prematurely
  - ⚠️ **CRITICAL**: Always verify charging actually stopped after sending command
- **Pre-command validation workflow**:
  1. Call `get_charging_status(vehicle_id)` to check:
     - `is_charging` must be `true` (or `charging_state` is `"charging"`)
     - Check `current_soc_percent` vs `target_soc_percent` for warnings
  2. If NOT charging: Inform user "Cannot stop charging - vehicle is not currently charging"
  3. If SOC < 20%: **WARN** user "⚠️ Battery very low ({current}%) - are you sure you want to stop charging?"
  4. If SOC < target - 10%: **WARN** user "⚠️ Battery at {current}% (target: {target}%) - stopping charging now will leave battery well below target"
  5. Only if user confirms (or no warnings): Send `stop_charging()` command
- **Post-command verification workflow**:
  1. Send `stop_charging()` command
  2. Wait 10-15 seconds for command to propagate
  3. Call `get_charging_status(vehicle_id)` again
  4. Verify `is_charging` is `false` and `charging_state` is NOT `"charging"`
  5. If STILL charging: Inform user "Stop charging command sent but vehicle is still charging - check vehicle display or try again"
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: See "Stop Charging (Safe Workflow)" in Examples section below

### Locator Features

**`flash_lights(vehicle_id, duration_seconds=None)`**
- **Action**: Flash headlights to locate vehicle in parking lot
- **Parameters**:
  - `vehicle_id` - Vehicle name or VIN
  - `duration_seconds` (optional) - Flash duration in seconds (if supported by vehicle)
- **Examples**:
  - `flash_lights("Golf")` - Flash with default duration
  - `flash_lights("Golf", 10)` - Flash for 10 seconds

**`honk_and_flash(vehicle_id, duration_seconds=None)`**
- **Action**: Honk horn and flash lights simultaneously
- **Parameters**:
  - `vehicle_id` - Vehicle name or VIN
  - `duration_seconds` (optional) - Duration in seconds (if supported by vehicle)
- **Examples**:
  - `honk_and_flash("Golf")` - Use default duration
  - `honk_and_flash("Golf", 5)` - Honk and flash for 5 seconds

---

## Common Usage Patterns

### Quick Battery Check (Electric Vehicle)
```python
# 1. Discover vehicles
get_vehicles()

# 2. Check battery
get_battery_status("ID.7")
# Result: Battery at 85%, 320 km range, not charging
```

### Full Status Report
```python
# 1. Discover vehicles
get_vehicles()

# 2. Get comprehensive state
get_vehicle_state("Golf")
# Result: All systems status in one call
```

### Pre-Trip Check
```python
# 1. Check battery/fuel
get_battery_status("ID.7")  # or get_vehicle_state() for combustion

# 2. Check doors are closed and locked
get_vehicle_doors("ID.7")

# 3. Check location
get_vehicle_position("ID.7")
```

### Remote Climate Control
```python
# 1. Check current climate state
get_climate_status("Golf")

# 2. Start pre-heating to 22°C
start_climatization("Golf", 22.0)

# 3. Verify it started (cache auto-refreshes after command)
get_climate_status("Golf")
# Result: state = "heating", target = 22°C
```

### Charging Session Management (Safe Workflow)
```python
# === STARTING CHARGING ===

# 1. Check detailed charging status BEFORE attempting to start
charging = get_charging_status("ID.7")
# Result: {"is_plugged_in": true, "current_soc_percent": 45, "target_soc_percent": 80, "is_charging": false}

# 2. Validate prerequisites
if not charging["is_plugged_in"]:
    # Error: Cannot start charging - vehicle not plugged in
    return

if charging["current_soc_percent"] >= charging["target_soc_percent"]:
    # Error: Cannot start charging - battery at 45% already at/above target 80%
    return

# 3. Prerequisites met - send start command
result = start_charging("ID.7")
# Result: {"success": true}

# 4. CRITICAL: Wait for command to propagate (10-15 seconds)
wait(15)

# 5. Verify charging actually started
charging_verify = get_charging_status("ID.7")
# Result: {"is_charging": true, "charging_state": "charging", "charging_power_kw": 11.0}

if not charging_verify["is_charging"]:
    # Error: Charging command sent but vehicle did not start charging
    # Possible causes: Vehicle error, charger error, API failure
    # Action: Ask user to check vehicle display for error messages

# 6. Monitor progress (optional)
battery = get_battery_status("ID.7")
# Result: {"battery_level_percent": 45, "is_charging": true}


# === STOPPING CHARGING ===

# 1. Check if vehicle is currently charging BEFORE attempting to stop
charging = get_charging_status("ID.7")
# Result: {"is_charging": true, "current_soc_percent": 65, "target_soc_percent": 80}

# 2. Validate vehicle is charging
if not charging["is_charging"]:
    # Error: Cannot stop charging - vehicle is not currently charging
    return

# 3. Check for warning conditions
if charging["current_soc_percent"] < 20:
    # WARNING: Battery very low (65%) - are you sure?
    # Get user confirmation before proceeding

if charging["current_soc_percent"] < charging["target_soc_percent"] - 10:
    # WARNING: Battery at 65% (target: 80%) - well below target
    # Get user confirmation before proceeding

# 4. User confirmed or no warnings - send stop command
result = stop_charging("ID.7")
# Result: {"success": true}

# 5. CRITICAL: Wait for command to propagate (10-15 seconds)
wait(15)

# 6. Verify charging actually stopped
charging_verify = get_charging_status("ID.7")
# Result: {"is_charging": false, "charging_state": "ready_for_charging"}

if charging_verify["is_charging"]:
    # Error: Stop charging command sent but vehicle is still charging
    # Possible causes: Scheduled charging override, vehicle error, API failure
    # Action: Ask user to check vehicle display or try again
```

### Vehicle Security
```python
# 1. Check lock status
get_vehicle_doors("Golf")

# 2. Lock vehicle if needed
lock_vehicle("Golf")

# 3. Verify it locked (cache auto-refreshes)
get_vehicle_doors("Golf")
```

### Find Vehicle in Parking Lot
```python
# 1. Get GPS coordinates
get_vehicle_position("Golf")

# 2. Flash lights for 10 seconds
flash_lights("Golf", 10)

# Alternative: Honk and flash
honk_and_flash("Golf", 5)
```

---

## Best Practices (for AI Assistants)

### 1. **Always Start with Discovery**
- First command: `get_vehicles()` to see what's available
- Validates vehicle exists before trying to access it

### 2. **Use Readable Vehicle Names**
- Prefer: `"Golf"`, `"ID.7"` (easier for humans)
- Avoid: Long VINs unless necessary
- Both work, but names are more readable

### 3. **Choose the Right Tool**
- **Quick check**: `get_battery_status()` for electric vehicles
- **Detailed analysis**: `get_charging_status()` for charging details
- **Everything**: `get_vehicle_state()` for comprehensive overview

### 4. **Verify Vehicle Type**
- Check vehicle type before using BEV/PHEV-only tools
- `get_battery_status()` and `get_charging_status()` only work for electric/hybrid
- Combustion vehicles will return errors for these tools

### 5. **Trust the Cache**
- Data is cached for 5 minutes automatically
- Cache refreshes automatically after any control command
- No need to manually manage cache

### 6. **Handle Errors Gracefully**
- All tools return JSON with `error` field if something fails
- Common errors: vehicle not found, feature not supported, VW API unavailable
- Always check for `error` field in responses

### 7. **CRITICAL: Safe Charging Workflow** ⚠️
**ALWAYS follow these workflows when controlling charging - DO NOT skip steps!**

#### Starting Charging: `start_charging()`

1. **Pre-command validation** (REQUIRED):
   - Call `get_charging_status(vehicle_id)` BEFORE `start_charging()`
   - Check `is_plugged_in` is `true` (or `plug_connection_state == "connected"`)
   - Check `current_soc_percent < target_soc_percent`
   - If either check fails: DO NOT send command, inform user of the reason

2. **Send command** (only if validation passed):
   - Call `start_charging(vehicle_id)`

3. **Post-command verification** (REQUIRED):
   - Wait 10-15 seconds for command to propagate to vehicle
   - Call `get_charging_status(vehicle_id)` again
   - Verify `is_charging` is `true` and `charging_state == "charging"`
   - If NOT charging: Inform user that command was sent but charging did not start (possible vehicle/charger error)

**Why this matters**: The VW API may return success but the vehicle may fail to start charging due to:
- Vehicle-side errors (battery management system limits)
- Charger errors (communication failure, power issues)
- API propagation delays or failures
- Physical issues (cable not fully connected despite reporting "plugged in")

**Example failure scenario**: Vehicle reports `is_plugged_in: true` but cable is loosely connected → Command succeeds but charging never starts → Without verification, user thinks car is charging but returns to empty battery.

#### Stopping Charging: `stop_charging()`

1. **Pre-command validation** (REQUIRED):
   - Call `get_charging_status(vehicle_id)` BEFORE `stop_charging()`
   - Check `is_charging` is `true` (or `charging_state == "charging"`)
   - If NOT charging: DO NOT send command, inform user "Vehicle is not currently charging"

2. **Pre-command warnings** (REQUIRED - get user confirmation):
   - If `current_soc_percent < 20%`: **WARN** "⚠️ Battery very low ({current}%) - are you sure you want to stop charging?"
   - If `current_soc_percent < target_soc_percent - 10`: **WARN** "⚠️ Battery at {current}% (target: {target}%) - stopping now will leave battery well below target"
   - Wait for user confirmation before proceeding if warnings issued
   - If user wants to proceed anyway: Continue with command

3. **Send command** (only if validation passed and warnings acknowledged):
   - Call `stop_charging(vehicle_id)`

4. **Post-command verification** (REQUIRED):
   - Wait 10-15 seconds for command to propagate to vehicle
   - Call `get_charging_status(vehicle_id)` again
   - Verify `is_charging` is `false` and `charging_state` is NOT `"charging"`
   - If STILL charging: Inform user that command was sent but charging did not stop (possible vehicle error)

**Why this matters**: Stopping charging prematurely can leave the user stranded:
- Very low SOC (< 20%): May not have enough range to reach next charger
- Well below target: User set a target for a reason (planned trip range)
- Silent failure: VW API may report success but vehicle continues charging (e.g., scheduled charging override)

**Example warning scenario**: User says "stop charging my ID.7" → Battery at 15% (target 80%) → AI warns "⚠️ Battery very low (15%) and well below target (80%) - are you sure?" → User can reconsider or confirm they want to stop anyway.

---

## Technical Details

### Caching Behavior
- **Duration**: 5 minutes (300 seconds)
- **Purpose**: Respect VW API rate limits, improve response time
- **Auto-refresh**: Cache invalidates automatically after any control command
- **Transparent**: No manual cache management needed

### Vehicle Identification
The system automatically resolves both vehicle names and VINs:
- **Name**: `"Golf"`, `"ID.7"`, `"T7"` - matched case-insensitively
- **VIN**: `"WVWZZZAUZPW123456"` - exact match
- **License Plate**: NOT SUPPORTED (VW API limitation)

### Architecture (Internal)
The server uses a modular mixin-based architecture:
- **CacheMixin**: Handles data caching and invalidation
- **VehicleResolutionMixin**: Resolves names/VINs to internal vehicle objects
- **CommandMixin**: All 10 control commands (lock, climate, charging, lights)
- **StateExtractionMixin**: Extracts state from carconnectivity vehicle objects
- **Main Adapter**: Orchestrates mixins and provides public API

---

## Known Limitations

### 1. No License Plate Data (VW API Limitation)
- **Issue**: VW WeConnect API does not provide license plate information (as of February 2026)
- **Impact**: All vehicles show `license_plate: null`
- **Workaround**: Use vehicle name or VIN instead
- **Not fixable**: This is a Volkswagen API limitation, not a bug in this server

### 2. VW API Rate Limiting
- **Issue**: VW servers limit request frequency
- **Mitigation**: 5-minute cache reduces API calls
- **Impact**: Rapid repeated requests may be temporarily blocked

### 3. Token Expiration
- **Issue**: Authentication tokens expire after several hours
- **Mitigation**: Server automatically re-authenticates when needed
- **Impact**: Occasional delays on first request after long idle periods

### 4. API Availability
- **Issue**: VW servers can be temporarily unavailable
- **Impact**: First connection after server start can take 10-30 seconds
- **Retry**: Usually resolves itself within a minute

### 5. Command Execution Time
- **Issue**: Control commands sent to VW API are not instant
- **Impact**: Vehicle may take 5-30 seconds to execute command
- **Best practice**: Check status again after 30 seconds if needed

---

## Error Handling

All tools return consistent error format:

```json
{
  "success": false,
  "error": "Vehicle not found: Golf"
}
```

### Common Errors

**"Vehicle not found"**
- Cause: Invalid vehicle_id
- Solution: Use `get_vehicles()` to see available vehicles

**"Vehicle does not support [feature]"**
- Cause: Trying to use BEV/PHEV tool on combustion vehicle, or feature not available
- Solution: Check vehicle type, try different tool

**"VW API unavailable"** / **"Connection timeout"**
- Cause: VW servers temporarily down
- Solution: Wait 1-2 minutes and retry

**"Authentication failed"**
- Cause: Invalid credentials or token expired
- Solution: Server will automatically re-authenticate, or restart server

---

## Examples (Copy-Paste Ready)

### Example 1: Morning Vehicle Check
```python
# Discover vehicles
vehicles = get_vehicles()
# Result: [{"name": "ID.7", ...}]

# Check battery level
battery = get_battery_status("ID.7")
# Result: {"battery_level_percent": 85, "range_km": 320}

# Check doors are locked
doors = get_vehicle_doors("ID.7")
# Result: {"lock_state": "locked"}

# All good! Ready to go.
```

### Example 2: Pre-Heat Before Departure
```python
# Check current climate state
climate = get_climate_status("Golf")
# Result: {"state": "off"}

# Start heating to 22°C
result = start_climatization("Golf", 22.0)
# Result: {"success": true, "message": "Climatization started"}

# Verify it's running (30 seconds later)
climate = get_climate_status("Golf")
# Result: {"state": "heating", "target_temperature_celsius": 22.0}
```

### Example 3: Charging Session (Safe Workflow)
```python
# 1. Check if vehicle is ready to charge
charging = get_charging_status("ID.7")
# Result: {"is_plugged_in": true, "current_soc_percent": 45, "target_soc_percent": 80, "is_charging": false}

# 2. Validate prerequisites
if not charging["is_plugged_in"]:
    print("ERROR: Cannot start charging - vehicle not plugged in")
    exit()

if charging["current_soc_percent"] >= charging["target_soc_percent"]:
    print(f"INFO: Battery already at target ({charging['current_soc_percent']}% >= {charging['target_soc_percent']}%)")
    exit()

# 3. Prerequisites met - start charging
result = start_charging("ID.7")
# Result: {"success": true, "message": "Charging started"}

# 4. Wait for command to propagate
wait(15)  # Wait 15 seconds

# 5. Verify charging actually started
charging_verify = get_charging_status("ID.7")
# Result: {"is_charging": true, "charging_state": "charging", "charging_power_kw": 11.0, "remaining_time_minutes": 120}

if charging_verify["is_charging"]:
    print(f"SUCCESS: Charging started - {charging_verify['charging_power_kw']} kW, {charging_verify['remaining_time_minutes']} min remaining")
else:
    print("ERROR: Charging command sent but vehicle did not start charging - check vehicle display")
```

### Example 4: Stop Charging (Safe Workflow with Warnings)
```python
# 1. Check if vehicle is currently charging
charging = get_charging_status("ID.7")
# Result: {"is_charging": true, "current_soc_percent": 45, "target_soc_percent": 80, "charging_power_kw": 11.0}

# 2. Validate vehicle is actually charging
if not charging["is_charging"]:
    print("ERROR: Cannot stop charging - vehicle is not currently charging")
    exit()

# 3. Check for warning conditions
warnings = []

if charging["current_soc_percent"] < 20:
    warnings.append(f"⚠️ Battery very low ({charging['current_soc_percent']}%) - stopping now may leave insufficient range")

if charging["current_soc_percent"] < charging["target_soc_percent"] - 10:
    warnings.append(f"⚠️ Battery at {charging['current_soc_percent']}% (target: {charging['target_soc_percent']}%) - stopping now will leave battery well below target")

# 4. Display warnings and get confirmation
if warnings:
    for warning in warnings:
        print(warning)
    print("\nAre you sure you want to stop charging? (yes/no)")
    # If user says no, exit without stopping
    # If user confirms yes, continue

# 5. User confirmed or no warnings - stop charging
result = stop_charging("ID.7")
# Result: {"success": true, "message": "Charging stopped"}

# 6. Wait for command to propagate
wait(15)  # Wait 15 seconds

# 7. Verify charging actually stopped
charging_verify = get_charging_status("ID.7")
# Result: {"is_charging": false, "charging_state": "ready_for_charging", "current_soc_percent": 47}

if not charging_verify["is_charging"]:
    print(f"SUCCESS: Charging stopped - battery at {charging_verify['current_soc_percent']}%")
else:
    print("ERROR: Stop charging command sent but vehicle is still charging - check vehicle display or try again")
```

### Example 5: Find Car in Parking Lot
```python
# Get location
position = get_vehicle_position("Golf")
# Result: {"latitude": 48.1351, "longitude": 11.5820}

# Flash lights for 10 seconds to locate it
result = flash_lights("Golf", 10)
# Result: {"success": true}
```

---

## Summary (TL;DR for AI Assistants)

1. **Always start** with `get_vehicles()` to discover available vehicles
2. **Use vehicle names** (e.g., "Golf") instead of VINs for readability
3. **License plates DON'T WORK** - VW API doesn't provide them (as of Feb 2026)
4. **Electric vehicles**: Use `get_battery_status()` for quick checks
5. **Charging details**: Use `get_charging_status()` for detailed analysis
6. **Cache is automatic** - 5 minutes, refreshes after commands, no manual management
7. **Errors are JSON** - Check for `error` field in responses
8. **Control commands** invalidate cache automatically - next read gets fresh data

**Most important**: Be helpful and proactive. If a user asks about their car, start with `get_vehicles()` to see what's available, then provide relevant information based on their question.

---

## Technical Reference: Tool & Resource Tags

All tools and resources include **hierarchical tags** for MCP client filtering and organization:

### Tag Categories

**Operation Type** (all items):
- `read` - Read-only operations (8 read tools + 14 resources)
- `write` - State-changing operations (synonym for `command`)
- `command` - State-changing operations (10 command tools)

**Functional Areas**:
- `discovery` - Vehicle discovery (`get_vehicles`)
- `vehicle-info` - Basic vehicle information (`get_vehicle_info`, `get_vehicle_state`)
- `physical` - Physical components (`get_vehicle_doors`)
- `energy` - Battery and charging (`get_battery_status`, `get_charging_status`, charging commands)
- `climate` - Climate control (`get_climatization_status`, climatization commands, window heating)
- `location` - GPS position (`get_vehicle_position`)
- `security` - Door locks (`lock_vehicle`, `unlock_vehicle`)

**Specific Features**:
- `battery` - Battery status (BEV/PHEV)
- `charging` - Charging control (BEV/PHEV)
- `gps` - GPS location
- `comfort` - Climate and comfort features
- `locator` - Finding vehicle in parking lot
- `lights` - Light control
- `horn` - Horn control
- `defrost` - Window heating/defrosting
- `comprehensive` - Complete state snapshot

**Vehicle Type Filters**:
- `bev-phev` - Electric/hybrid vehicles only

### Example Tag Combinations

- `get_vehicles`: `{"discovery", "read"}`
- `get_battery_status`: `{"energy", "read", "battery", "bev-phev"}`
- `start_charging`: `{"command", "charging", "energy", "bev-phev", "write"}`
- `lock_vehicle`: `{"command", "security", "write"}`
- `flash_lights`: `{"command", "locator", "lights", "write"}`
- `honk_and_flash`: `{"command", "locator", "lights", "horn", "write"}`

**Usage**: MCP clients can filter tools by tags to show only relevant operations (e.g., show only `bev-phev` tools when working with electric vehicles, or only `read` tools when browsing data).

