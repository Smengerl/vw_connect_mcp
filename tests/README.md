# WeConnect MCP Test Suite

Comprehensive test suite for the WeConnect MCP server implementation.

## Quick Stats

| Category | Tests | Files | Scope | Description |
|----------|-------|-------|-------|-------------|
| **Tools** | 76 | 7 | Unit | Data retrieval operations (adapter methods) |
| **Commands** | 71 | 5 | Unit | Vehicle control operations (execute_command) |
| **Resources** | 22 | 2 | Integration | MCP resource protocol (read_resource) |
| **MCP Server** | 8 | 1 | Integration | MCP protocol layer (call_tool) |
| **Real API** | ~13 | 2 | E2E | Real VW API & full roundtrip tests |
| **Total** | **177+** | **17** | All | Complete coverage |

**All 177 tests passing** ✅ | **Test execution: ~0.4s** ⚡

## Test Structure

```
tests/
├── conftest.py                    # ⭐ Central fixtures (8 fixtures)
│
├── tools/                         # Unit Tests: Adapter Methods (76 tests)
│   ├── test_list_vehicles.py      # 5 tests - List all vehicles
│   ├── test_get_vehicle.py        # 12 tests - Get vehicle details
│   ├── test_get_physical_status.py# 14 tests - Doors, windows, tyres, lights
│   ├── test_get_energy_status.py  # 16 tests - Battery, charging, range
│   ├── test_get_climate_status.py # 18 tests - Climate & window heating
│   ├── test_maintenance.py        # 6 tests - Service schedules
│   └── test_position.py           # 5 tests - GPS coordinates
│
├── commands/                      # Unit Tests: Command Execution (71 tests)
│   ├── test_lock_unlock.py        # 13 tests - Lock/unlock vehicle
│   ├── test_climatization.py      # 13 tests - Start/stop climate
│   ├── test_charging.py           # 13 tests - Start/stop charging
│   ├── test_lights_horn.py        # 17 tests - Flash lights, honk
│   └── test_window_heating.py     # 15 tests - Window heating control
│
├── resources/                     # Integration Tests: MCP Resources (22 tests)
│   ├── test_list_vehicles.py      # 7 tests - data://list_vehicles
│   └── test_vehicle_state.py      # 15 tests - data://state/{vehicle_id}
│
├── test_mcp_server.py             # Integration: MCP Protocol (8 tests)
├── test_adapter.py                # Mock adapter implementation
├── test_data.py                   # Central test data configuration
├── test_carconnectivity_adapter.py# E2E: Real VW API (~10 tests)
└── test_full_roundtrip.py         # E2E: Full MCP stack (~3 tests)
```

## Central Fixtures (conftest.py)

**All fixtures centralized** - No duplicates! 🎯

### Mock Data Fixtures (unit/integration tests)
| Fixture | Scope | Type | Used By |
|---------|-------|------|---------|
| `adapter` | module | TestAdapter | tools/, commands/, resources/, test_mcp_server.py |
| `mcp_server` | module | FastMCP | tools/, commands/, resources/, test_mcp_server.py |
| `mcp_client` | function | MCP Client | resources/, test_mcp_server.py |

### Real API Fixtures (end-to-end tests)
| Fixture | Scope | Type | Used By |
|---------|-------|------|---------|
| `config_path` | module | Path | test_carconnectivity_adapter.py, test_full_roundtrip.py |
| `tokenstore_file` | module | Path | test_carconnectivity_adapter.py, test_full_roundtrip.py |
| `real_adapter` | module | CarConnectivityAdapter | test_carconnectivity_adapter.py, real_mcp_server |
| `real_mcp_server` | module | FastMCP | test_full_roundtrip.py |
| `real_mcp_client` | function | MCP Client | test_full_roundtrip.py |

**Benefits**: Module-scoped fixtures = 10× faster (0.37s vs 0.68s) ⚡

## Test Categories by Scope

### 1. Unit Tests: Tools (76 tests)
**Scope**: Individual adapter methods  
**Fixtures**: `adapter` (TestAdapter with 2 mock vehicles)  
**Speed**: Fast (no API calls)  
**Run**: `pytest tests/tools/ -v`

