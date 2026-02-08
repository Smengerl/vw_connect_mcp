# GitHub Copilot Instructions for WeConnect MCP

**Type**: MCP Server (Python) for Volkswagen WeConnect vehicle data and control  
**Architecture**: Modular adapter with mixins (CacheMixin, VehicleResolutionMixin, CommandMixin, StateExtractionMixin)  
**Key Library**: `carconnectivity` (third-party VW API wrapper)  
**Test Suite**: 208 tests - **MUST ALWAYS PASS** before committing

## Technology Stack

- **Python 3.10+** with modern type hints (`dict[str, Any]`, not `Dict`)
- **MCP SDK** for protocol implementation
- **Pydantic** for data models (all fields `Optional` - VW API is unreliable)
- **pytest** for testing - **ALL 208 TESTS MUST PASS**

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

## Testing Guidelines (CRITICAL)

**Golden Rule**: ALL 208 tests MUST pass before committing. No exceptions.

### Test Structure
```
tests/
├── commands/          # Test all 10 command methods (74 tests)
│   ├── test_charging.py
│   ├── test_climatization.py
│   ├── test_lights_horn.py
│   ├── test_lock_unlock.py
│   └── test_window_heating.py
├── tools/            # Test MCP tool layer (76 tests)
│   ├── test_get_battery_status.py
│   ├── test_get_climate_status.py
│   ├── test_get_energy_status.py
│   └── ...
├── test_caching.py   # Cache behavior (12 tests)
├── test_carconnectivity_adapter.py  # Adapter tests
└── test_mcp_server.py  # MCP protocol tests
```

### Running Tests
```bash
# Before every commit - ALL must pass
pytest tests/ -v

# Specific test file
pytest tests/commands/test_climatization.py -v

# With coverage
pytest tests/ --cov=src/weconnect_mcp

# Watch mode during development
pytest-watch tests/
```

### Writing Tests - MANDATORY for New Features

**Rule**: Every new feature MUST have tests covering:
1. ✅ Success case (happy path)
2. ✅ Error case (vehicle not found)
3. ✅ Edge cases (None values, missing data)
4. ✅ Type-specific behavior (BEV vs combustion)

**Example - Adding a New Command**:
```python
# File: tests/commands/test_new_feature.py
import pytest
from weconnect_mcp.adapter import TestAdapter

def test_new_command_success():
    """Test successful command execution."""
    adapter = TestAdapter()
    result = adapter.new_command("TestVehicle")
    
    assert result["success"] is True
    assert "message" in result

def test_new_command_vehicle_not_found():
    """Test error when vehicle doesn't exist."""
    adapter = TestAdapter()
    result = adapter.new_command("NonExistent")
    
    assert result["success"] is False
    assert "error" in result
    assert "not found" in result["error"].lower()

def test_new_command_invalidates_cache():
    """Test that command invalidates cache."""
    adapter = TestAdapter()
    
    # Execute command
    adapter.new_command("TestVehicle")
    
    # Verify cache was invalidated
    assert adapter._last_fetch_time is None
```

**Example - Adding a New State Getter**:
```python
# File: tests/tools/test_get_new_status.py
import pytest
from weconnect_mcp.adapter import TestAdapter

def test_get_new_status_success():
    """Test successful status retrieval."""
    adapter = TestAdapter()
    status = adapter.get_new_status("TestVehicle")
    
    assert status is not None
    # Test specific fields
    assert hasattr(status, 'field_name')

def test_get_new_status_vehicle_not_found():
    """Test None returned for non-existent vehicle."""
    adapter = TestAdapter()
    status = adapter.get_new_status("NonExistent")
    
    assert status is None

def test_get_new_status_handles_none_values():
    """Test graceful handling of None values from VW API."""
    adapter = TestAdapter()
    status = adapter.get_new_status("VehicleWithPartialData")
    
    # Should not crash, should return model with None fields
    assert status is not None
```

### Test Development Workflow

1. **Write test first** (TDD approach recommended)
2. **Run test** - should fail (red)
3. **Implement feature** - minimum code to pass
4. **Run test** - should pass (green)
5. **Refactor** - improve code quality
6. **Run ALL tests** - ensure nothing broke
7. **Commit only if all 208 tests pass**

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

### Integration Tests

For real VW API testing, use scripts (not pytest):
```bash
# Located in scripts/carconnectivity/
./scripts/carconnectivity/test_vehicle_commands.py ID7 lock_vehicle
./scripts/carconnectivity/test_vehicle_commands.py Golf get_battery_status
```

## Development Scripts

Located in `scripts/carconnectivity/` for manual testing with real VW API:

```bash
# Test any command
./scripts/carconnectivity/test_vehicle_commands.py <vehicle_id> <command>

# Examples
./scripts/carconnectivity/test_vehicle_commands.py ID7 start_charging
./scripts/carconnectivity/test_vehicle_commands.py Golf lock_vehicle
./scripts/carconnectivity/test_vehicle_commands.py T7 get_battery_status

# List all available commands
./scripts/carconnectivity/test_vehicle_commands.py --help
```

**When to use scripts**:
- Manual testing during development
- Testing with real vehicles
- Debugging VW API behavior
- Verifying commands work end-to-end

**When NOT to use scripts**:
- Automated testing (use pytest instead)
- CI/CD pipelines (use pytest)
- Before commits (use pytest)

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

### ✅ DO: Use Descriptive Variable Names
```python
# Good
charging_power_kw = charging.power.value if charging.power is not None else None

# Bad
p = charging.power.value
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
- Run tests before committing: `pytest tests/ -v`

### Branches
- `main`: Production-ready code
- Feature branches: `feature/description`
- Bugfix branches: `fix/description`

## Performance Considerations

1. **Caching is critical** - VW API has strict rate limits
2. **Lazy loading** - Don't fetch data until needed
3. **Batch operations** - Get all vehicles at once, not one by one
4. **Connection pooling** - `carconnectivity` handles this

## Security Notes

- **Credentials**: Never commit `config.json` or `.netrc` files
- **Token storage**: `tokenstore.json` is gitignored
- **Logging**: Don't log sensitive data (VINs OK, tokens NOT OK)

## When to Ask for Help

- Adding new vehicle features? Check `carconnectivity` library docs first
- MCP protocol questions? Check MCP SDK documentation
- VW API behaving weird? It's normal - VW API is unreliable, handle gracefully

## Quick Reference

### Add New Command
1. Add method to `CommandMixin` in `mixins/command_mixin.py`
2. Add tool definition in `server/tools.py`
3. Add test in `tests/commands/test_*.py`
4. Update `AI_INSTRUCTIONS.md`
5. Run tests: `pytest tests/ -v`

### Add New State Extraction
1. Add method to `StateExtractionMixin` in `mixins/state_extraction_mixin.py`
2. Add Pydantic model to `AbstractAdapter` if needed
3. Add public method to main adapter
4. Add tool in `server/tools.py`
5. Add test in `tests/tools/test_*.py`

### Debug MCP Server
```bash
# Run server in debug mode
python -m weconnect_mcp.server

# Test with MCP inspector
npx @modelcontextprotocol/inspector python -m weconnect_mcp.server
```

---

**Remember**: This is an MCP server for AI assistants. The code should be reliable, well-typed, and handle VW API flakiness gracefully. When in doubt, return `None` or error dict rather than crashing.
