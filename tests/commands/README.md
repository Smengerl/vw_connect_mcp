# WeConnect MCP Command Tests

Comprehensive test suite for MCP server vehicle control commands.

## Test Structure

```
tests/commands/
├── test_lock_unlock.py            # 13 tests - Lock/unlock vehicle
├── test_climatization.py          # 13 tests - Start/stop climatization
├── test_charging.py               # 13 tests - Start/stop charging (EV/PHEV)
├── test_lights_horn.py            # 17 tests - Flash lights, honk & flash
└── test_window_heating.py         # 15 tests - Window heating control
```

**Note**: Shared fixtures (`adapter`, `mcp_server`) are defined in `tests/conftest.py` (central location for all test categories).

**Total**: 71 tests ✅

## Command Coverage

All 10 vehicle control commands are tested:

### Lock & Security
- ✅ `lock_vehicle` - Lock all doors
- ✅ `unlock_vehicle` - Unlock all doors

### Climate Control
- ✅ `start_climatization` - Pre-heat/cool vehicle
- ✅ `stop_climatization` - Stop climate control
- ✅ `start_window_heating` - Activate window heating
- ✅ `stop_window_heating` - Deactivate window heating

### Charging (Electric/Hybrid)
- ✅ `start_charging` - Start charging session
- ✅ `stop_charging` - Stop charging session

### Lights & Horn
- ✅ `flash_lights` - Flash headlights (with optional duration)
- ✅ `honk_and_flash` - Honk and flash (with optional duration)

## Test Patterns

Each command test file follows a consistent structure:

### 1. Basic Execution Tests
```python
def test_command_by_vin(adapter):
    """Test command execution by VIN"""
    result = adapter.execute_command(VIN_ELECTRIC, "command_name")
    assert result["success"] is True
```

### 2. Identifier Resolution Tests
```python
@pytest.mark.parametrize("identifier", get_electric_vehicle_identifiers())
def test_command_all_identifiers(adapter, identifier):
    """Test command works with VIN, name, or license plate"""
    result = adapter.execute_command(identifier, "command_name")
    assert result["success"] is True
```

### 3. Error Handling Tests
```python
def test_command_invalid_vehicle(adapter):
    """Test command on non-existent vehicle returns error"""
    result = adapter.execute_command(VIN_INVALID, "command_name")
    assert result["success"] is False
    assert "error" in result
```

### 4. Vehicle Type Tests
```python
def test_command_electric_vehicle(adapter):
    """Test command on electric vehicle"""
    result = adapter.execute_command(VIN_ELECTRIC, "command_name")
    assert result["success"] is True

def test_command_combustion_vehicle(adapter):
    """Test command on combustion vehicle"""
    result = adapter.execute_command(VIN_COMBUSTION, "command_name")
    assert result["success"] is True
```

### 5. MCP Server Registration Tests
```python
@pytest.mark.asyncio
async def test_command_tool_is_registered(mcp_server):
    """Test that command tool is registered in the MCP server"""
    tools = await mcp_server.get_tools()
    assert "command_name" in tools.keys()
```

## Running Tests

### Run all command tests:
```bash
pytest tests/commands/ -v
```

### Run specific command test:
```bash
pytest tests/commands/test_lock_unlock.py -v
pytest tests/commands/test_climatization.py -v
pytest tests/commands/test_charging.py -v
pytest tests/commands/test_lights_horn.py -v
pytest tests/commands/test_window_heating.py -v
```

### Run with coverage:
```bash
pytest tests/commands/ --cov=weconnect_mcp --cov-report=term-missing
```

## Test Data

Tests use `TestAdapter` with 2 mock vehicles:

1. **ID.7 Tourer** (Electric)
   - VIN: `WVWZZZED4SE003938`
   - Name: `ID7 Tourer`
   - License: `M-XY 5678`

2. **Transporter 7** (Combustion)
   - VIN: `WV2ZZZSTZNH009136`
   - Name: `T7`
   - License: `M-AB 1234`

All identifiers (VIN, name, license plate) work interchangeably.

## Shared Fixtures (from tests/conftest.py)

**Note**: Fixtures are centrally defined in `tests/conftest.py` and automatically available to all test files.

### `adapter` Fixture
Provides a `TestAdapter` instance with mock vehicles:
```python
def test_example(adapter):
    result = adapter.execute_command("Golf", "lock")
```

### `mcp_server` Fixture
Provides a FastMCP server instance for registration tests:
```python
@pytest.mark.asyncio
async def test_example(mcp_server):
    tools = await mcp_server.get_tools()
```

## What's Tested

✅ **Command Execution**
- Successful command execution
- Correct response format (`{"success": bool, "message": str}`)
- Error responses for invalid vehicles

✅ **Vehicle Identification**
- Resolution by VIN
- Resolution by vehicle name
- Resolution by license plate
- Parametrized tests for all identifier types

✅ **Error Handling**
- Non-existent vehicle handling
- Invalid command names
- Proper error messages in response

✅ **Vehicle Type Support**
- Electric vehicles (BEV)
- Combustion vehicles
- Hybrid vehicles (PHEV) - same as BEV for commands

✅ **Optional Parameters**
- Duration parameter for flash/honk commands
- Proper kwargs passing to execute_command

✅ **MCP Server Integration**
- Tool registration verification
- All 10 command tools registered
- Async tool listing works

## Test Implementation

Commands use the `execute_command()` method from `AbstractAdapter`:

```python
def execute_command(
    self,
    vehicle_id: str,    # VIN, name, or license plate
    command: str,       # Command name
    **kwargs            # Optional command parameters
) -> Dict[str, Any]:   # {"success": bool, "message": str, "error": str}
```

Mock implementation in `TestAdapter` supports all commands and returns:
- `{"success": True, "message": "Command {name} executed"}` on success
- `{"success": False, "error": "..."}` on error

## Related Documentation

- Main test suite: `tests/README.md`
- Tool tests: `tests/tools/` (71 tests)
- Test data: `tests/test_data.py`
- Mock adapter: `tests/test_adapter.py`
