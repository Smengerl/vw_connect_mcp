# WeConnect MCP Test Suite

Comprehensive test suite for the WeConnect MCP server implementation.

## Quick Stats

| Category | Tests | Files | Scope | Description |
|----------|-------|-------|-------|-------------|
| **Tools** | 76 | 7 | Unit | Data retrieval operations (adapter methods) |
| **Commands** | 74 | 5 | Unit | Vehicle control operations (lock, unlock, start_charging, etc.) |
| **Resources** | 27 | 3 | Unit | MCP resource protocol tests |
| **MCP Server** | 8 | 1 | Integration | MCP protocol layer (call_tool) |
| **Caching** | 12 | 1 | Unit | Cache behavior and invalidation |
| **Real API** | 18 | 4 | E2E | Real VW API integration tests |
| **Total** | **215** | **21** | All | Complete coverage |

**197 mock tests** ✅ (~4s) | **18 real API tests** 🐌 (slow, requires VW credentials)

## Test Structure

```
tests/
├── conftest.py                    # ⭐ Central fixtures (mock + real API)
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
├── commands/                      # Unit Tests: Command Execution (74 tests)
│   ├── test_lock_unlock.py        # 15 tests - Lock/unlock vehicle
│   ├── test_climatization.py      # 14 tests - Start/stop climate
│   ├── test_charging.py           # 13 tests - Start/stop charging
│   ├── test_lights_horn.py        # 17 tests - Flash lights, honk
│   └── test_window_heating.py     # 15 tests - Window heating control
│
├── resources/                     # Unit Tests: MCP Resources (27 tests)
│   ├── test_list_vehicles.py      # 7 tests - data://list_vehicles
│   ├── test_vehicle_state.py      # 15 tests - data://state/{vehicle_id}
│   └── test_license_plate.py      # 5 tests - License plate handling
│
├── real_api/                      # E2E Tests: Real VW API (18 tests, SLOW)
│   ├── test_real_api_carconnectivity_adapter.py  # 9 tests - Adapter with real API
│   ├── test_real_api_full_roundtrip.py           # 2 tests - Full MCP stack
│   ├── test_real_api_integration.py              # 4 tests - AI workflow simulation
│   └── test_real_api_license_plate.py            # 3 tests - License plate limitation
│
├── test_mcp_server.py             # Integration: MCP Protocol (8 tests)
├── test_caching.py                # Unit: Cache behavior (12 tests)
├── test_adapter.py                # Mock adapter implementation
└── test_data.py                   # Central test data configuration
```

## Running Tests

### Quick Start

```bash
# Run only fast mock tests (recommended for development)
./scripts/test.sh --skip-slow
# or
pytest tests/ -m "not real_api" -v

# Run ALL tests including slow real API tests (requires VW credentials)
./scripts/test.sh
# or
pytest tests/ -v
```

### Using test.sh Script

```bash
# Fast tests only (197 tests, ~4s)
./scripts/test.sh --skip-slow

# All tests including real API (215 tests, slower)
./scripts/test.sh

# With verbose output
./scripts/test.sh --skip-slow -v

# Show help
./scripts/test.sh --help
```

### Direct pytest Commands

```bash
# All mock tests (fast)
pytest tests/ -m "not real_api" -v           # 197 passed in ~4s ⚡

# All tests including real API (slow)
pytest tests/ -v                              # 215 passed (slower)

# Specific categories
pytest tests/tools/ -v                        # 76 tool tests
pytest tests/commands/ -v                     # 74 command tests  
pytest tests/resources/ -v                    # 27 resource tests
pytest tests/test_caching.py -v               # 12 caching tests

# Real API tests only (requires VW credentials)
pytest tests/real_api/ -v                     # 18 E2E tests
pytest tests/ -m "real_api" -v                # Same, via marker

# With coverage
pytest tests/ -m "not real_api" --cov=src/weconnect_mcp --cov-report=html
```

## Central Fixtures (conftest.py)

**All fixtures centralized** - No duplicates! 🎯

