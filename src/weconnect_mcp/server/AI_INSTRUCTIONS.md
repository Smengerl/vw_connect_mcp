# AI Instructions for WeConnect MCP Server (Tibber backend)

**Purpose**: Access Volkswagen vehicle data via the [Tibber Data API](https://data-api.tibber.com/docs/) through Model Context Protocol (MCP) — used because direct VW WeConnect API access is currently blocked to third parties (see `experiment/vw-device-flow-attestation-bypass/FINDING.md`). Tibber's VW integration is backed by Enode (see `experiment/tibber-integration/TIBBER_API.md` §1.1).

**Key Features**:
- Read a small, confirmed set of vehicle data: identity (VIN, brand, model, name, online state) and charging/range status (state of charge, target SOC, range, plug status, charging state)
- Automatic caching (5 minutes) to be a polite API citizen
- Electric vehicles only — Tibber's VW integration only ever reports EVs

**Critical Limitation** ⚠️ — **this backend is read-only, full stop**:
The Tibber Data API has no write/command endpoints at all (confirmed by reading its full OpenAPI schema — see `experiment/tibber-integration/TIBBER_API.md` §5). **Every command tool** (lock/unlock, climate control, charging start/stop, lights, window heating) **always returns `{"success": false}`**, regardless of vehicle or parameters. This is not a bug or a missing feature — the underlying API genuinely cannot do this. If a user asks to lock the car, start charging, or precondition the cabin, tell them directly that this server currently cannot do that (see "What This Server Cannot Do" below) rather than attempting the command and hoping.

**Second limitation** — narrow read surface: doors, windows, tyres, lights, climatization status, window heating status, GPS position, maintenance schedule, odometer, license plate, model year, and software version are **not available**. Only identity + charging/range data exists. See "What This Server Can Do" below for the complete list — there is nothing beyond it.

---

## MCP Server Architecture

This server provides **both Tools and Resources** via the Model Context Protocol. The tool/resource *registrations* are shared code (the same `read_tools.py` / `command_tools.py` / `resources.py` also back a VW-direct `carconnectivity` backend on other branches) — but every description below reflects what's **actually true when this server is running the Tibber backend**, not a generic dual-backend description.

### **MCP Tools** (Preferred for AI Assistants)
- **18 total tools**: 8 read-only tools + 10 command tools
- **Read tools that work** (`readOnlyHint: true`, `idempotentHint: true`):
  - `get_vehicles()` - List all vehicles
  - `get_vehicle_info(vehicle_id)` - Identity: manufacturer, model, name, online state
  - `get_vehicle_state(vehicle_id)` - Same data as `get_vehicle_info` (no richer snapshot exists for this backend)
  - `get_battery_status(vehicle_id)` - Battery level, range, charging flag
  - `get_charging_status(vehicle_id)` - Charging state, plug status, target/current SOC
- **Read tools that always fail** (registered, but the underlying data doesn't exist — always return a "not found" error, never a crash):
  - `get_vehicle_doors(vehicle_id)`, `get_climatization_status(vehicle_id)`, `get_vehicle_position(vehicle_id)`
- **Command tools — all 10 always fail** (`readOnlyHint: false`, always return `{"success": false, "error": "Not supported: the Tibber Data API is read-only..."}`):
  - `lock_vehicle`, `unlock_vehicle`, `start_climatization`, `stop_climatization`, `start_charging`, `stop_charging`, `flash_lights`, `honk_and_flash`, `start_window_heating`, `stop_window_heating`

### **MCP Resources** (Alternative Access Pattern)
- **URI-based data access** with server-side caching
- **14 resources** (all read-only, prefixed with `res_`), same split as tools:
  - **Work**: `data://vehicles`, `data://vehicle/{id}/info`, `data://vehicle/{id}/state`, `data://vehicle/{id}/charging`, `data://vehicle/{id}/range`, `data://vehicle/{id}/battery`
  - **Always error** (no Tibber data): `data://vehicle/{id}/doors`, `.../windows`, `.../tyres`, `.../type`, `.../climate`, `.../maintenance`, `.../window-heating`, `.../lights`, `.../position`
- **When to use**: When you need declarative data references or server-side caching semantics
- **When NOT to use**: Most AI interactions should use Tools (more intuitive function-call interface)

### **Recommendation for AI Assistants**
**Always use Tools** (not Resources) for interactive conversations.

---

## What This Server CAN Do

Only these data points exist, for electric vehicles only:

| Data | Tool/Resource |
|---|---|
| VIN, brand, model, name | `get_vehicles()`, `get_vehicle_info()` |
| Online/connection state | `get_vehicle_info()` |
| Battery level (%) | `get_battery_status()` |
| Electric range (km) | `get_battery_status()` |
| Target SOC (%) | `get_charging_status()` |
| Plug connected (bool) | `get_charging_status()` (`is_plugged_in`) |
| Charging state (charging/idle) | `get_charging_status()` |

That's the entire surface. `charging_power_kw` and `remaining_time_minutes` are always present as fields in the JSON but always `null` — Tibber doesn't report them.

## What This Server CANNOT Do

**No commands, ever** — lock/unlock doors, start/stop climate control, start/stop charging, flash lights, honk, or window heating. The Tibber Data API has no write endpoint. Every command tool call returns `{"success": false, "error": "Not supported: the Tibber Data API is read-only (no command endpoints exist)."}`.

**No physical/location/maintenance data** — door lock state, window state, tyre pressure, exterior lights, climatization state, window heating state, GPS position, service/inspection schedule, odometer, license plate, model year, software version. All the corresponding tools/resources exist (for interface compatibility with the VW-direct backend) but always return a "not found" error — that's expected, not a bug.

**If a user asks for any of the above**: say plainly that this server (running the Tibber backend) cannot do it, and why (Tibber's public API is read-only and only reports charging/range data) — don't try the tool and then explain the failure, and don't imply it might work "sometimes."

---

## Quick Start Guide (for AI Assistants)

### 1. Discover Available Vehicles
**Always start here!** Call `get_vehicles()` to see what vehicles are available.

```python
get_vehicles()
# Returns: [{"vin": "WVWZZZ...", "name": "ID.7", "model": "ID.7", "license_plate": null}]
```

### 2. Identify Vehicles
Use either:
- **Vehicle name** (preferred): `"ID.7"` - easier for humans to read
- **VIN**: `"WVWZZZED4SE003938"` - unique identifier

Both formats work automatically. `license_plate` is always `null` (not available via Tibber).

### 3. Read Vehicle Data
Use `get_vehicles`, `get_vehicle_info`, `get_battery_status`, `get_charging_status`. Nothing else returns real data — see "What This Server CAN Do" above.

### 4. Do NOT Attempt Control
There is no working command in this deployment. If the user wants to lock the car, precondition the cabin, or start charging, tell them this server can only read status, not control the vehicle.

---

## Available Tools (Complete Reference)

All tools return JSON data. Data is cached for 5 minutes.

### Discovery & Basic Info

**`get_vehicles()`**
- **Purpose**: List all available vehicles
- **Returns**: Array of vehicles with VIN, name, model (`license_plate` always `null`)
- **Example**: `get_vehicles()` → `[{"vin": "WVWZZZ...", "name": "ID.7", "model": "ID.7", "license_plate": null}]`

**`get_vehicle_info(vehicle_id)`**
- **Purpose**: Get basic vehicle identity
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: `manufacturer`, `model`, `name`, `connection_state` ("online"/"offline"). `license_plate`, `odometer`, `state`, `type`, `software_version`, `model_year` are always `null`.
- **Example**: `get_vehicle_info("ID.7")` → `{"model": "ID.7", "manufacturer": "Volkswagen", "connection_state": "online", "odometer": null, ...}`

**`get_vehicle_state(vehicle_id)`**
- **Purpose**: Same identity data as `get_vehicle_info` — there is no richer combined snapshot for this backend (no doors/windows/climate/tyres to add).

### Energy & Range

**`get_battery_status(vehicle_id)`**
- **Purpose**: Quick battery check
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: Battery level (%), electric range (km), charging status
- **Example**: `get_battery_status("ID.7")` → `{"battery_level_percent": 74, "range_km": 346.0, "is_charging": false}`

**`get_charging_status(vehicle_id)`**
- **Purpose**: Charging/plug status
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: `is_charging`, `is_plugged_in`, `charging_state` ("charging"/"idle"), `target_soc_percent`, `current_soc_percent`. `charging_power_kw` and `remaining_time_minutes` are always `null`.
- **Example**: `get_charging_status("ID.7")` → `{"is_charging": false, "is_plugged_in": false, "charging_state": "idle", "target_soc_percent": 80, "current_soc_percent": 74}`

### Not Available (documented for completeness — always fail)

**`get_vehicle_doors(vehicle_id)`**, **`get_climatization_status(vehicle_id)`**, **`get_vehicle_position(vehicle_id)`** — all return `{"error": "..."}`. Don't call these unless you need to demonstrate/confirm they're unsupported.

---

## Available Resources (URI-Based Data Access)

Same split as tools. Working: `data://vehicles`, `data://vehicle/{id}/info`, `data://vehicle/{id}/state`, `data://vehicle/{id}/charging`, `data://vehicle/{id}/range`, `data://vehicle/{id}/battery`. Always error: `data://vehicle/{id}/doors`, `.../windows`, `.../tyres`, `.../type`, `.../climate`, `.../maintenance`, `.../window-heating`, `.../lights`, `.../position`. See each resource's `description` field (in `resources.py`) for the specific reason.

---

## Control Commands (Write Operations) — ALL UNSUPPORTED

Every command tool below is registered (for interface compatibility) but **always returns `{"success": false, "error": "Not supported: the Tibber Data API is read-only (no command endpoints exist)."}`** — regardless of vehicle state, parameters, or retries. Do not attempt workarounds (retrying, waiting, checking status first) — the result will not change, because the underlying API has no endpoint to call.

- `lock_vehicle(vehicle_id)`, `unlock_vehicle(vehicle_id)`
- `start_climatization(vehicle_id, target_temp_celsius=None)`, `stop_climatization(vehicle_id)`
- `start_charging(vehicle_id)`, `stop_charging(vehicle_id)`
- `flash_lights(vehicle_id, duration_seconds=None)`, `honk_and_flash(vehicle_id, duration_seconds=None)`
- `start_window_heating(vehicle_id)`, `stop_window_heating(vehicle_id)`

If a user asks to control the vehicle, respond directly: "This server currently only reads vehicle status via Tibber (read-only API) — it can't lock/unlock, control climate, or start/stop charging." Do not call the command tool "to check" — the answer is always the same and calling it wastes a round trip.

---

## Common Usage Patterns

### Quick Battery Check
```python
get_vehicles()
get_battery_status("ID.7")
# Result: Battery at 74%, 346 km range, not charging
```

### Charging Status Check
```python
get_vehicles()
get_charging_status("ID.7")
# Result: {"is_charging": false, "is_plugged_in": false, "current_soc_percent": 74, "target_soc_percent": 80}
```

### Basic Vehicle Identity
```python
get_vehicles()
get_vehicle_info("ID.7")
# Result: {"manufacturer": "Volkswagen", "model": "ID.7", "connection_state": "online"}
```

There is no meaningful pre-trip check, remote climate control, charging control, security, or "find my car" workflow with this backend — all of those need commands or position/door data that don't exist here.

---

## Best Practices (for AI Assistants)

### 1. Always Start with Discovery
`get_vehicles()` first, to validate the vehicle exists and see its exact name/VIN.

### 2. Use Readable Vehicle Names
Prefer `"ID.7"` over the full VIN.

### 3. Know the Boundary
Only 3 tools return real data: `get_vehicles`, `get_vehicle_info`/`get_vehicle_state`, `get_battery_status`, `get_charging_status`. Everything else — physical status, climate, position, maintenance, and every command — always fails. Don't guess; check "What This Server CAN Do" above before calling an unfamiliar tool.

### 4. Trust the Cache
Data is cached for 5 minutes automatically. There is no cache-invalidation-after-command behavior to reason about, since no command ever succeeds.

### 5. Handle Errors Gracefully
Read tools that don't apply to this backend return `{"error": "..."}`. Command tools always return `{"success": false, "error": "..."}`. Neither indicates a transient failure worth retrying.

### 6. Don't Attempt Charging/Climate/Lock Workflows
Unlike a VW-direct backend, there is no "verify command succeeded" pattern to follow here, because no command can succeed. If the user wants control, say so directly instead of running a doomed multi-step workflow.

---

## Technical Details

### Caching Behavior
- **Duration**: 5 minutes (300 seconds)
- **Purpose**: Be a polite Tibber API citizen; Tibber's own docs ask clients to implement backoff and avoid excessive polling.
- **No command-triggered invalidation is meaningful**: no command ever changes server-observable state.

### Vehicle Identification
- **Name**: `"ID.7"` etc. — matched case-insensitively
- **VIN**: exact match. For our confirmed VW/Enode-backed vehicle, Tibber's `externalId` is the bare VIN (no vendor prefix, unlike some other brands Tibber supports) — see `experiment/tibber-integration/TIBBER_API.md` §5.2.
- **License Plate**: NOT SUPPORTED (Tibber doesn't provide it — same net effect as the prior VW-API limitation, different root cause)

### Architecture (Internal)
The server uses a modular mixin-based architecture. With the Tibber backend specifically:
- **CacheMixin**: Handles data caching and invalidation (shared with the VW-direct backend)
- **VehicleResolutionMixin**: Resolves names/VINs to vehicle identifiers (shared)
- **TibberStateExtractionMixin**: Extracts charging/range state from Tibber's 5-capability device-detail response
- **TibberAdapter** (`src/weconnect_mcp/adapter/tibber_adapter.py`): Orchestrates the above; every command method and every physical/climate/position/maintenance read method is a fixed no-op/None by design, not a partial implementation
- **TibberDataAPI** (`src/weconnect_mcp/adapter/tibber_client.py`): OAuth2 (Authorization Code + PKCE) client. Requires a token file produced once, interactively, by `weconnect_mcp.cli.tibber_login_cli` — the adapter itself never opens a browser.

---

## Known Limitations

### 1. Read-Only — No Control At All
The Tibber Data API has no write endpoints (confirmed via its OpenAPI schema). This is permanent and structural, not a temporary rate limit or bug — see `experiment/tibber-integration/TIBBER_API.md` §5.

### 2. Narrow Data Surface
Only identity + 5 charging/range capabilities exist. Doors, windows, tyres, lights, climatization, window heating, position, maintenance, odometer, license plate, model year, software version: none of these have a Tibber equivalent. See the full 51-point comparison against the VW-direct `carconnectivity` library in `experiment/tibber-integration/README.md`.

### 3. Electric Vehicles Only
Tibber's VW integration only ever reports EVs — combustion/PHEV fields in the data models are always empty for this backend.

### 4. Token Expiration / Auth
Access tokens last ~1 hour and refresh automatically using a stored refresh token (~30 days). If the refresh token itself expires or is revoked, the server will fail to start with a clear `TibberAuthError` — re-run `weconnect_mcp.cli.tibber_login_cli` to re-authorize (a one-time interactive step; the running server can't do this itself, by design — see "Architecture" above).

### 5. Cache Freshness
Data is cached for 5 minutes; a very recent state change made through the Tibber/VW app itself may take up to 5 minutes to show up here.

---

## Error Handling

All tools return consistent error format:

```json
{
  "success": false,
  "error": "Not supported: the Tibber Data API is read-only (no command endpoints exist)."
}
```

or, for a read tool with no data for this backend:

```json
{
  "error": "Vehicle ID.7 not found"
}
```

### Common Errors

**"Vehicle not found"**
- Cause: Invalid `vehicle_id`, or (for `get_vehicle_doors`/`get_climatization_status`/`get_vehicle_position`) simply that no such data exists for this backend
- Solution: Use `get_vehicles()` to confirm the vehicle exists; if it does and the error persists on one of those three tools, that's expected — see "What This Server CANNOT Do"

**"Not supported: the Tibber Data API is read-only..."**
- Cause: Any command tool was called
- Solution: None — inform the user this server cannot control the vehicle

---

## Examples (Copy-Paste Ready)

### Example 1: Battery Check
```python
vehicles = get_vehicles()
# Result: [{"name": "ID.7", "model": "ID.7", "vin": "WVWZZZ..."}]

battery = get_battery_status("ID.7")
# Result: {"battery_level_percent": 74, "range_km": 346.0, "is_charging": false}
```

### Example 2: Charging Status
```python
charging = get_charging_status("ID.7")
# Result: {"is_charging": false, "is_plugged_in": false, "charging_state": "idle",
#          "target_soc_percent": 80, "current_soc_percent": 74}
```

### Example 3: User Asks to Start Charging
```
User: "Start charging my ID.7"
AI: "I can't do that — this server reads vehicle status via Tibber's API, which is
     read-only. It has no way to start or stop charging remotely. Current status:
     74% charged, not plugged in, target 80%."
```
(Do not call `start_charging()` first and then explain the failure — the outcome is
always the same, so state the limitation directly.)

---

## Summary (TL;DR for AI Assistants)

1. **Always start** with `get_vehicles()` to discover available vehicles
2. **Only 4 tools return real data**: `get_vehicles`, `get_vehicle_info`/`get_vehicle_state`, `get_battery_status`, `get_charging_status`
3. **Everything else always fails**: physical status, climate, position, maintenance (no data), and all 10 commands (read-only API)
4. **No control is possible** — if asked to lock/unlock/charge/climate/flash, say so directly, don't attempt the command
5. **License plates DON'T WORK** — Tibber doesn't provide them
6. **Cache is automatic** — 5 minutes, no command-triggered refresh (nothing to refresh)
7. **Errors are JSON** — `{"error": ...}` for missing data, `{"success": false, "error": ...}` for commands

**Most important**: Be upfront about the read-only, narrow-data nature of this backend. Don't run multi-step "verify the command worked" workflows — no command can work.

---

## Technical Reference: Tool & Resource Tags

Unchanged from the underlying interface (tags describe intent, not backend support — check the description text of each tool/resource for whether it actually works with Tibber):

**Operation Type**: `read`, `write`/`command`
**Functional Areas**: `discovery`, `vehicle-info`, `physical`, `energy`, `climate`, `location`, `security`
**Specific Features**: `battery`, `charging`, `gps`, `comfort`, `locator`, `lights`, `horn`, `defrost`, `comprehensive`
**Vehicle Type Filters**: `bev-phev`

**Usage**: MCP clients can filter tools by tags, but tags alone don't indicate Tibber support — always check the tool/resource `description` field, which is written per-backend-reality in this deployment.

---

## Maintainer note: keep docs in sync

**Whenever you add, remove, or rename MCP tools or resources, you MUST update `README.md` accordingly** to avoid documentation drift.

The source of truth for the exposed interface is:
- **Read tools**: `src/weconnect_mcp/server/mixins/read_tools.py`
- **Command tools**: `src/weconnect_mcp/server/mixins/command_tools.py`
- **Resources**: `src/weconnect_mcp/server/mixins/resources.py`
- **Prompts**: `src/weconnect_mcp/server/mixins/prompts.py`
- **Agent instructions**: this file (`AI_INSTRUCTIONS.md`)

All five locations (README, AI_INSTRUCTIONS.md, read_tools.py, command_tools.py, resources.py, prompts.py) must stay consistent at all times. **This version of this file describes the Tibber backend specifically** (as requested — no dual-backend hedging); if the server is run with the `carconnectivity` backend instead, these descriptions do not apply and this file would need a corresponding rewrite back toward VW-direct capabilities.
