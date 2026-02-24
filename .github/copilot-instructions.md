# GitHub Copilot Instructions for WeConnect MCP

**Type**: MCP Server (Python) for Volkswagen WeConnect vehicle data and control  
**Architecture**: Modular adapter with mixins (CacheMixin, VehicleResolutionMixin, CommandMixin, StateExtractionMixin)  
**Key Library**: `carconnectivity` (third-party VW API wrapper)  
**Languages**: Python 3.10+ (tested with Python 3.14)
**Project Size**: ~50 files, ~5000 lines of code
**Test Suite**: 215 tests (197 mock + 18 real API) - **197 MOCK TESTS MUST PASS** before committing

## Repository Overview

**Purpose**: MCP (Model Context Protocol) server that exposes Volkswagen WeConnect vehicle data and control commands to AI assistants (Claude, Copilot, etc.)

**Key Dependencies**:
- `carconnectivity` (0.9.2) - Third-party VW API wrapper
- `mcp` (1.25.0) - Model Context Protocol SDK
- `pydantic` (2.12.5) - Data validation
- `pytest` (9.0.2) - Testing framework
- `fastmcp` (2.14.1) - Fast MCP server implementation

## Technology Stack

- **Python 3.10+** with modern type hints (`dict[str, Any]`, not `Dict`)
- **MCP SDK** for protocol implementation
- **Pydantic** for data models (all fields `Optional` - VW API is unreliable)
- **pytest** for testing - **197 MOCK TESTS MUST PASS** (18 real API tests will fail without VW credentials)

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

## First-Time Setup (For Developers)

⚠️ **IMPORTANT FOR CODING AGENTS**: The developer must have already completed this setup with real VW credentials. **DO NOT modify or create config.json** - it contains the developer's VW credentials and should never be committed to the repository.

**For developers setting up locally (ONE TIME ONLY)**:

```bash
# 1. Clone and navigate to repository
git clone https://github.com/Smengerl/weconnect_mvp.git
cd weconnect_mvp

# 2. Setup virtual environment and install dependencies (~30 seconds)
./scripts/setup.sh
# This creates .venv/, installs dependencies, and creates config.json from example

# 3. Edit config.json with YOUR REAL VW WeConnect credentials
nano src/config.json  # or code src/config.json
# Required: username (VW email), password, spin (4-digit S-PIN)

# 4. Activate virtual environment
source .venv/bin/activate

# 5. Verify setup - run mock tests (~7 seconds, expect 197 passed)
./scripts/test.sh --skip-slow
```

**Expected output**: `197 passed, 18 deselected` (real API tests are skipped)

## Build & Test Commands (Use These Before Committing)

### Testing (CRITICAL)

**ALWAYS use `./scripts/test.sh` - do NOT run pytest directly**

```bash
# Fast mock tests only (~7 seconds) - use this during development
# These tests use TestAdapter (fake data) and DO NOT require VW credentials
./scripts/test.sh --skip-slow
# Expected: 197 passed, 18 deselected

# All tests including real API tests (~30 seconds)
# These WILL FAIL unless config.json has valid VW credentials
# DO NOT use in automated environments without credentials
./scripts/test.sh
# Expected with credentials: 215 passed
# Expected without credentials: 197 passed, 18 failed

# Verbose output for debugging
./scripts/test.sh --skip-slow -v
```

**Test Categories**:
- **Mock tests (197)**: Use `TestAdapter` with fake data - no VW credentials needed
  - `tools/` (76 tests) - Adapter method tests
  - `commands/` (74 tests) - Command execution tests  
  - `resources/` (27 tests) - MCP resource tests
  - `test_caching.py` (12 tests) - Cache behavior
  - `test_mcp_server.py` (8 tests) - MCP protocol
- **Real API tests (18)**: Marked with `@pytest.mark.real_api` - require valid VW credentials
  - `real_api/` directory - WILL FAIL without credentials

**Pre-commit requirement**: `./scripts/test.sh --skip-slow` must show **197 passed**

**IMPORTANT**: Real API tests (`./scripts/test.sh` without `--skip-slow`) will fail for agents working remotely or without VW credentials configured. This is expected and normal. Only mock tests need to pass for code contributions.

### Running the Server

```bash
# Foreground (logs to console) - use for development/debugging
./scripts/start_server_fg.sh

# Background (logs to logs/server.log) - use for integration testing
./scripts/start_server_bg.sh
./scripts/stop_server_bg.sh  # Stop background server

# Direct invocation with custom settings
python -m weconnect_mcp.cli.mcp_server_cli src/config.json --log-level DEBUG --transport stdio

# Test with MCP inspector tool
npx @modelcontextprotocol/inspector python -m weconnect_mcp.server
```

**Server startup time**: 10-30 seconds on first run (VW API connection requires valid credentials)

### No Build Step Required

This is a pure Python project - **no compilation needed**. Just install dependencies with `./scripts/setup.sh` and run.

## Project Structure & Key Files

