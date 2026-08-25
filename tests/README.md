# WeConnect MCP Test Suite

Test suite for the WeConnect MCP server (Tibber Data API backend).

## Quick Stats

| Category | Tests | Files | Scope | Description |
|----------|-------|-------|-------|-------------|
| **Tools** | 30 | 3 | Unit | Data retrieval operations (adapter methods) |
| **Tibber client** | 26 | 1 | Unit | OAuth2/token-refresh logic, incl. concurrent-instance locking |
| **Tibber extraction** | 9 | 1 | Unit | tibber_adapter.py's device-detail extraction functions + vin_from_external_id, against real fixture data |
| **Error translation** | 11 | 1 | Unit | AdapterUnavailableError → `server_unavailable` JSON translation chain |
| **Reconnecting adapter** | 11 | 1 | Unit | No-restart-needed self-healing retry logic |
| **Caching** | 5 | 1 | Unit | CacheMixin behavior (expiry, fetch-once, refetch) |
| **Starting adapter** | 6 | 1 | Unit | UnavailableAdapter fallback stub |
| **Server startup** | 7 | 1 | Unit | mcp_server_cli.py's connect-or-fallback logic (both transports) |
| **Health endpoint** | 3 | 1 | Integration | `/health` route, real ASGI transport |
| **MCP Server** | 1 | 1 | Integration | MCP protocol layer (client connection) |
| **Total** | **109** | **12** | All | Complete coverage |

All tests are fast mock/offline tests (well under 1s total) — there is no
separate slow/real-API suite: the Tibber Data API is read-only, so nothing
exists to test beyond what the mock adapter, fixture data, and mocked
`httpx` calls already cover.

## Test Structure

```
tests/
├── conftest.py                    # ⭐ Central fixtures (adapter, mcp_server, mcp_client)
│
├── tools/                         # Unit Tests: Adapter Methods (30 tests)
│   ├── test_list_vehicles.py      # 4 tests  - List all vehicles
│   ├── test_get_vehicle.py        # 10 tests - Get vehicle details (BASIC/FULL)
│   └── test_get_energy_status.py  # 16 tests - Battery, charging, range, last-seen
│
├── test_mcp_server.py             # Integration: MCP client connection (1 test)
├── test_health_endpoint.py        # Integration: /health route (3 tests)
├── test_caching.py                # Unit: CacheMixin behavior (5 tests)
├── test_tibber_extraction.py      # Unit: device-detail extraction + VIN extraction (9 tests)
├── test_tibber_client.py          # Unit: OAuth2/token-refresh, concurrent locking (26 tests)
├── test_error_translation.py      # Unit: AdapterUnavailableError → JSON translation (11 tests)
├── test_starting_adapter.py       # Unit: UnavailableAdapter fallback stub (6 tests)
├── test_reconnecting_adapter.py   # Unit: self-healing retry logic (11 tests)
├── test_mcp_server_cli.py         # Unit: startup connect-or-fallback, both transports (7 tests)
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

### 1. Unit Tests: Tools (30 tests)
**What**: Individual adapter data retrieval methods
**Fixtures**: `adapter` (TestAdapter with 2 mock vehicles)
**Run**: `pytest tests/tools/ -v`

**Coverage**:
- List vehicles
- Get vehicle details (BASIC/FULL)
- Energy status (battery, charging, range)

### 2. Unit Tests: Caching (5 tests)
**What**: CacheMixin behavior, exercised directly via a minimal concrete
subclass (TestAdapter itself has no caching)
**Run**: `pytest tests/test_caching.py -v`

**Coverage**:
- Cache duration constant
- Expired before first fetch, fetch-once, no-refetch-within-window,
  refetch-after-expiry

### 3. Unit Tests: Tibber Extraction (9 tests)
**What**: `tibber_adapter.py`'s device-detail capability parsing and
`vin_from_external_id()`, against the confirmed-live device-detail fixture
from `ARCHITECTURE.md` §3.1 — no mock adapter, no network
**Run**: `pytest tests/test_tibber_extraction.py -v`

**Coverage**:
- Charging state (SoC, target SoC, plug/charging status)
- Range conversion (meters → km)
- Bare-VIN vs. `vendor:VIN` externalId formats

### 4. Integration Tests: MCP Server (1 test)
**What**: MCP protocol layer (Client ↔ Server)
**Fixtures**: `adapter`, `mcp_server`, `mcp_client`
**Run**: `pytest tests/test_mcp_server.py -v`

**Coverage**:
- Client connection

## Test Data

**Mock vehicles** (in `TestAdapter`, both electric-shaped — Tibber's
integration is EV-only, see `ARCHITECTURE.md`; no license plates either,
Tibber never reports one):
1. **ID.7 Tourer** - VIN: WVWZZZED4SE003938, Name: ID7
2. **T7 Multivan eHybrid** - VIN: WV2ZZZSTZNH009136, Name: T7

**Test data configuration**: `tests/test_data.py`
- Vehicle identifiers (VINs, names)
- Expected values for all scenarios
- Helper functions for parametrized tests

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