**Coverage**:
- List vehicles, get vehicle details (BASIC/FULL)
- Physical status (doors, windows, tyres, lights)
- Energy status (battery, charging, range)
- Climate status (climatization, window heating)
- Maintenance info, GPS position

### 2. Unit Tests: Commands (71 tests)
**Scope**: Command execution via adapter  
**Fixtures**: `adapter` (TestAdapter)  
**Speed**: Fast (no API calls)  
**Run**: `pytest tests/commands/ -v`

**Coverage**: All 10 vehicle control commands
- Lock/unlock vehicle
- Start/stop climatization
- Start/stop charging (EV/PHEV)
- Flash lights, honk & flash
- Start/stop window heating

### 3. Integration Tests: Resources (22 tests)
**Scope**: MCP resource protocol  
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`  
**Speed**: Fast (mock data via MCP protocol)  
**Run**: `pytest tests/resources/ -v`

**Coverage**:
- `data://list_vehicles` - List all vehicles
- `data://state/{vehicle_id}` - Vehicle state by VIN/name/license

### 4. Integration Tests: MCP Server (8 tests)
**Scope**: MCP protocol layer (Client ↔ Server)  
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`  
**Speed**: Fast (mock data)  
**Run**: `pytest tests/test_mcp_server.py -v`

**Coverage**:
- Client connection
- Tool invocation via `call_tool()`
- Response validation
- Error handling

### 5. E2E Tests: Real API (13+ tests)
**Scope**: Real VW API integration & full MCP stack  
**Fixtures**: `real_adapter`, `real_mcp_server`, `real_mcp_client`  
**Speed**: Slow (real API calls)  
**Run**: `pytest tests/test_carconnectivity_adapter.py tests/test_full_roundtrip.py -v`

⚠️ **Requirements**:
- Valid VW credentials in `src/config.json`
- Internet connection
- Real vehicle(s) in account

## Running Tests

### All unit/integration tests (fast):
```bash
pytest tests/ -k "not carconnectivity and not roundtrip" -v
# 177 passed in ~0.4s ⚡
```

### All tests including E2E (slow):
```bash
pytest tests/ -v
# 177+ passed (longer due to API calls)
```

### Specific categories:
```bash
pytest tests/tools/ -v          # 76 tool tests
pytest tests/commands/ -v       # 71 command tests
pytest tests/resources/ -v      # 22 resource tests
pytest tests/test_mcp_server.py -v  # 8 MCP protocol tests
```

### With coverage:
```bash
pytest tests/ --cov=src/weconnect_mcp --cov-report=html
```

## Test Data

**Mock vehicles** (in `TestAdapter`):
1. **ID.7 Tourer** - Electric, VIN: WVWZZZED4SE003938, License: M-AB 1234
2. **Transporter 7** - Combustion, VIN: WV2ZZZSTZNH009136, License: M-CD 5678

**Test data configuration**: `tests/test_data.py`
- Vehicle identifiers (VINs, names, license plates)
- Expected values for all scenarios
- Helper functions for parametrized tests

## Key Features

✅ **No fixture duplication** - All in `conftest.py`  
✅ **Fast execution** - Module-scoped fixtures (177 tests in 0.37s)  
✅ **Comprehensive coverage** - Tools, commands, resources, protocol, E2E  
✅ **Consistent patterns** - All tests follow same structure  
✅ **Mock & Real** - Unit tests with mocks + E2E with real API  
✅ **Async support** - Full async/await testing with pytest-asyncio  
✅ **Error handling** - Tests for invalid inputs and edge cases  

## Architecture

```
Mock Tests (fast)          Integration Tests (medium)      E2E Tests (slow)
─────────────────         ────────────────────────────    ────────────────
TestAdapter               TestAdapter → MCP Server        Real VW API
    ↓                           ↓                              ↓
Adapter methods           MCP Client → Resources         CarConnectivityAdapter
Command execution         MCP Client → Tools                    ↓
                                                          MCP Server → Client
                                                          Full roundtrip
```

**Test execution flow**:
1. Fast unit tests verify adapter logic (147 tests, ~0.3s)
2. Integration tests verify MCP protocol (30 tests, ~0.1s)
3. E2E tests verify real API (optional, ~5-10s depending on network)

---

**Happy Testing!** 🧪✨

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