```
weconnect_mvp/
├── src/weconnect_mcp/              # Main package
│   ├── adapter/                    # Core adapter implementation
│   │   ├── abstract_adapter.py     # Base class + Pydantic models (VehicleModel, etc.)
│   │   ├── carconnectivity_adapter.py  # ⭐ Main adapter (mixin composition)
│   │   ├── test_adapter.py         # ⭐ Mock adapter for testing (fake data)
│   │   └── mixins/                 # Mixin pattern components
│   │       ├── cache_mixin.py      # 5-min caching with auto-invalidation
│   │       ├── vehicle_resolution_mixin.py  # VIN/name → vehicle lookup
│   │       ├── command_mixin.py    # ⭐ 10 vehicle commands (lock, climate, charging, etc.)
│   │       └── state_extraction_mixin.py  # ⭐ Extract state from carconnectivity
│   ├── server/                     # MCP server implementation
│   │   ├── mcp_server.py           # FastMCP server setup
│   │   ├── tools.py                # ⭐ MCP tool definitions (18 tools)
│   │   └── resources.py            # ⭐ MCP resource definitions (14 resources)
│   └── cli/                        # CLI entry points
│       └── mcp_server_cli.py       # Main server CLI with argparse
├── tests/                          # 215 tests (197 mock + 18 real API)
│   ├── conftest.py                 # ⭐ Central fixtures (mock_adapter, real_adapter)
│   ├── tools/                      # 76 tests for adapter methods
│   ├── commands/                   # 74 tests for vehicle commands
│   ├── resources/                  # 27 tests for MCP resources
│   ├── real_api/                   # 18 real VW API tests (require credentials)
│   ├── test_caching.py             # 12 cache invalidation tests
│   ├── test_mcp_server.py          # 8 MCP protocol tests
│   └── README.md                   # Detailed test documentation
├── scripts/                        # Development scripts
│   ├── setup.sh                    # ⭐ ONE-TIME: Setup venv + dependencies
│   ├── test.sh                     # ⭐ Run pytest with proper markers
│   ├── start_server_fg.sh          # Start server (foreground, logs to console)
│   ├── start_server_bg.sh          # Start server (background, logs to file)
│   ├── stop_server_bg.sh           # Stop background server
│   └── create_*_config.sh          # Generate AI assistant configs
├── src/config.json                 # ⚠️ VW credentials (gitignored, NEVER commit!)
├── src/config.example.json         # Template for config.json
├── requirements.txt                # Python dependencies (pip install -r)
├── pytest.ini                      # Pytest configuration (markers, async mode)
├── README.md                       # User-facing documentation
├── CONTRIBUTING.md                 # Contribution guidelines
└── .github/copilot-instructions.md # This file
```

**Configuration Files**:
- `pytest.ini` - Defines test markers (`real_api`, `slow`), async mode
- `src/config.json` - **NEVER EDIT OR COMMIT** - contains VW credentials
- `requirements.txt` - All Python dependencies

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
├── resources/        # Test MCP resources (27 tests)
├── real_api/         # Real VW API tests (18 tests, require credentials)
├── test_caching.py   # Cache behavior (12 tests)
├── test_adapter.py   # Adapter tests
└── test_mcp_server.py  # MCP protocol tests (8 tests)
```

### Running Tests
```bash
# Before every commit - ALL mock tests must pass
./scripts/test.sh --skip-slow
# Expected: 197 passed, 18 deselected in ~7 seconds

# Specific test file
pytest tests/commands/test_climatization.py -v

# With coverage
pytest tests/ --cov=src/weconnect_mcp -m "not real_api"

# Real API tests (will fail without VW credentials)
./scripts/test.sh
# Expected with credentials: 215 passed
# Expected without credentials: 197 passed, 18 failed (real_api tests)
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

### Integration Tests

For real VW API testing, use scripts (not pytest):
```bash
# Located in scripts/
./scripts/vehicle_command.sh ID7 lock_vehicle
./scripts/vehicle_command.sh Golf get_battery_status
```

## Development Scripts

Located in `scripts/` for setup, testing, and server management:

```bash
# Setup & Environment
./scripts/setup.sh              # ONE-TIME: Create venv, install deps, create config
./scripts/activate_venv.sh      # Activate virtual environment

# Testing
./scripts/test.sh --skip-slow   # Run mock tests only (~7s, 197 tests)
./scripts/test.sh               # Run all tests including real API (~30s, 215 tests)
./scripts/test.sh --skip-slow -v # Verbose mode

# Server Management
./scripts/start_server_fg.sh    # Start in foreground (logs to console)
./scripts/start_server_bg.sh    # Start in background (logs to logs/server.log)
./scripts/stop_server_bg.sh     # Stop background server

# AI Integration Configuration
./scripts/create_claude_config.sh           # Generate Claude Desktop config
./scripts/create_github_copilot_config.sh   # Generate GitHub Copilot config
./scripts/create_copilot_desktop_config.sh  # Generate Copilot Desktop config

# Manual Testing (requires real VW credentials)
./scripts/vehicle_command.sh <vehicle_id> <command>
# Examples:
./scripts/vehicle_command.sh ID7 start_charging
./scripts/vehicle_command.sh Golf lock_vehicle
```

**When to use scripts**:
- `setup.sh` - First time setup only (developer, not agent)
- `test.sh` - Always use for testing (not `pytest` directly)
- `start_server_*.sh` - When testing server functionality
- `vehicle_command.sh` - Manual testing with real vehicles during development

**When NOT to use scripts**:
- In CI/CD (no scripts configured yet)
- In automated environments without VW credentials

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

## Validation & CI/CD

**No GitHub Actions or automated CI/CD configured**

Manual pre-commit validation steps:
1. Run mock tests: `./scripts/test.sh --skip-slow` → Must show **197 passed, 18 deselected**
2. Visual code review for style compliance
3. Check no sensitive data in commits (`config.json` is gitignored)

**Real API tests**: Marked with `@pytest.mark.real_api`, require valid VW credentials in `src/config.json`. These will fail in:
- Remote/cloud environments without credentials
- CI/CD pipelines (no credentials available)
- Any environment where `config.json` doesn't contain real VW account details

This is **expected behavior** - only mock tests need to pass for code contributions.

---

**Remember**: This is an MCP server for AI assistants. The code should be reliable, well-typed, and handle VW API flakiness gracefully. When in doubt, return `None` or error dict rather than crashing.
