# WeConnect MCP Test Suite

Comprehensive test suite for the WeConnect MCP server implementation.

## Test Structure

```
tests/
├── tools/              # MCP Tool Tests (81 tests) ✅
│   ├── conftest.py                    # Shared fixtures
│   ├── test_list_vehicles.py          # 7 tests
│   ├── test_get_vehicle.py            # 13 tests
│   ├── test_get_physical_status.py    # 15 tests
│   ├── test_get_energy_status.py      # 17 tests
│   ├── test_get_climate_status.py     # 18 tests
│   ├── test_maintenance.py            # 6 tests
│   └── test_position.py               # 5 tests
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

### 2. Adapter Tests (`test_adapter.py`)

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

✅ **81/81 tool tests passing** (100%)
⚠️ Some integration tests may fail (update mcp_server.py to use consolidated methods)

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
1. Add tool tests in `tests/tools/`
2. Update `test_data.py` with expected values
3. Update `TestAdapter` if needed
4. Run full test suite: `pytest tests/tools/ -v`
5. Document in test file headers
6. Update this README if structure changes

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
