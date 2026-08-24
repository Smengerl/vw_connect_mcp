# GitHub Copilot Instructions for WeConnect MCP

**Type**: MCP Server (Python) for vehicle data via the [Tibber Data API](https://data-api.tibber.com/docs/) — originally built for Volkswagen, but **not VW-specific**: Tibber's integration runs through Enode (30+ EV brands), so any vehicle paired to the connected Tibber account works identically
**Architecture**: Modular adapter with mixins (`CacheMixin`, `TibberStateExtractionMixin`) composed into `TibberAdapter`; vehicle identifier resolution is a concrete default method on `AbstractAdapter` itself, not a separate mixin
**Key Library**: `fastmcp` (MCP server framework). No third-party VW API library is used — the old `carconnectivity` (VW-direct) backend was removed after VW blocked third-party access; its code lives on, unmaintained, on the permanent `carconnectivity` git branch.
**Languages**: Python 3.10+ with modern type hints (`dict[str, Any]`, not `Dict`)
**Test Suite**: 47 tests (all mock/offline, no real API calls) — **ALL 47 MUST PASS** before committing

> For setup, usage, scripts, project structure, and test documentation see **README.md** and **tests/README.md**. For the AI-facing description of the tool surface (kept in sync with the actual tools) see **src/weconnect_mcp/server/AI_INSTRUCTIONS.md**.

## Critical Context: Read-Only, Narrow Surface

The Tibber Data API is **read-only** (no write/command endpoints exist at all) and exposes only
identity + 5 charging/range capabilities for electric vehicles. There is no doors/windows/tyres/
lights/climatization/GPS/maintenance data, and **no command tools of any kind** (no lock/unlock,
climate control, charging control, lights, honk). Don't add a "command" mixin, a `CommandMixin`,
or any `lock_vehicle()`/`start_charging()`-style method — there is nothing on the Tibber side to
back it. If a data point or action isn't in the 5-tool list below, it doesn't exist for this
backend; say so rather than guessing at a tool name.

## Code Style (Non-Negotiable)

**Type Hints**: Always required for parameters and return values
```python
def get_vehicle(vehicle_id: str) -> Optional[VehicleModel]:  # ✅ Good
def get_vehicle(vehicle_id):  # ❌ Bad - no types
```

**Naming**: `snake_case.py`, `PascalCase` classes, `snake_case()` functions, `UPPER_SNAKE_CASE` constants

**Imports**: Standard library → Third-party → Local imports

**None Handling**: ALWAYS check for `None` — Tibber only reports a handful of fields, and many
are `None` by design (not an error — a structural limitation of the API), not a runtime failure to guard against
```python
# ✅ Good
charging = energy_status.electric.charging
if charging is not None:
    soc = charging.current_soc_percent if charging.current_soc_percent is not None else None

# ❌ Bad - will crash
soc = energy_status.electric.charging.current_soc_percent
```

## Architecture (Mixin Pattern)

`TibberAdapter` (`src/weconnect_mcp/adapter/tibber_adapter.py`) uses **multiple inheritance** to
compose functionality:

```python
class TibberAdapter(
    CacheMixin,                  # Caching with 5-min TTL
    TibberStateExtractionMixin,  # Extract charging/range state from Tibber's device-detail response
    AbstractAdapter               # Base class (abstract interface) -- also provides
):                                #   resolve_vehicle_id (VIN/name/license plate) as a concrete default
    ...
```

| Mixin | File |
|---|---|
| `CacheMixin` | `src/weconnect_mcp/adapter/mixins/cache_mixin.py` |
| `TibberStateExtractionMixin` | `src/weconnect_mcp/adapter/mixins/tibber_state_extraction_mixin.py` |
| `TibberAdapter` (composes the above) | `src/weconnect_mcp/adapter/tibber_adapter.py` |
| `AbstractAdapter` + Pydantic models | `src/weconnect_mcp/adapter/abstract_adapter.py` |
| `TibberDataAPI` (OAuth2 + PKCE HTTP client) | `src/weconnect_mcp/adapter/tibber_client.py` |
| `StartingAdapter` (no-op stub while HTTP-mode backend connects) | `src/weconnect_mcp/adapter/starting_adapter.py` |

**Key Points**:
- Each mixin = single responsibility
- `AbstractAdapter` only declares what Tibber can actually back: `list_vehicles`, `get_vehicle`,
  `get_energy_status`, `shutdown`. There are **no command methods** and no
  physical/climate/position/maintenance read methods to stub out — they were removed from the
  interface entirely rather than kept as permanent `None`/"not supported" no-ops.
- All Pydantic models use `Optional` fields — most stay `None` for this backend by design.

## Important Domain Knowledge

### Vehicle Identification
- **Name**: `"ID.7"` (preferred for readability), matched case-insensitively (partial match on name)
- **VIN**: `"WVWZZZED4SE003938"` (unique identifier)
- **License Plate**: ⚠️ **NOT SUPPORTED** — Tibber's API doesn't provide it; `license_plate` is always `null`

### Vehicle Types
Tibber's vehicle integration **only ever reports electric vehicles**, regardless of brand.
`EnergyStatusModel.combustion` is always `None` for this backend; the `combustion` fields/models
still exist in `abstract_adapter.py` only because `tests/test_adapter.py`'s mock covers both
vehicle types for test purposes.

### Caching Strategy
- **Duration**: 5 minutes (300 seconds) via `CacheMixin`
- **Purpose**: Be a polite Tibber API citizen (Tibber's docs ask clients to avoid excessive polling)
- **No cache invalidation exists** — there are no commands that would ever need to force a
  refresh, so `invalidate_cache()` was removed entirely (it used to exist on both
  `AbstractAdapter` and `CacheMixin` but nothing called it). Don't reintroduce it without a real
  caller.

### What Tibber Actually Reports (5 capabilities)
Extracted in `TibberStateExtractionMixin` from a Tibber device-detail response's flat
`capabilities` list:

| Capability id | Meaning |
|---|---|
| `storage.stateOfCharge` | Current battery % |
| `storage.targetStateOfCharge` | Target charge % |
| `range.remaining` | Remaining range (meters — converted to km) |
| `connector.status` | Plugged in? (`connected`/`disconnected`) |
| `charging.status` | `charging`/`idle` |

`ChargingModel` has no `charging_power_kw` or `remaining_time_minutes` fields at all — Tibber never exposes them, so they were removed from the model entirely rather than kept as always-`None` fields.

## Testing Guidelines (CRITICAL)

**Golden Rule**: All 47 tests MUST pass before committing. No exceptions.
**Always use `./scripts/test.sh`** (not `pytest` directly) — see `tests/README.md` for full test
structure and commands. `--skip-slow` is accepted but currently a no-op: there are no slow/real-API
tests (the Tibber API is read-only, so the mock adapter already covers everything it can return).

### Test Layout
```
tests/
  conftest.py            # shared fixtures: adapter, mcp_server, mcp_client
  test_adapter.py         # TestAdapter — mock AbstractAdapter implementation (NOT in the adapter package)
  test_data.py            # shared VIN constants + expected-value dicts
  test_caching.py         # CacheMixin behavior (via a minimal concrete subclass)
  test_tibber_extraction.py  # TibberStateExtractionMixin + vin_from_external_id, real fixture data
  test_mcp_server.py      # MCP protocol / tool-registration tests
  tools/
    test_get_vehicle.py
    test_get_energy_status.py
    test_list_vehicles.py
```

### Writing Tests — MANDATORY for New Features

**Rule**: Every new read tool or adapter method MUST have tests covering:
1. ✅ Success case (happy path)
2. ✅ Error case (vehicle not found → `None` / `{"error": ...}`)
3. ✅ Edge cases (`None` values — most Tibber fields are optional by design)

**Example — Adding a New State Getter** (there is no "add a command" example: no command surface exists):
```python
# File: tests/tools/test_get_new_status.py
from test_adapter import TestAdapter  # not weconnect_mcp.adapter — TestAdapter lives in tests/

def test_get_new_status_success():
    adapter = TestAdapter()
    status = adapter.get_new_status("ID7")  # TestAdapter's mock vehicle names: "T7", "ID7"
    assert status is not None

def test_get_new_status_vehicle_not_found():
    adapter = TestAdapter()
    assert adapter.get_new_status("NonExistent") is None
```

Prefer the `adapter` fixture from `conftest.py` (module-scoped `TestAdapter()`) over instantiating
`TestAdapter()` directly inside `tools/` tests — see existing tests for the pattern.

### Test Development Workflow

1. **Write test first** (TDD approach recommended)
2. **Run test** — should fail (red)
3. **Implement feature** — minimum code to pass
4. **Run test** — should pass (green)
5. **Run ALL tests**: `./scripts/test.sh`
6. **Commit only if all 47 tests pass**

### Using TestAdapter (Mock)

`TestAdapter` (in `tests/test_adapter.py`, **not** part of the `weconnect_mcp.adapter` package) is
a full mock `AbstractAdapter` implementation with 2 hardcoded vehicles — no real Tibber calls:

```python
from test_adapter import TestAdapter  # requires tests/ on sys.path — conftest.py does this

adapter = TestAdapter()

vehicles = adapter.list_vehicles()          # -> list[VehicleListItem], 2 entries
vehicle = adapter.get_vehicle("ID7")         # -> VehicleModel | None
energy = adapter.get_energy_status("ID7")    # -> EnergyStatusModel | None (electric)
energy = adapter.get_energy_status("T7")     # -> EnergyStatusModel | None (hybrid: electric + combustion both populated)
```

There is no `./scripts/vehicle_command.sh` and no way to test against the real Tibber API from a
script — there are no commands to test, and read-only calls against a real account require a
one-time interactive login (`weconnect_mcp.cli.tibber_login_cli`) that isn't part of the test suite.

## Common Patterns & Anti-Patterns

### ✅ DO: Handle None Values
```python
# Good - most Tibber fields are optional by design
charging = energy_status.electric.charging if energy_status.electric else None
if charging is not None:
    soc = charging.current_soc_percent

# Bad - will crash
soc = energy_status.electric.charging.current_soc_percent
```

### ✅ DO: Check `energy_status.electric` Before Reading Charging/Battery Data
```python
# Good - electric can be None per the model's own type (Optional[ElectricDriveInfo]),
# even though every vehicle the mock adapter and the real Tibber backend report has it set
if energy_status is None or energy_status.electric is None:
    return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't have a battery"})
```

### ❌ DON'T: Add a Command Method or "Not Supported" Stub
```python
# Bad - there is no write endpoint on Tibber's API; don't add a stub that always
# returns {"success": False, "error": "not supported"} either. Just don't add the method.
def lock_vehicle(self, vehicle_id: str) -> dict[str, Any]:
    ...
```

### ❌ DON'T: Invent a Resource Layer
MCP Resources were deliberately not implemented (would have been a 1:1 duplicate of the tools with
no benefit for this project's target clients) — see `read_tools.py`'s module docstring. Don't add
`@mcp.resource(...)` registrations.

## MCP-Specific Guidelines

### Tool Implementation
Tools are registered via `register_read_tools()` in `src/weconnect_mcp/server/mixins/read_tools.py`
using FastMCP's `@mcp.tool(...)` decorator (not the raw MCP SDK's `@server.call_tool()` dispatcher):

```python
@mcp.tool(
    name="get_charging_status",
    description="...",
    tags={"energy", "read", "charging", "bev-phev"},
    annotations={"title": "Get Charging Status", "readOnlyHint": True, "idempotentHint": True},
)
def get_charging_status(
    vehicle_id: Annotated[str, "Vehicle identifier (VIN, name, or license plate)"]
) -> str:
    energy_status = adapter.get_energy_status(vehicle_id)
    if energy_status is None or energy_status.electric is None or energy_status.electric.charging is None:
        return json.dumps({"error": f"Vehicle {vehicle_id} not found or doesn't support charging"})
    result = energy_status.electric.charging.model_dump()
    result["range_km"] = energy_status.range.electric_km if energy_status.range else None
    result["last_seen"] = energy_status.last_seen
    return json.dumps(result)
```

**Pattern**:
1. Extract `vehicle_id` (and any other args) as function parameters (FastMCP infers the schema from type hints/`Annotated`)
2. Call the adapter method(s) — `get_vehicle_info` now calls both `get_vehicle()` and
   `get_energy_status()` to merge identity with a quick energy snapshot
3. Return **a JSON string** built with `json.dumps(...)` — tools here return `str`, not `TextContent`
   (FastMCP wraps the return value for the wire protocol itself)
4. On a not-found vehicle, return `json.dumps({"error": "..."})`. `get_charging_status`
   additionally returns `{"error": "..."}` when the vehicle resolves but doesn't support charging
   — so "not found" is not the only error case for that tool; there is still no other "not
   supported" response to model beyond that, since unsupported operations simply have no tool.

### The 3 Tools (Complete List — Nothing Else Exists)
`get_vehicles`, `get_vehicle_info`, `get_charging_status`
— all in `src/weconnect_mcp/server/mixins/read_tools.py`. Two tools were merged away rather than
kept as duplicates: `get_vehicle_state` returned byte-identical data to `get_vehicle_info` (no
richer combined snapshot exists for this backend); `get_battery_status` returned fields that were
either already present elsewhere (`battery_level_percent` was literally
`charging.current_soc_percent` under a different name) or have since been folded into
`get_vehicle_info`/`get_charging_status` directly (`range_km`, `is_plugged_in`).

### Prompts
11 workflow prompts in `src/weconnect_mcp/server/mixins/prompts.py`, registered via
`register_prompts()`. Steps that would need a command (start charging, climate control) are
advisory-only — they tell the user to act via the vehicle's own app. Steps that would need GPS
position ask the user for the location instead of calling a tool.

## Logging

Configured centrally in `src/weconnect_mcp/cli/logging_config.py` (`configure_logging()`,
`get_logger()`) — chooses the right stream (stdout for `http` transport, stderr for `stdio`),
optionally writes to a file, and clamps third-party library levels.

```python
from weconnect_mcp.cli import logging_config
logger = logging_config.get_logger(__name__)

logger.debug("Detailed debug info")
logger.info("Important state change")
logger.warning("Unexpected but handled")
logger.error("Error that needs attention")
```

**MCP Requirement**: In `stdio` transport, all logs go to `stderr` (MCP uses `stdout` for the protocol).

## Documentation

### Docstrings
Use Google-style docstrings:

```python
def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
    """Get vehicle info. Fields with no Tibber equivalent stay None.

    Args:
        vehicle_id: VIN, name, or license plate
        details: BASIC, FULL, or ALL

    Returns:
        VehicleModel, or None if the vehicle isn't found
    """
```

### Comments
- Explain **why**, not **what** (code should be self-explanatory)
- Document Tibber API quirks/limitations (many already documented at the top of each module)
- Mark TODOs with `# TODO: description`

## Git Workflow

### Commits
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Keep commits atomic (one logical change)
- Run tests before committing: `./scripts/test.sh`

### Keeping Docs in Sync (Important)
Whenever you add, remove, or rename an MCP tool or prompt, update **all** of:
`README.md`, `src/weconnect_mcp/server/AI_INSTRUCTIONS.md`,
`src/weconnect_mcp/server/mixins/read_tools.py`, `src/weconnect_mcp/server/mixins/prompts.py`.
These four are the source of truth for the exposed interface and must stay consistent.

## Quick Reference

### Add a New Read Tool
1. Add a method to `TibberAdapter` in `src/weconnect_mcp/adapter/tibber_adapter.py` (and, if it
   needs new extraction logic, to `TibberStateExtractionMixin` in
   `src/weconnect_mcp/adapter/mixins/tibber_state_extraction_mixin.py`)
2. Add the corresponding abstract method + Pydantic model to `AbstractAdapter` in
   `src/weconnect_mcp/adapter/abstract_adapter.py` if needed
3. Implement the same method on `TestAdapter` in `tests/test_adapter.py`
4. Register the tool in `src/weconnect_mcp/server/mixins/read_tools.py`
5. Add tests in `tests/tools/test_*.py`
6. Update `README.md` and `src/weconnect_mcp/server/AI_INSTRUCTIONS.md` (see "Keeping Docs in Sync" above)
7. Run tests: `./scripts/test.sh` (all 47+ must pass)

### There is no "Add New Command" section
No command surface exists on this backend — see "Critical Context" above.

### Run / Debug the MCP Server
```bash
# stdio (local, for Claude Desktop / VS Code Copilot)
python -m weconnect_mcp.cli.mcp_server_cli src/tibber_config.json

# http (cloud / local API access)
python -m weconnect_mcp.cli.mcp_server_cli --transport http --port 8089

# Or via the installed console script (pyproject.toml [project.scripts]):
weconnect-mcp src/tibber_config.json

# One-time interactive Tibber login (required before the server can start):
python -m weconnect_mcp.cli.tibber_login_cli src/tibber_config.json
# or: weconnect-tibber-login

# Test with MCP inspector:
npx @modelcontextprotocol/inspector python -m weconnect_mcp.cli.mcp_server_cli
```

There is no `weconnect_mcp.server.__main__` — `python -m weconnect_mcp.server` does not work.
The entry point is always `weconnect_mcp.cli.mcp_server_cli` (module `main()` or the `weconnect-mcp`
console script).

---

**Remember**: This is a read-only MCP server backed by the Tibber Data API. The code should be
reliable, well-typed, and handle Tibber's narrow, mostly-`None` data surface gracefully — but there
is no VW-direct unreliability to work around anymore, and no command surface to guard. When in
doubt, return `None` or a `{"error": ...}` dict rather than crashing, and don't invent a tool or
method for something Tibber simply doesn't expose.
