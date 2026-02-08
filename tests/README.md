# WeConnect MCP Test Suite

Comprehensive test suite for the WeConnect MCP server implementation.

## Quick Stats

| Category | Tests | File### 5. Adapter Tests (`test_adapter.py`)

**Purpose**: Mock adapter implementation for testing.

**Key Features**:
- 2 mock vehicles (ID.7 Tourer electric, Transporter 7 combustion)
- Realistic test data matching real-world scenarios
- Implements all AbstractAdapter methods
- Supports all consolidated methods (get_physical_status, get_energy_status, etc.)
- Mock execute_command implementation for command testing

### 6. Test Data (`test_data.py`) |
|----------|-------|-------|---------|
| **Tools** | 76 | 7 | Data retrieval operations |
| **Commands** | 71 | 5 | Vehicle control operations |
| **Resources** | 22 | 2 | MCP resource protocol |
| **Integration** | 13+ | 3 | Real API & E2E tests |
| **Total** | **169+** | **17+** | Complete coverage |

**All tests passing** ✅

## Test Structure

```
tests/
├── conftest.py         # Shared fixtures for ALL tests ⭐
│
├── tools/              # MCP Tool Tests (76 tests) ✅
│   ├── test_list_vehicles.py          # 5 tests
│   ├── test_get_vehicle.py            # 12 tests
│   ├── test_get_physical_status.py    # 14 tests
│   ├── test_get_energy_status.py      # 16 tests
│   ├── test_get_climate_status.py     # 18 tests
│   ├── test_maintenance.py            # 6 tests
│   └── test_position.py               # 5 tests
│
├── commands/           # MCP Command Tests (71 tests) ✅
│   ├── test_lock_unlock.py            # 13 tests
│   ├── test_climatization.py          # 13 tests
│   ├── test_charging.py               # 13 tests
│   ├── test_lights_horn.py            # 17 tests
│   └── test_window_heating.py         # 15 tests
│
├── resources/          # MCP Resource Tests (22 tests) ✅
│   ├── test_list_vehicles.py          # 7 tests
│   └── test_vehicle_state.py          # 15 tests
│
├── test_adapter.py                # TestAdapter mock implementation
├── test_data.py                   # Central test data configuration
├── test_carconnectivity_adapter.py # Integration tests (real VW API)
├── test_mcp_server.py             # MCP server protocol tests
└── test_full_roundtrip.py         # End-to-end integration tests
```

## Test Categories

### 1. Tool Tests (`tests/tools/`)

**Purpose**: Validate individual MCP tool implementations using mock data.

**Characteristics**:
- Uses `TestAdapter` for deterministic mock data
- Fast execution (no API calls)
- Comprehensive coverage of all tool features
- Tests both happy paths and error cases
- Validates MCP server tool registration

**Run**: `pytest tests/tools/ -v`

**Coverage**:
- ✅ list_vehicles - List all available vehicles
- ✅ get_vehicle - Get vehicle info (BASIC/FULL details)
- ✅ get_physical_status - Doors, windows, tyres, lights
- ✅ get_energy_status - Battery, charging, range
- ✅ get_climate_status - Climatization, window heating
- ✅ get_maintenance_info - Inspection and oil service schedules
- ✅ get_position - GPS coordinates and heading

### 2. Command Tests (`tests/commands/`)

**Purpose**: Validate MCP command implementations for vehicle control.

**Characteristics**:
- Uses `TestAdapter` for deterministic mock data
- Fast execution (no API calls)
- Tests all 10 vehicle control commands
- Tests identifier resolution (VIN, name, license plate)
- Validates MCP server tool registration

**Run**: `pytest tests/commands/ -v`

**Coverage**:
- ✅ lock_vehicle / unlock_vehicle - Door lock control
- ✅ start_climatization / stop_climatization - Climate control
- ✅ start_charging / stop_charging - Charging control (EV/PHEV)
- ✅ flash_lights / honk_and_flash - Lights and horn
- ✅ start_window_heating / stop_window_heating - Window heating

**See**: `tests/commands/README.md` for detailed documentation

### 3. Resource Tests (`tests/resources/`)

**Purpose**: Validate MCP resource implementations for data access.

**Characteristics**:
- Uses `TestAdapter` for deterministic mock data
- Fast execution (no API calls)
- Tests MCP resource protocol
- Tests resource templates with parameters
- Validates data consistency with adapter

**Run**: `pytest tests/resources/ -v`

**Coverage**:
- ✅ data://list_vehicles - List all vehicles resource
- ✅ data://state/{vehicle_id} - Vehicle state resource template

**See**: `tests/resources/README.md` for detailed documentation

