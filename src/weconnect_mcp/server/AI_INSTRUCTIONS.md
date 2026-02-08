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
- **Requirements**: Vehicle must be plugged in
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `start_charging("ID.7")`

**`stop_charging(vehicle_id)`**
- **Action**: Stop charging session
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Example**: `stop_charging("ID.7")`

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

### Charging Session Management
```python
# 1. Check detailed charging status
get_charging_status("ID.7")

# 2. Start or stop charging
start_charging("ID.7")  # or stop_charging("ID.7")

# 3. Monitor progress
get_battery_status("ID.7")
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

### Example 3: Charging Session
```python
# Check if vehicle is plugged in
charging = get_charging_status("ID.7")
# Result: {"is_plugged_in": true, "is_charging": false}

# Start charging
result = start_charging("ID.7")
# Result: {"success": true}

# Monitor progress
charging = get_charging_status("ID.7")
# Result: {"is_charging": true, "charging_power_kw": 11.0, "remaining_time_minutes": 45}
```

### Example 4: Find Car in Parking Lot
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
