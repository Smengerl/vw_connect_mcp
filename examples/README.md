# Examples

This directory contains demonstration scripts showcasing the capabilities of the weconnect_mvp MCP server.

## Quick Start

Run any example with:
```bash
python3 examples/<example_name>.py
```

## Available Examples

### 🆕 New Features & Architecture

#### `consolidated_api_demo.py` ⭐ **RECOMMENDED**
Demonstrates the new consolidated API architecture - **start here!**

**What it shows:**
- `get_vehicle()` with BASIC vs FULL detail levels
- `get_physical_status()` with component filtering (doors, windows, tyres, lights)
- `get_energy_status()` - vehicle-type-aware (battery for electric, fuel for combustion)
- `get_climate_status()` - unified climate info (climatization + window heating)
- Comparison: Old vs New API architecture

**Key improvements over old API:**
- ✅ Fewer MCP tools (4 vs 10+)
- ✅ Better organization (logical categories)
- ✅ Flexible detail levels (BASIC/FULL)
- ✅ Component filtering (request only what you need)

```bash
python3 examples/consolidated_api_demo.py
```

**Replaces:** `battery_demo.py`, `charging_state_demo.py`, `phase1_demo.py`, `phase2_demo.py`

---

#### `license_plate_demo.py` ⭐ **NEW**
Demonstrates the license plate support added to VehicleModel.

**What it shows:**
- License plates in `list_vehicles()` and `get_vehicle()`
- Vehicle identification by license plate
- Consistency check between methods
- Before/after comparison of the fix
- Practical use cases (user-friendly selection, fleet management)

**Key features:**
- ✅ License plate now available in both BASIC and FULL detail levels
- ✅ Can identify vehicles by plate: `adapter.resolve_vehicle_id('M-AB 1234')`
- ✅ Consistent API across all methods

```bash
python3 examples/license_plate_demo.py
```

---

#### `caching_demo.py` ⭐ **NEW**
Explains the caching system that prevents VW API rate limiting.

**What it shows:**
- Cache configuration (default: 300 seconds / 5 minutes)
- Cache behavior (hit/miss)
- Internal mechanism
- Customization guide
- Logging examples

**Key features:**
- ✅ Automatic caching of VW server responses
- ✅ Configurable duration via `CACHE_DURATION_SECONDS`
- ✅ Transparent to users (no code changes needed)
- ✅ Prevents VW API rate limits

```bash
python3 examples/caching_demo.py
```

---

### 🚗 Vehicle Identification & Management

#### `vehicle_identifier_demo.py`
Shows the flexible vehicle identification system.

**What it demonstrates:**
- Identify vehicles by VIN, name, or license plate
- Case-insensitive matching
- Resolution priority: Name > VIN > License Plate
- Tool usage with different identifiers
- All three methods return identical results

**Example identifiers:**
- `'ID7'` - by name
- `'WVWZZZED4SE003938'` - by VIN
- `'M-XY 5678'` - by license plate

```bash
python3 examples/vehicle_identifier_demo.py
```

---

#### `vehicle_type_demo.py`
Demonstrates vehicle type detection (electric, combustion, hybrid).

**What it shows:**
- Detect vehicle type from VIN
- Type-specific information
- MCP tool usage examples
- Human-friendly descriptions

**Vehicle types:**
- `electric` - Battery Electric Vehicle (BEV)
- `combustion` - Internal Combustion Engine
- `hybrid` / `plugin_hybrid` - Hybrid vehicles

```bash
python3 examples/vehicle_type_demo.py
```

---

### 📍 Location Services

#### `position_demo.py`
Shows vehicle position retrieval.

**What it demonstrates:**
- GPS coordinates (latitude/longitude)
- Heading/compass direction
- Parking time
- Location tracking
- Coordinate formatting

```bash
python3 examples/position_demo.py
```

---

## Architecture Evolution

### Problem: Too Many Specialized Methods

The old API (Phase 1 + 2) had grown to 10+ specialized methods, making it difficult to maintain and use:

```python
# OLD API - Many fragmented calls
battery = adapter.get_battery_status(vin)
range = adapter.get_range_info(vin)
doors = adapter.get_doors_state(vin)
windows = adapter.get_windows_state(vin)
tyres = adapter.get_tyres_state(vin)
lights = adapter.get_lights_state(vin)
climate = adapter.get_climatization_state(vin)
window_heat = adapter.get_window_heating_state(vin)
maintenance = adapter.get_maintenance_info(vin)
# ... and more
```