### 4. Shared Fixtures (`conftest.py`)

**Purpose**: Central fixture definitions for all test categories.

**Location**: `tests/conftest.py` (root of tests directory)

**Fixtures provided**:
- `adapter`: TestAdapter instance with 2 mock vehicles
- `mcp_server`: FastMCP server with all tools, commands, and resources
- `mcp_client`: Connected MCP client for async resource/tool access

**Benefits**:
- No duplication across test directories
- Single source of truth for test fixtures
- Automatic availability in all subdirectories (pytest mechanism)
- Easy maintenance and updates

**Usage**: Simply declare fixtures as function parameters in any test:
```python
def test_example(adapter):
    vehicles = adapter.list_vehicles()
    
async def test_resource(mcp_client):
    result = await mcp_client.read_resource("data://list_vehicles")
```

### 5. Adapter Tests (`test_adapter.py`)

**Purpose**: Mock adapter implementation for testing.

**Key Features**:
- 2 mock vehicles (ID.7 Tourer electric, Transporter 7 combustion)
- Realistic test data matching real-world scenarios
- Implements all AbstractAdapter methods
- Consolidated and legacy methods

### 3. Test Data (`test_data.py`)

**Purpose**: Centralized test data configuration.

**Contains**:
- Vehicle identifiers (VINs, names, license plates)
- Expected values for all test scenarios
- Helper functions for parametrized tests

**Benefits**:
- Single source of truth
- Easy updates when mock data changes
- Prevents test failures from inconsistent expectations

### 4. Integration Tests (`test_carconnectivity_adapter.py`)

**Purpose**: Validate CarConnectivityAdapter with **REAL VW API**.

⚠️ **Requirements**:
- Valid VW account credentials in `src/config.json`
- Internet connection
- Real vehicle(s) in account

**Run**: `pytest tests/test_carconnectivity_adapter.py -v`

**What's tested**:
- Real API authentication and connection
- Vehicle data retrieval from VW servers
- All consolidated adapter methods
- Real-world data validation

### 5. MCP Server Tests (`test_mcp_server.py`)

**Purpose**: Validate FastMCP server implementation.

**What's tested**:
- MCP resource registration
- MCP tool registration
- Protocol communication
- JSON serialization
- Client-server interaction

**Run**: `pytest tests/test_mcp_server.py -v`

### 6. Full Roundtrip Tests (`test_full_roundtrip.py`)

**Purpose**: End-to-end validation of complete MCP stack.

**Flow**: VW API → Adapter → MCP Server → MCP Client → Tests

⚠️ **Requirements**: Same as integration tests (real VW API)

**Run**: `pytest tests/test_full_roundtrip.py -v`

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Tool Tests Only (Fast)
```bash
pytest tests/tools/ -v
```

### Command Tests Only (Fast)
```bash
pytest tests/commands/ -v
```

### Resource Tests Only (Fast)
```bash
pytest tests/resources/ -v
```

### Integration Tests Only (Requires VW API)
```bash
pytest tests/test_carconnectivity_adapter.py tests/test_full_roundtrip.py -v
```

### Specific Test File
```bash
pytest tests/tools/test_get_vehicle.py -v
```

### Specific Test Function
```bash
pytest tests/tools/test_get_vehicle.py::test_get_vehicle_basic_details_electric -v
```

### With Coverage
```bash
pytest tests/ --cov=src/weconnect_mcp --cov-report=html
```

### With Debugging Output
```bash
pytest tests/tools/ -v -s --log-cli-level=DEBUG
```

## Test Data

### Mock Vehicles (TestAdapter)

**Electric Vehicle: ID.7 Tourer**
- VIN: `WVWZZZED4SE003938`
- Name: `ID7`
- License Plate: `M-XY 5678`
- Battery: 80%, 312km range
- Status: Active heating (22°C), parked in Munich
- Features: Charging capable, no oil service needed

**Combustion Vehicle: Transporter 7**
- VIN: `WV2ZZZSTZNH009136`
- Name: `T7`
- License Plate: `M-AB 1234`
- Tank: 68%, 650km range (diesel)
- Status: Climatization off, parked in Berlin
- Features: Oil service scheduled

## Fixtures

### Shared Fixtures (`tests/tools/conftest.py`)
- `adapter` - TestAdapter with 2 mock vehicles
- `mcp_server` - FastMCP server with registered tools

### Integration Fixtures (`test_carconnectivity_adapter.py`)
- `config_path` - Path to VW credentials (src/config.json)
- `tokenstore_file` - OAuth token cache (tmp/tokenstore)
- `adapter` - CarConnectivityAdapter with real VW API