### Mock Data Fixtures (fast unit tests)
| Fixture | Scope | Type | Used By |
|---------|-------|------|---------|
| `adapter` | module | TestAdapter | All mock tests |
| `mcp_server` | module | FastMCP | Resource & MCP server tests |
| `mcp_client` | function | MCP Client | Resource & MCP server tests |

### Real API Fixtures (slow E2E tests)
| Fixture | Scope | Type | Used By |
|---------|-------|------|---------|
| `config_path` | module | Path | All real_api/ tests |
| `tokenstore_file` | module | Path | All real_api/ tests |
| `real_adapter` | module | CarConnectivityAdapter | All real_api/ tests |
| `real_mcp_server` | module | FastMCP | test_real_api_full_roundtrip.py |
| `real_mcp_client` | function | MCP Client | test_real_api_full_roundtrip.py |

**Benefits**: 
- Module-scoped fixtures = faster execution ⚡
- No fixture duplication across test files
- Consistent test data for all tests

## Test Categories

### 1. Unit Tests: Tools (76 tests)
**What**: Individual adapter data retrieval methods  
**Fixtures**: `adapter` (TestAdapter with 2 mock vehicles)  
**Speed**: Fast (~1s)  
**Run**: `pytest tests/tools/ -v`

**Coverage**:
- List vehicles, get vehicle details (BASIC/FULL)
- Physical status (doors, windows, tyres, lights)
- Energy status (battery, charging, range)
- Climate status (climatization, window heating)
- Maintenance info, GPS position

### 2. Unit Tests: Commands (74 tests)
**What**: Vehicle control command execution  
**Fixtures**: `adapter` (TestAdapter)  
**Speed**: Fast (~1s)  
**Run**: `pytest tests/commands/ -v`

**Coverage**: All 10 vehicle control commands
- Lock/unlock vehicle
- Start/stop climatization
- Start/stop charging (EV/PHEV)
- Flash lights, honk & flash
- Start/stop window heating

### 3. Unit Tests: Resources (27 tests)
**What**: MCP resource protocol implementation  
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`  
**Speed**: Fast (~1s)  
**Run**: `pytest tests/resources/ -v`

**Coverage**:
- `data://list_vehicles` - List all vehicles
- `data://state/{vehicle_id}` - Vehicle state by VIN/name
- License plate handling and limitations

### 4. Unit Tests: Caching (12 tests)
**What**: Cache behavior and invalidation  
**Fixtures**: `adapter`  
**Speed**: Fast (~1s)  
**Run**: `pytest tests/test_caching.py -v`

**Coverage**:
- Cache TTL (5 minutes)
- Cache invalidation after commands
- Fresh data retrieval

### 5. Integration Tests: MCP Server (8 tests)
**What**: MCP protocol layer (Client ↔ Server)  
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`  
**Speed**: Fast (~0.5s)  
**Run**: `pytest tests/test_mcp_server.py -v`

**Coverage**:
- Client connection
- Tool invocation via `call_tool()`
- Response validation
- Error handling

### 6. E2E Tests: Real API (18 tests, SLOW)
**What**: Real VW API integration & full MCP stack  
**Fixtures**: `real_adapter`, `real_mcp_server`, `real_mcp_client`  
**Speed**: Slow (5-30s, network dependent)  
**Run**: `pytest tests/real_api/ -v`

⚠️ **Requirements**:
- Valid VW credentials in `src/config.json`
- Internet connection
- Real vehicle(s) in account

**Coverage**:
- CarConnectivityAdapter with real VW API
- Full MCP roundtrip (VW API → Adapter → Server → Client)
- AI workflow simulation
- License plate limitation verification

**Files**:
- `test_real_api_carconnectivity_adapter.py` - Adapter integration (9 tests)
- `test_real_api_full_roundtrip.py` - Full MCP stack (2 tests)
- `test_real_api_integration.py` - AI workflow (4 tests)
- `test_real_api_license_plate.py` - License plate tests (3 tests)

## Test Data

**Mock vehicles** (in `TestAdapter`):
1. **ID.7 Tourer** - Electric, VIN: WVWZZZED4SE003938, Name: ID7, License: M-XY 5678
2. **Transporter 7** - Combustion, VIN: WV2ZZZSTZNH009136, Name: T7, License: M-AB 1234

**Test data configuration**: `tests/test_data.py`
- Vehicle identifiers (VINs, names, license plates)
- Expected values for all scenarios
- Helper functions for parametrized tests

## Key Features

✅ **Comprehensive coverage** - 215 tests across all layers  
✅ **Fast execution** - 197 mock tests in ~4s  
✅ **Pytest markers** - `@pytest.mark.real_api` for slow tests  
✅ **No fixture duplication** - All in `conftest.py`  
✅ **Consistent patterns** - All tests follow same structure  
✅ **Mock & Real** - Unit tests with mocks + E2E with real API  
✅ **Async support** - Full async/await testing with pytest-asyncio  
✅ **Error handling** - Tests for invalid inputs and edge cases  
✅ **Test script** - `./scripts/test.sh --skip-slow` for easy execution

## Pytest Markers

Tests are marked for selective execution:

```python
@pytest.mark.real_api    # Requires real VW API credentials
@pytest.mark.slow        # Slow test (network I/O)
```

**Usage**:
```bash
# Run only mock tests (fast)
pytest tests/ -m "not real_api" -v