**Problems:**
- ❌ Too many MCP tools (10+)
- ❌ Poor organization (flat structure)
- ❌ Redundant API calls
- ❌ Difficult to maintain

### Solution: Consolidated API

The new API groups related functionality into 4 logical categories:

```python
# NEW API - Logical groupings with flexible filtering
vehicle = adapter.get_vehicle(vin, details='full')
physical = adapter.get_physical_status(vin, components=['doors', 'windows'])
energy = adapter.get_energy_status(vin)  # Type-aware (electric vs combustion)
climate = adapter.get_climate_status(vin)
```

**Benefits:**
- ✅ Fewer MCP tools (4 vs 10+)
- ✅ Better organization (logical categories)
- ✅ Flexible detail levels (BASIC/FULL)
- ✅ Component filtering (request only what you need)
- ✅ Vehicle-type awareness (electric vs combustion)
- ✅ Easier to maintain and extend

### Migration Guide

**Old Code:**
```python
battery = adapter.get_battery_status(vin)
range = adapter.get_range_info(vin)
```

**New Code:**
```python
energy = adapter.get_energy_status(vin)
# Access: energy.electric_drive.battery_level_percent
#         energy.range.total_km
```

**Old Code:**
```python
doors = adapter.get_doors_state(vin)
windows = adapter.get_windows_state(vin)
```

**New Code:**
```python
physical = adapter.get_physical_status(vin, components=['doors', 'windows'])
# Access: physical.doors.lock_state
#         physical.windows.front_left.open
```

---

## Test Data

All examples use the `TestAdapter` which provides mock data:

**Vehicle 1: T7 (Transporter 7)**
- VIN: `WV2ZZZSTZNH009136`
- Type: Combustion
- License Plate: `M-AB 1234`

**Vehicle 2: ID7 (ID.7 Tourer)**
- VIN: `WVWZZZED4SE003938`
- Type: Electric
- License Plate: `M-XY 5678`

---

## Running with Real Data

To use real VW vehicles instead of test data:

1. Configure `src/config.json` with your VW credentials
2. Replace `TestAdapter()` with:
   ```python
   from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
   
   adapter = CarConnectivityAdapter(
       config_path='src/config.json',
       tokenstore_file='token.json'
   )
   ```

**Warning:** Real adapter makes actual API calls to VW servers. Use caching to avoid rate limits!

---

## Recent Improvements

### Version 2024-02 (February 2024)

**1. License Plate Support** ✅
- Added `license_plate` field to `VehicleModel`
- Available in both `list_vehicles()` and `get_vehicle()`
- Can identify vehicles by license plate
- See: `license_plate_demo.py`

**2. Caching System** ✅
- Automatic caching of VW API responses
- Configurable duration (default: 300s / 5min)
- Prevents rate limiting
- Transparent to users (no code changes needed)
- See: `caching_demo.py`

**3. Consolidated API Architecture** ✅
- Reduced from 10+ methods to 4 logical groups
- Better organization and maintainability
- Flexible detail levels and component filtering
- Vehicle-type awareness (electric vs combustion)
- See: `consolidated_api_demo.py`

**4. AI Instructions Externalized** ✅
- Moved from Python code to `AI_INSTRUCTIONS.md`
- Easier to update and maintain
- Better documentation

**5. Removed Redundant Examples** ✅
- Deleted `battery_demo.py` - now covered by `consolidated_api_demo.py`
- Deleted `charging_state_demo.py` - now covered by `consolidated_api_demo.py`
- Deleted `phase1_demo.py` - old API, replaced by new architecture
- Deleted `phase2_demo.py` - old API, replaced by new architecture
- Result: Cleaner, more focused example set

---

## Contributing

When adding new examples:

1. **Use descriptive names:** `<feature>_demo.py`
2. **Include docstring:** Explain what the demo shows
3. **Add print statements:** Make output clear and formatted
4. **Use TestAdapter:** For consistent test data
5. **Update this README:** Add your example to the list

---

## Questions?

- Check the main [README.md](../README.md) for project overview
- See [tests/README.md](../tests/README.md) for testing documentation
- Review [AI_INSTRUCTIONS.md](../src/weconnect_mcp/server/AI_INSTRUCTIONS.md) for MCP tool usage