### Server Fixtures (`test_mcp_server.py`, `test_full_roundtrip.py`)
- `mockdata_mcp_server` - Server with TestAdapter
- `mockdata_mcp_client` - Connected MCP client
- `mcp_server` - Server with real API adapter
- `mcp_client` - Client for roundtrip tests

## Best Practices

### Adding New Tests

1. **Tool Tests**: Add to `tests/tools/test_<tool_name>.py`
   - Use `adapter` fixture (auto-available via conftest.py)
   - Import expected values from `tests.test_data`
   - Follow existing naming conventions
   - Add MCP registration test

2. **Update Test Data**: Modify `tests/test_data.py`
   - Add new expected values
   - Update if TestAdapter mock data changes
   - Keep consistent with actual adapter output

3. **Integration Tests**: Add to appropriate integration file
   - Use `@pytest.mark.asyncio` for async tests
   - Skip if no VW API access: `@pytest.mark.skipif(...)`
   - Document VW API requirements

### Test Naming

- **Test files**: `test_<feature>.py`
- **Test functions**: `test_<feature>_<scenario>()`
- **Fixtures**: Descriptive names with docstrings

### Documentation

- Every test file has a comprehensive header
- Fixtures have detailed docstrings
- Complex tests have inline comments
- Expected values are documented in test_data.py

## Consolidated Methods

The adapter implements consolidated methods that replace multiple old methods:

### get_vehicle()
Replaces: `get_vehicle_info`, `get_vehicle_type`

### get_physical_status()
Replaces: `get_doors_state`, `get_windows_state`, `get_tyres_state`, `get_lights_state`

### get_energy_status()
Replaces: `get_charging_state`, `get_range_info`, `get_battery_status`

### get_climate_status()
Replaces: `get_climatization_state`, `get_window_heating_state`

### Standalone Methods
- `list_vehicles()`
- `get_maintenance_info()`
- `get_position()`

## Current Status

✅ **169 fast tests passing** (100%)
- 76 Tool tests
- 71 Command tests  
- 22 Resource tests

⚠️ Integration tests require valid VW API credentials

## Test Coverage Summary

### MCP Protocol Components

| Component | Implemented | Tested | Coverage |
|-----------|-------------|--------|----------|
| **Tools** | 24 tools | 76 tests | ✅ 100% |
| **Commands** | 10 commands | 71 tests | ✅ 100% |
| **Resources** | 2 resources | 22 tests | ✅ 100% |

### Tool Categories

| Category | Tools | Tests | Purpose |
|----------|-------|-------|---------|
| Core Info | 4 | 17 | Vehicle identification & type |
| Physical | 4 | 14 | Doors, windows, tyres, lights |
| Energy | 3 | 16 | Battery, charging, range |
| Climate | 2 | 18 | Climatization, heating |
| Maintenance | 1 | 6 | Service schedules |
| Location | 1 | 5 | GPS position |

### Command Categories

| Category | Commands | Tests | Purpose |
|----------|----------|-------|---------|
| Lock & Security | 2 | 13 | Lock/unlock doors |
| Climate Control | 4 | 26 | Climatization, window heating |
| Charging | 2 | 13 | Start/stop charging |
| Lights & Horn | 2 | 17 | Flash, honk & flash |

### Resource Categories

| Resource | Type | Tests | Purpose |
|----------|------|-------|---------|
| list_vehicles | Static | 7 | List all vehicles |
| state/{vehicle_id} | Template | 15 | Vehicle state by ID |

## Troubleshooting

### "Module not found" errors
```bash
# Install test dependencies
pip install -e ".[test]"
```

### Integration tests fail
- Check `src/config.json` has valid VW credentials
- Verify internet connection
- Check VW API service status
- Review tokenstore validity

### Async test warnings
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` for async tests

### Fixture not found
- Check conftest.py in correct directory
- Verify fixture scope (module vs function)
- Import fixtures if needed

## Contributing

When adding new features:
1. Add tool tests in `tests/tools/` for data retrieval
2. Add command tests in `tests/commands/` for vehicle control
3. Add resource tests in `tests/resources/` for MCP resources
4. Update `test_data.py` with expected values
5. Update `test_adapter.py` mock implementation
6. Ensure all tests pass before committing

Test file naming convention:
- Tools: `test_{tool_name}.py`
- Commands: `test_{command_category}.py`
- Resources: `test_{resource_name}.py`

Each test file should include:
- Docstring explaining what's tested
- Import of test data from `test_data.py`
- Grouped tests with clear section headers
- MCP server registration test at the end
3. Update `TestAdapter` if needed
4. Run full test suite: `pytest tests/tools/ -v`
5. Document in test file headers
6. Update this README if structure changes

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
