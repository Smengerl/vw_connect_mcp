# GitHub Copilot Instructions for WeConnect MCP

**Type**: MCP Server (Python) for Volkswagen WeConnect vehicle data and control  
**Architecture**: Modular adapter with mixins (CacheMixin, VehicleResolutionMixin, CommandMixin, StateExtractionMixin)  
**Key Library**: `carconnectivity` (third-party VW API wrapper)  
**Languages**: Python 3.10+ with modern type hints (`dict[str, Any]`, not `Dict`)  
**Test Suite**: 215 tests (197 mock + 18 real API) - **197 MOCK TESTS MUST PASS** before committing

> For setup, usage, scripts, project structure, and test documentation see **README.md** and **tests/README.md**.

## Code Style (Non-Negotiable)

**Type Hints**: Always required for parameters and return values
```python
def get_vehicle(vehicle_id: str) -> Optional[VehicleModel]:  # ✅ Good
def get_vehicle(vehicle_id):  # ❌ Bad - no types
```

**Naming**: `snake_case.py`, `PascalCase` classes, `snake_case()` functions, `UPPER_SNAKE_CASE` constants

**Imports**: Standard library → Third-party → Local imports

**None Handling**: ALWAYS check for `None` - VW API is unreliable
```python
# ✅ Good
battery = vehicle.battery
if battery is not None:
    level = battery.level.value if battery.level is not None else None

# ❌ Bad - will crash
level = vehicle.battery.level.value
```

## Architecture (Mixin Pattern)

Main adapter uses **multiple inheritance** to compose functionality:

```python
class CarConnectivityAdapter(
    CacheMixin,              # Caching with 5-min TTL
    VehicleResolutionMixin,  # Resolve VIN/name to vehicle
    CommandMixin,            # 10 vehicle control commands
    StateExtractionMixin,    # Extract state from carconnectivity
    AbstractAdapter          # Base class
):
    ...
```

**Key Points**:
- Each mixin = single responsibility
- Type errors in isolated mixins are OK (resolved when combined)
- All Pydantic models use `Optional` fields (VW API unreliable)

## Important Domain Knowledge

### Vehicle Identification
- **Name**: `"Golf"`, `"ID.7"` (preferred for readability)
- **VIN**: `"WVWZZZAUZPW123456"` (unique identifier)
- **License Plate**: ⚠️ **NOT SUPPORTED** - VW API doesn't provide this (as of Feb 2026)

### Vehicle Types
- **BEV** (Battery Electric Vehicle): Full electric (e.g., ID.7)
- **PHEV** (Plug-in Hybrid): Electric + combustion
- **Combustion**: Traditional fuel only

**Key Point**: Battery/charging tools only work for BEV/PHEV!

### Caching Strategy
- **Duration**: 5 minutes (300 seconds) via `CacheMixin`
- **Purpose**: Respect VW API rate limits
- **Auto-invalidation**: Cache invalidates after any command (lock, climate, charging, etc.)

### Command Parameters
- **Climate**: `target_temp_celsius` (float) - `start_climatization("Golf", 22.0)`
- **Lights**: `duration_seconds` (int) - `flash_lights("Golf", 10)`
- **Honk**: `duration_seconds` (int) - `honk_and_flash("Golf", 5)`

### Battery State of Charge (SOC) - Fallback Mechanism

The battery SOC (State of Charge) is retrieved from **two sources** with automatic fallback:

1. **Primary Source**: `vehicle.drives.drives['electric'].battery.level` (used in `_get_range_info()`)
2. **Fallback Source**: `vehicle.battery.level` (used in `_get_charging_state()`)