# Run only real API tests (slow)
pytest tests/ -m "real_api" -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

## Architecture

```
Mock Tests (fast)          Integration Tests (fast)      E2E Tests (slow)
─────────────────         ────────────────────────────   ────────────────
TestAdapter               TestAdapter → MCP Server       Real VW API
    ↓                           ↓                              ↓
Adapter methods           MCP Client → Resources         CarConnectivityAdapter
Command execution         MCP Client → Tools                    ↓
Cache behavior                                           MCP Server → Client
                                                         Full roundtrip
```

**Test execution flow**:
1. Fast unit tests verify adapter logic (177 tests, ~3s)
2. Integration tests verify MCP protocol & caching (20 tests, ~1s)
3. E2E tests verify real API (18 tests, ~5-30s depending on network)

---

## Best Practices

### Adding New Tests

1. **Tool Tests**: Add to `tests/tools/test_<tool_name>.py`
   - Use `adapter` fixture (auto-available via conftest.py)
   - Import expected values from `tests.test_data`
   - Follow existing naming conventions

2. **Command Tests**: Add to `tests/commands/test_<command_category>.py`
   - Test success cases
   - Test error cases (invalid vehicle_id)
   - Test type-specific behavior (BEV vs combustion)

3. **Real API Tests**: Add to `tests/real_api/test_real_api_*.py`
   - Mark with `@pytest.mark.real_api` and `@pytest.mark.slow`
   - Use `real_adapter` fixture from conftest.py
   - Document VW API requirements

4. **Update Test Data**: Modify `tests/test_data.py` when needed

### Test Naming

- **Test files**: `test_<feature>.py`
- **Test functions**: `test_<feature>_<scenario>()`
- **Fixtures**: Descriptive names with docstrings

### Documentation

- Every test file should have a header docstring
- Fixtures need detailed docstrings
- Complex tests should have inline comments

## Troubleshooting

### "Module not found" errors
```bash
pip install -e ".[test]"
```

### Real API tests fail
- Check `src/config.json` has valid VW credentials
- Verify internet connection
- Check VW API service status
- Review tokenstore validity (`/tmp/tokenstore`)

### Async test warnings
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` for async tests

### Fixture not found
- Check conftest.py is in correct directory
- Verify fixture scope (module vs function)

## Contributing

When adding new features:
1. Add unit tests for adapter methods (tools/ or commands/)
2. Add integration tests if needed (resources/, test_mcp_server.py)
3. Update `TestAdapter` mock implementation if needed
4. Add real API tests in real_api/ if applicable
5. Update `test_data.py` with expected values
6. Run full test suite: `./scripts/test.sh --skip-slow`
7. Document in test file headers
8. Update this README if structure changes

**Before committing**:
```bash
# Must pass!
./scripts/test.sh --skip-slow
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Happy Testing!** 🧪✨
