# WeConnect MCP Test Suite

Test suite for the WeConnect MCP server (Tibber Data API backend).

## Quick Stats

| Category | Tests | Files | Scope | Description |
|----------|-------|-------|-------|-------------|
| **Tools** | 31 | 3 | Unit | Data retrieval operations (adapter methods) |
| **Caching** | 4 | 1 | Unit | Cache behavior and invalidation |
| **MCP Server** | 1 | 1 | Integration | MCP protocol layer (client connection) |
| **Total** | **36** | **5** | All | Complete coverage |

All 36 tests are fast mock tests (~1s) — there is no separate slow/real-API
suite: the Tibber Data API is read-only, so nothing exists to test beyond
what the mock adapter already covers via unit tests. A `real_api` pytest
marker is defined for future use if that ever changes, but no test uses it
today.

## Test Structure

```
tests/
├── conftest.py                    # ⭐ Central fixtures (adapter, mcp_server, mcp_client)
│
├── tools/                         # Unit Tests: Adapter Methods (31 tests)
│   ├── test_list_vehicles.py      # 4 tests  - List all vehicles
│   ├── test_get_vehicle.py        # 11 tests - Get vehicle details (BASIC/FULL)
│   └── test_get_energy_status.py  # 16 tests - Battery, charging, range
│
├── test_mcp_server.py             # Integration: MCP client connection (1 test)
├── test_caching.py                # Unit: Cache behavior (4 tests)
├── test_adapter.py                # Mock adapter implementation (TestAdapter)
└── test_data.py                   # Central test data configuration
```

There is no `commands/`, `resources/`, or `real_api/` directory: the Tibber
Data API has no write endpoints at all (no vehicle commands), and the MCP
resources layer was removed in favor of tools alone (identical data, but
tools are the mechanism every target MCP client — Claude Desktop, VS Code
Copilot, Claude Code — actually supports).

## Running Tests

```bash
# Run the whole suite
pytest tests/ -v
# or
./scripts/test.sh

# Specific file
pytest tests/tools/test_get_energy_status.py -v

# With coverage
pytest tests/ --cov=src/weconnect_mcp --cov-report=html
```

## Central Fixtures (conftest.py)

| Fixture | Scope | Type | Used By |
|---------|-------|------|---------|
| `adapter` | module | TestAdapter | All tests |
| `mcp_server` | module | FastMCP | test_mcp_server.py |
| `mcp_client` | function | MCP Client | test_mcp_server.py |

## Test Categories

### 1. Unit Tests: Tools (31 tests)
**What**: Individual adapter data retrieval methods
**Fixtures**: `adapter` (TestAdapter with 2 mock vehicles)
**Run**: `pytest tests/tools/ -v`

**Coverage**:
- List vehicles
- Get vehicle details (BASIC/FULL)
- Energy status (battery, charging, range)

### 2. Unit Tests: Caching (4 tests)
**What**: Cache behavior and invalidation
**Fixtures**: `adapter`
**Run**: `pytest tests/test_caching.py -v`

**Coverage**:
- Cache duration constant
- `invalidate_cache()` presence and callability

### 3. Integration Tests: MCP Server (1 test)
**What**: MCP protocol layer (Client ↔ Server)
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`
**Run**: `pytest tests/test_mcp_server.py -v`

**Coverage**:
- Client connection

## Test Data

**Mock vehicles** (in `TestAdapter`):
1. **ID.7 Tourer** - Electric, VIN: WVWZZZED4SE003938, Name: ID7, License: M-XY 5678
2. **Transporter 7** - Combustion, VIN: WV2ZZZSTZNH009136, Name: T7, License: M-AB 1234

**Test data configuration**: `tests/test_data.py`
- Vehicle identifiers (VINs, names, license plates)
- Expected values for all scenarios
- Helper functions for parametrized tests

## Pytest Markers

```python
@pytest.mark.real_api    # Reserved for a real Tibber API test, requires tibber_config.json (unused today)
@pytest.mark.slow        # Slow test (network I/O)
```

Both are excluded by default (see `pytest.ini`'s `addopts`), but no current
test carries either marker.

## Best Practices

### Adding New Tests

1. **Tool tests**: Add to `tests/tools/test_<tool_name>.py`
   - Use `adapter` fixture (auto-available via conftest.py)
   - Import expected values from `tests.test_data`
   - Follow existing naming conventions
2. **Update Test Data**: Modify `tests/test_data.py` when needed

### Test Naming

- **Test files**: `test_<feature>.py`
- **Test functions**: `test_<feature>_<scenario>()`
- **Fixtures**: Descriptive names with docstrings

## Troubleshooting

### "Module not found" errors
```bash
pip install -e ".[test]"
```

### Async test warnings
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` for async tests

### Fixture not found
- Check conftest.py is in correct directory
- Verify fixture scope (module vs function)

## Contributing

When adding new features:
1. Add unit tests for adapter methods (`tools/`)
2. Add integration tests if needed (`test_mcp_server.py`)
3. Update `TestAdapter` mock implementation if needed
4. Update `test_data.py` with expected values
5. Run full test suite: `pytest tests/ -v`
6. Document in test file headers
7. Update this README if structure changes

**Before committing**:
```bash
pytest tests/ -v
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