**Why fallback is needed**: VW API is unreliable. Sometimes `drives` data is unavailable (e.g., when vehicle is in low-power mode or hasn't communicated with WeConnect recently), but `battery` data is still present.

**Implementation** (in `get_energy_status()`):
```python
# Try primary source (drives)
if range_info and range_info.electric_drive:
    battery_level = range_info.electric_drive.battery_level_percent

# Fallback to charging state if drives data unavailable
if battery_level is None and charging_state and charging_state.current_soc_percent is not None:
    battery_level = charging_state.current_soc_percent
```

**Important**: SOC should be available **even when not charging**! The fallback ensures maximum data availability.

## Testing Guidelines (CRITICAL)

**Golden Rule**: All 197 mock tests MUST pass before committing. No exceptions.  
**Always use `./scripts/test.sh --skip-slow`** (not `pytest` directly) — see `tests/README.md` for full test structure and commands.

### Writing Tests - MANDATORY for New Features

**Rule**: Every new feature MUST have tests covering:
1. ✅ Success case (happy path)
2. ✅ Error case (vehicle not found)
3. ✅ Edge cases (None values, missing data)
4. ✅ Type-specific behavior (BEV vs combustion)

**Example - Adding a New Command**:
```python
# File: tests/commands/test_new_feature.py
from weconnect_mcp.adapter import TestAdapter

def test_new_command_success():
    adapter = TestAdapter()
    result = adapter.new_command("TestVehicle")
    assert result["success"] is True
    assert "message" in result

def test_new_command_vehicle_not_found():
    adapter = TestAdapter()
    result = adapter.new_command("NonExistent")
    assert result["success"] is False
    assert "not found" in result["error"].lower()

def test_new_command_invalidates_cache():
    adapter = TestAdapter()
    adapter.new_command("TestVehicle")
    assert adapter._last_fetch_time is None
```

**Example - Adding a New State Getter**:
```python
# File: tests/tools/test_get_new_status.py
from weconnect_mcp.adapter import TestAdapter

def test_get_new_status_success():
    adapter = TestAdapter()
    status = adapter.get_new_status("TestVehicle")
    assert status is not None

def test_get_new_status_vehicle_not_found():
    adapter = TestAdapter()
    assert adapter.get_new_status("NonExistent") is None

def test_get_new_status_handles_none_values():
    adapter = TestAdapter()
    status = adapter.get_new_status("VehicleWithPartialData")
    assert status is not None  # Should not crash, fields may be None
```

### Test Development Workflow

1. **Write test first** (TDD approach recommended)
2. **Run test** - should fail (red)
3. **Implement feature** - minimum code to pass
4. **Run test** - should pass (green)
5. **Refactor** - improve code quality
6. **Run ALL tests** - ensure nothing broke: `./scripts/test.sh --skip-slow`
7. **Commit only if 197 mock tests pass**

### Using TestAdapter (Mock)

Always use `TestAdapter` for unit tests (no real API calls):

```python
from weconnect_mcp.adapter import TestAdapter

adapter = TestAdapter()  # Mock adapter with fake data

# Commands return success/error dicts
result = adapter.lock_vehicle("TestVehicle")
assert result["success"] is True

# State methods return Pydantic models or None
doors = adapter.get_vehicle_doors("TestVehicle")
assert doors.lock_state == "locked"
```

For real VW API testing, use `./scripts/vehicle_command.sh <vehicle_id> <command>` (requires VW credentials).

## Common Patterns & Anti-Patterns

### ✅ DO: Handle None Values
```python
# Good - VW API often returns incomplete data
battery = vehicle.battery
if battery is not None:
    level = battery.level.value if battery.level is not None else None

# Bad - will crash
level = vehicle.battery.level.value
```

### ✅ DO: Use Type Guards
```python
# Good - check instance type before using type-specific features
if isinstance(vehicle, ElectricVehicle):
    charging = vehicle.charging  # Safe: only EVs have charging
```

### ✅ DO: Invalidate Cache After Commands
```python
# Good - implemented in CommandMixin
def lock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
    # ... execute command ...
    self.invalidate_cache()  # Force fresh data on next read
    return {"success": True}
```

## MCP-Specific Guidelines

### Tool Implementation
Tools are defined in `tools.py` and call adapter methods:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_battery_status":
        vehicle_id = arguments.get("vehicle_id")
        result = adapter.get_battery_status(vehicle_id)
        return [TextContent(type="text", text=json.dumps(result.model_dump()))]
```

**Pattern**:
1. Extract arguments from `arguments` dict
2. Call adapter method
3. Convert Pydantic model to dict with `.model_dump()`
4. Return as JSON string in `TextContent`

### Error Handling
```python
try:
    result = adapter.some_method(vehicle_id)
    if result is None:
        return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
    return [TextContent(type="text", text=json.dumps(result.model_dump()))]
except Exception as e:
    return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

## Logging

Use Python logging (configured in `carconnectivity_adapter.py`):

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("Important state change")
logger.warning("Unexpected but handled")
logger.error("Error that needs attention")
```

**MCP Requirement**: All logs to `stderr` (not `stdout`) because MCP uses `stdout` for protocol.

## Documentation

### Docstrings
Use Google-style docstrings:

```python
def get_vehicle_info(self, vehicle_id: str) -> Optional[VehicleModel]:
    """Get basic vehicle information.
    
    Args:
        vehicle_id: Vehicle name or VIN
        
    Returns:
        VehicleModel with basic info, or None if not found
        
    Example:
        >>> info = adapter.get_vehicle_info("Golf")
        >>> print(info.model)
        "Golf 8"
    """
```

### Comments
- Explain **why**, not **what** (code should be self-explanatory)
- Document workarounds for VW API quirks
- Mark TODOs with `# TODO: description`

## Git Workflow

### Commits
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Keep commits atomic (one logical change)
- Run tests before committing: `./scripts/test.sh --skip-slow`

## Quick Reference

### Add New Command
1. Add method to `CommandMixin` in `mixins/command_mixin.py`
2. Add tool definition in `server/tools.py`
3. Add test in `tests/commands/test_*.py`
4. Update `AI_INSTRUCTIONS.md`
5. Run tests: `./scripts/test.sh --skip-slow` (197 must pass)

### Add New State Extraction
1. Add method to `StateExtractionMixin` in `mixins/state_extraction_mixin.py`
2. Add Pydantic model to `AbstractAdapter` if needed
3. Add public method to main adapter
4. Add tool in `server/tools.py`
5. Add test in `tests/tools/test_*.py`
6. Run tests: `./scripts/test.sh --skip-slow` (197 must pass)

### Debug MCP Server
```bash
# Run server in debug mode
python -m weconnect_mcp.server

# Test with MCP inspector
npx @modelcontextprotocol/inspector python -m weconnect_mcp.server
```

---

**Remember**: This is an MCP server for AI assistants. The code should be reliable, well-typed, and handle VW API flakiness gracefully. When in doubt, return `None` or error dict rather than crashing.
