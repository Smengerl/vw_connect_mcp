# AI Instructions for WeConnect MCP Server (Tibber backend)

**Purpose**: Access vehicle data via the [Tibber Data API](https://data-api.tibber.com/docs/) through Model Context Protocol (MCP) — this project was originally built for Volkswagen (used because direct VW WeConnect API access is currently blocked to third parties), but the Tibber backend itself is **not VW-specific**: Tibber's vehicle integration is backed by Enode (see `ARCHITECTURE.md` §1.1), which covers 30+ EV brands. Any vehicle paired to the connected Tibber account works — the `brand` field reflects whatever that vehicle actually is (e.g. `"Volkswagen"` for the vehicle this project was verified against), not a fixed value.

**Key Features**:
- Read a small, confirmed set of vehicle data: identity (VIN, brand, model, name, online state) and charging/range status (state of charge, target SOC, range, plug status, charging state)
- Automatic caching (5 minutes) to be a polite API citizen
- Electric vehicles only — Tibber's vehicle integration only ever reports EVs (true across every brand it supports, not a VW-specific restriction)

**Critical Limitation** ⚠️ — **this server is read-only, full stop**:
The Tibber Data API has no write/command endpoints at all (confirmed by reading its full OpenAPI schema — see `ARCHITECTURE.md` §3). There is **no lock/unlock, climate control, charging start/stop, lights, or window heating tool at all** — not a tool that exists and fails, simply no such tool. If a user asks to lock the car, start charging, or precondition the cabin, tell them directly that this server currently cannot do that (see "What This Server Cannot Do" below).

**Second limitation** — narrow read surface: doors, windows, tyres, lights, climatization status, window heating status, GPS position, maintenance schedule, odometer, license plate, model year, and software version are **not available**. Only identity + charging/range data exists. See "What This Server Can Do" below for the complete list — there is nothing beyond it.

---

## MCP Server Architecture

This server provides **Tools** and **Prompts** via the Model Context Protocol — no Resources layer (a URI-based, 1:1 duplicate of the tools with no realized benefit for the MCP clients this project targets was considered and deliberately removed; see `src/weconnect_mcp/server/mixins/read_tools.py`'s module docstring for the reasoning).

### **MCP Tools**
- **5 total tools, all fully functional** — every tool below reliably returns real data; nothing is registered "for interface compatibility" that always fails:
  - `get_vehicles()` - List all vehicles
  - `get_vehicle_info(vehicle_id)` - Identity: manufacturer, model, name, online state
  - `get_vehicle_state(vehicle_id)` - Same data as `get_vehicle_info` (no richer snapshot exists for this backend)
  - `get_battery_status(vehicle_id)` - Battery level, range, charging flag
  - `get_charging_status(vehicle_id)` - Charging state, plug status, target/current SOC

### **MCP Prompts**
- **11 workflow prompts** (`src/weconnect_mcp/server/mixins/prompts.py`), each usable with this backend. Steps that would have needed a command (start/stop charging, climate control) are advisory-only — they tell the user to act via the vehicle's own app instead of calling a tool, since no such tool exists. Steps that would have needed GPS position ask the user for the location instead of calling a tool.

---

## What This Server CAN Do

Only these data points exist, for electric vehicles only:

| Data | Tool |
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

**No commands, ever** — lock/unlock doors, start/stop climate control, start/stop charging, flash lights, honk, or window heating. The Tibber Data API has no write endpoint, so there is no tool for any of this at all.

**No physical/location/maintenance data** — door lock state, window state, tyre pressure, exterior lights, climatization state, window heating state, GPS position, service/inspection schedule, odometer, license plate, model year, software version. There is no tool for any of this either.

**If a user asks for any of the above**: say plainly that this server cannot do it, and why (Tibber's public API is read-only and only reports charging/range data) — don't guess at a tool name and try calling it; check the tool list above first.

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
Use `get_vehicles`, `get_vehicle_info`, `get_vehicle_state`, `get_battery_status`, `get_charging_status` — these are the only 5 tools that exist.

### 4. Do NOT Attempt Control
There is no command tool in this deployment. If the user wants to lock the car, precondition the cabin, or start charging, tell them this server can only read status, not control the vehicle.

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

There is no sixth tool. Door/window/tyre/light/climate/position/maintenance queries and every vehicle command simply have no corresponding tool — don't guess a name and try calling it.

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

There is no meaningful pre-trip check, remote climate control, charging control, security, or "find my car" workflow with this server — all of those need commands or position/door data that don't exist here. (The 11 prompts in `prompts.py` work around this by asking the user for location and telling them to act via their vehicle's own app where a command would otherwise be needed.)

---

## Best Practices (for AI Assistants)

### 1. Always Start with Discovery
`get_vehicles()` first, to validate the vehicle exists and see its exact name/VIN.

### 2. Use Readable Vehicle Names
Prefer `"ID.7"` over the full VIN.

### 3. Know the Boundary
There are only 5 tools, and all 5 return real data: `get_vehicles`, `get_vehicle_info`, `get_vehicle_state`, `get_battery_status`, `get_charging_status`. Nothing else exists — no physical status, climate, position, maintenance, or command tool. Don't guess a tool name; check "What This Server CAN Do" above.

### 4. Trust the Cache
Data is cached for 5 minutes automatically.

### 5. Handle Errors Gracefully
A tool returns `{"error": "..."}` only when the vehicle identifier doesn't resolve to a known vehicle. That's the only error case — there's no "not supported" response to reason about, since unsupported operations simply have no tool.

### 6. Don't Attempt Charging/Climate/Lock Workflows
There is no command tool of any kind. If the user wants control, say so directly instead of looking for a tool that doesn't exist.

---

## Technical Details

### Caching Behavior
- **Duration**: 5 minutes (300 seconds)
- **Purpose**: Be a polite Tibber API citizen; Tibber's own docs ask clients to implement backoff and avoid excessive polling.

### Vehicle Identification
- **Name**: `"ID.7"` etc. — matched case-insensitively
- **VIN**: exact match. For our confirmed VW/Enode-backed vehicle, Tibber's `externalId` is the bare VIN (no vendor prefix, unlike some other brands Tibber supports) — see `ARCHITECTURE.md` §3.1.
- **License Plate**: NOT SUPPORTED (Tibber doesn't provide it)

### Architecture (Internal)
The server uses a modular mixin-based architecture:
- **CacheMixin**: Handles data caching and invalidation
- **VehicleResolutionMixin**: Resolves names/VINs to vehicle identifiers
- **TibberStateExtractionMixin**: Extracts charging/range state from Tibber's 5-capability device-detail response
- **TibberAdapter** (`src/weconnect_mcp/adapter/tibber_adapter.py`): Orchestrates the above. `AbstractAdapter` only declares the methods Tibber can actually back (`list_vehicles`, `get_vehicle`, `get_energy_status`, `shutdown`) — there are no command methods or physical/climate/position/maintenance read methods to be no-ops in the first place.
- **TibberDataAPI** (`src/weconnect_mcp/adapter/tibber_client.py`): OAuth2 (Authorization Code + PKCE) client. Requires a token file produced once, interactively, by `weconnect_mcp.cli.tibber_login_cli` — the adapter itself never opens a browser.

---

## Known Limitations

### 1. Read-Only — No Control At All
The Tibber Data API has no write endpoints (confirmed via its OpenAPI schema). This is permanent and structural, not a temporary rate limit or bug — see `ARCHITECTURE.md` §3.

### 2. Narrow Data Surface
Only identity + 5 charging/range capabilities exist. Doors, windows, tyres, lights, climatization, window heating, position, maintenance, odometer, license plate, model year, software version: none of these have a Tibber equivalent. See the full 51-point comparison against the old VW-direct `carconnectivity` library (now removed, still available on its own permanent branch) in `ARCHITECTURE.md` §5.

### 3. Electric Vehicles Only
Tibber's vehicle integration only ever reports EVs, regardless of brand — combustion/PHEV fields in the data models are always empty for this backend.

### 4. Token Expiration / Auth
Access tokens last ~1 hour and refresh automatically using a stored refresh token (~30 days). If the refresh token itself expires or is revoked, the server will fail to start with a clear `TibberAuthError` — re-run `weconnect_mcp.cli.tibber_login_cli` to re-authorize (a one-time interactive step; the running server can't do this itself, by design — see "Architecture" above).

### 5. Cache Freshness
Data is cached for 5 minutes; a very recent state change made through the vehicle's own app (or Tibber's app) may take up to 5 minutes to show up here.

---

## Error Handling

Tools return a single error format when the vehicle identifier doesn't resolve:

```json
{
  "error": "Vehicle ID.7 not found"
}
```

There is no other error case: every tool that exists is fully functional, so an error always means an unresolvable `vehicle_id` — use `get_vehicles()` to confirm the vehicle exists.

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
(There is no `start_charging` tool to call — don't look for one. State the limitation directly.)

---

## Summary (TL;DR for AI Assistants)

1. **Always start** with `get_vehicles()` to discover available vehicles
2. **There are only 5 tools, and all 5 work**: `get_vehicles`, `get_vehicle_info`, `get_vehicle_state`, `get_battery_status`, `get_charging_status`
3. **Nothing else exists** — no physical status, climate, position, maintenance, or command tool of any kind
4. **No control is possible** — if asked to lock/unlock/charge/climate/flash, say so directly, there's no tool to attempt
5. **License plates DON'T WORK** — Tibber doesn't provide them
6. **Cache is automatic** — 5 minutes
7. **Errors are JSON** — `{"error": "..."}` when a vehicle identifier doesn't resolve; that's the only error case

**Most important**: Be upfront about the read-only, narrow-data nature of this server. Don't look for a tool that doesn't exist and then report its absence as a failure — check the 5-tool list above first.

---

## Technical Reference: Tool Tags

**Operation Type**: `read` (there is no `write`/`command` tag — no such tool exists)
**Functional Areas**: `discovery`, `vehicle-info`, `energy`, `comprehensive`
**Specific Features**: `battery`, `charging`, `bev-phev`

**Usage**: MCP clients can filter tools by tags. All 5 tools are fully functional, so tags here are purely organizational (unlike a hypothetical dual-backend deployment, there's no "check the description to see if it actually works" caveat needed).

---

## Maintainer note: keep docs in sync

**Whenever you add, remove, or rename MCP tools or prompts, you MUST update `README.md` accordingly** to avoid documentation drift.

The source of truth for the exposed interface is:
- **Read tools**: `src/weconnect_mcp/server/mixins/read_tools.py`
- **Prompts**: `src/weconnect_mcp/server/mixins/prompts.py`
- **Agent instructions**: this file (`AI_INSTRUCTIONS.md`)

All three locations (README, AI_INSTRUCTIONS.md, read_tools.py, prompts.py) must stay consistent at all times.
