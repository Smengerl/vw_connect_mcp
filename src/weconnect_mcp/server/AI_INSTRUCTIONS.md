# AI Instructions for WeConnect MCP Server (Tibber backend)

**Purpose**: Access vehicle data via the [Tibber Data API](https://data-api.tibber.com/docs/) through Model Context Protocol (MCP) — this project was originally built for Volkswagen (used because direct VW WeConnect API access is currently blocked to third parties), but the Tibber backend itself is **not VW-specific**: Tibber's vehicle integration is backed by Enode (see `ARCHITECTURE.md` §1.1), which covers 30+ EV brands. Any vehicle paired to the connected Tibber account works — the `brand` field reflects whatever that vehicle actually is (e.g. `"Volkswagen"` for the vehicle this project was verified against), not a fixed value.

**Prerequisite the user must complete themselves**: this server only ever sees vehicles the user has already paired to their Tibber account (in the Tibber app, outside this server entirely). There is no tool to perform or check that pairing. If `get_vehicles()` returns an empty list or is missing a vehicle the user expects, tell them to pair it in the Tibber app first — don't treat it as a bug in this server.

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
- **3 total tools, all fully functional** — every tool below reliably returns real data; nothing is registered "for interface compatibility" that always fails:
  - `get_vehicles()` - List all vehicles
  - `get_vehicle_info(vehicle_id)` - Identity (manufacturer, model, name, online state, last-seen timestamp) plus a quick energy snapshot (electric range, charging flag, plug-connected flag)
  - `get_charging_status(vehicle_id)` - Resolved vehicle VIN/name, charging state, plug status, target/current SOC, electric range, last-seen timestamp

### **MCP Prompts**
- **11 workflow prompts** (`src/weconnect_mcp/server/mixins/prompts.py`), each usable with this backend. Steps that would have needed a command (start/stop charging, climate control) are advisory-only — they tell the user to act via the vehicle's own app instead of calling a tool, since no such tool exists. Steps that would have needed GPS position ask the user for the location instead of calling a tool.

---

## What This Server CAN Do

Only these data points exist, for electric vehicles only:

| Data | Tool |
|---|---|
| VIN, brand, model, name | `get_vehicles()`, `get_vehicle_info()`, `get_charging_status()` (`vin`, `name`) |
| Online/connection state | `get_vehicle_info()` |
| Last-seen timestamp (ISO 8601) | `get_vehicle_info()`, `get_charging_status()` (`last_seen`) |
| Electric range (km) | `get_vehicle_info()`, `get_charging_status()` (`range_km`) |
| Charging flag (bool) | `get_vehicle_info()`, `get_charging_status()` (`is_charging`) |
| Plug connected (bool) | `get_vehicle_info()`, `get_charging_status()` (`is_plugged_in`) |
| Battery level / current SOC (%) | `get_charging_status()` (`current_soc_percent`) |
| Target SOC (%) | `get_charging_status()` |
| Charging state (charging/idle) | `get_charging_status()` |

That's the entire surface.

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
# Returns: [{"vin": "WVWZZZ...", "name": "ID.7", "model": "ID.7"}]
```

### 2. Identify Vehicles
Use either:
- **Vehicle name** (preferred): `"ID.7"` - easier for humans to read
- **VIN**: `"WVWZZZED4SE003938"` - unique identifier

Both formats work automatically. Name matching is by substring, not exact match, and case-insensitive -- `"7"` or `"id"` both resolve to `"ID.7"` if it's the only match. Because of this, `get_vehicle_info` and `get_charging_status` always return the resolved vehicle's actual `vin`/`name` in their response -- check those fields to confirm which vehicle a loose identifier actually matched, especially with more than one vehicle registered. There is no license plate field or lookup -- Tibber never reports one.

### 3. Read Vehicle Data
Use `get_vehicles`, `get_vehicle_info`, `get_charging_status` — these are the only 3 tools that exist.

### 4. Do NOT Attempt Control
There is no command tool in this deployment. If the user wants to lock the car, precondition the cabin, or start charging, tell them this server can only read status, not control the vehicle.

---

## Available Tools (Complete Reference)

All tools return JSON data. Data is cached for 5 minutes.

### Discovery & Basic Info

**`get_vehicles()`**
- **Purpose**: List all available vehicles
- **Returns**: Array of vehicles with VIN, name, model
- **Example**: `get_vehicles()` → `[{"vin": "WVWZZZ...", "name": "ID.7", "model": "ID.7"}]`

**`get_vehicle_info(vehicle_id)`**
- **Purpose**: Vehicle identity plus a quick energy snapshot
- **Parameters**: `vehicle_id` - Vehicle name or VIN
- **Returns**: `manufacturer`, `model`, `name`, `connection_state` ("online"/"offline"), `last_seen` (ISO 8601), `range_km`, `is_charging`, `is_plugged_in`
- **Example**: `get_vehicle_info("ID.7")` → `{"vin": "WVWZZZ...", "model": "ID.7", "name": "ID.7", "manufacturer": "Volkswagen", "connection_state": "online", "last_seen": "2024-01-15T10:31:00Z", "range_km": 346.0, "is_charging": false, "is_plugged_in": false}`

### Energy & Range

**`get_charging_status(vehicle_id)`**
- **Purpose**: Charging/plug status plus electric range
- **Parameters**: `vehicle_id` - Vehicle name or VIN (partial names allowed, see "Identify Vehicles" above)
- **Returns**: `vin`, `name` (the resolved vehicle's actual VIN/name — check these to confirm which vehicle matched, especially when `vehicle_id` was a partial name), `is_charging`, `is_plugged_in`, `charging_state` ("charging"/"idle"), `target_soc_percent`, `current_soc_percent`, `range_km`, `last_seen` (ISO 8601)
- **Example**: `get_charging_status("ID.7")` → `{"vin": "WVWZZZ...", "name": "ID.7", "is_charging": false, "is_plugged_in": false, "charging_state": "idle", "target_soc_percent": 80, "current_soc_percent": 74, "range_km": 346.0, "last_seen": "2024-01-15T10:31:00Z"}`

There is no fourth tool. Door/window/tyre/light/climate/position/maintenance queries and every vehicle command simply have no corresponding tool — don't guess a name and try calling it. There used to be a separate `get_battery_status` tool, but every field it returned duplicated `get_vehicle_info`/`get_charging_status` or is now folded into them, so it was merged away.

---

## Common Usage Patterns

### Quick Battery Check
```python
get_vehicles()
get_charging_status("ID.7")
# Result: 74% charged (current_soc_percent), 346 km range (range_km), not charging
```

### Charging Status Check
```python
get_vehicles()
get_charging_status("ID.7")
# Result: {"is_charging": false, "is_plugged_in": false, "current_soc_percent": 74, "target_soc_percent": 80, "range_km": 346.0}
```

### Basic Vehicle Identity
```python
get_vehicles()
get_vehicle_info("ID.7")
# Result: {"manufacturer": "Volkswagen", "model": "ID.7", "connection_state": "online", "range_km": 346.0, "is_charging": false, "is_plugged_in": false}
```

There is no meaningful pre-trip check, remote climate control, charging control, security, or "find my car" workflow with this server — all of those need commands or position/door data that don't exist here. (The 11 prompts in `prompts.py` work around this by asking the user for location and telling them to act via their vehicle's own app where a command would otherwise be needed.)

---

## Best Practices (for AI Assistants)

### 1. Always Start with Discovery
`get_vehicles()` first, to validate the vehicle exists and see its exact name/VIN.

### 2. Use Readable Vehicle Names
Prefer `"ID.7"` over the full VIN.

### 3. Know the Boundary
There are only 3 tools, and all 3 return real data: `get_vehicles`, `get_vehicle_info`, `get_charging_status`. Nothing else exists — no physical status, climate, position, maintenance, or command tool. Don't guess a tool name; check "What This Server CAN Do" above.

### 4. Trust the Cache
Data is cached for 5 minutes automatically.

### 5. Handle Errors Gracefully
Two distinct error shapes exist — see "Error Handling" below for the full detail:
- `{"error": "..."}`: a per-request problem (unresolvable `vehicle_id`, or — `get_charging_status` only — a vehicle that doesn't support charging). Check the message text to tell the two apart.
- `{"error": "server_unavailable", "error_type": "...", "message": "..."}`: the whole backend is down (auth/config/connectivity problem). Branch on `error_type`, not on `message` text — it's the stable, short code meant for exactly this.

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
- **License Plate**: NOT SUPPORTED — there's no field or lookup path for it at all (Tibber doesn't provide it, and never will for this backend)

### Architecture (Internal)
- **CacheMixin**: The only mixin — handles data caching (freshness tracking, expiry checks); genuinely backend-agnostic, unlike the extraction functions below
- **Device-detail extraction functions** (top of `tibber_adapter.py`): Extract charging/range state from Tibber's 5-capability device-detail response — plain module-level functions, not a mixin, since they're 100% Tibber-specific with exactly one consumer
- **AbstractAdapter.resolve_vehicle_id**: Resolves names/VINs to vehicle identifiers (a concrete default on the base class, not a separate mixin — every adapter inherits the same one implementation)
- **TibberAdapter** (`src/weconnect_mcp/adapter/tibber_adapter.py`): Orchestrates the above. `AbstractAdapter` only declares the methods Tibber can actually back (`list_vehicles`, `get_vehicle`, `get_energy_status`, `shutdown`) — there are no command methods or physical/climate/position/maintenance read methods to be no-ops in the first place.
- **TibberDataAPI** (`src/weconnect_mcp/adapter/tibber_client.py`): OAuth2 (Authorization Code + PKCE) client. Requires a token file produced once, interactively, by `weconnect_mcp.cli.tibber_login_cli` — the adapter itself never opens a browser.

---

## Known Limitations

### 1. Read-Only — No Control At All
The Tibber Data API has no write endpoints (confirmed via its OpenAPI schema). This is permanent and structural, not a temporary rate limit or bug — see `ARCHITECTURE.md` §3.

### 2. Narrow Data Surface
Only identity + 5 charging/range capabilities exist. Doors, windows, tyres, lights, climatization, window heating, position, maintenance, odometer, license plate, model year, software version: none of these have a Tibber equivalent. See the full 51-point comparison against the old VW-direct `carconnectivity` library (now removed, still available on its own permanent branch) in `ARCHITECTURE.md` §5.

### 3. Electric Vehicles Only
Tibber's vehicle integration only ever reports EVs, regardless of brand — there is no combustion/PHEV field in the data models at all for this backend (removed entirely rather than kept as a permanently-empty field).

### 4. Token Expiration / Auth
Access tokens last ~1 hour and refresh automatically using a stored refresh token (~30 days). If the refresh token itself expires or is revoked, every tool call reports a `server_unavailable` error (`error_type: "reauth_required"`) until a human re-authorizes — see "Error Handling" below for the exact codes, the runnable command (embedded in the error's `message`), and — if you have shell access — the runbook for resolving it yourself. Re-authorization is a one-time interactive step; the running server can never do this itself, by design (opening a browser and blocking on human consent is incompatible with a headless server process — see "Architecture" above).

### 5. Cache Freshness
Data is cached for 5 minutes; a very recent state change made through the vehicle's own app (or Tibber's app) may take up to 5 minutes to show up here. `last_seen` (from `get_vehicle_info`/`get_charging_status`) is a separate, independent timestamp — it's when Tibber itself last heard from the vehicle, not when this server last fetched it; use it to judge whether the underlying vehicle data is stale, on top of (not instead of) this 5-minute cache window.

---

## Error Handling

Tools report failures in one of two distinct shapes — check which one you got before reacting:

### Per-request errors: `{"error": "..."}`

These mean the *tool call itself* didn't resolve, not that the server is broken. Retrying the
exact same call won't help; a different `vehicle_id` or a different tool might.

Unresolvable `vehicle_id` (any of the 3 tools):
```json
{
  "error": "Vehicle ID.7 not found"
}
```
Use `get_vehicles()` to confirm the vehicle exists and check the identifier.

Vehicle resolves but doesn't support charging (`get_charging_status` only):
```json
{
  "error": "Vehicle ID.7 not found or doesn't support charging"
}
```
The message text always says which case it is — check it rather than assuming every error is an unresolvable `vehicle_id`.

### Server-wide errors: `{"error": "server_unavailable", "error_type": "...", "message": "..."}`

These mean the whole backend can't serve *any* vehicle data right now — every tool call will fail
identically until the underlying cause is fixed. `error_type` is a stable, short code; `message` is
a human-readable detail that, for the two login-related codes below, **always contains the exact,
ready-to-run shell command for this specific deployment** — it already has the right Python
interpreter and the right credentials-file path baked in (see `tibber_client.default_login_command`
in the server's source if you want the mechanism). **Always read the command out of `message` and
run that string verbatim — never construct your own command** (e.g. a bare `weconnect-tibber-login`
or `python3 -m weconnect_mcp.cli.tibber_login_cli`), since without the exact interpreter/venv and
credentials-file path this deployment uses, a guessed command reliably fails with a confusing,
unrelated error (`command not found`, `ModuleNotFoundError`, or "Missing TIBBER_CLIENT_ID" even
though it *is* configured — just not for whatever interpreter/cwd the guessed command happened to
run under). React on `error_type`, not by pattern-matching the rest of `message`. The same codes
also show up in the `/health` endpoint's JSON in HTTP/cloud mode.

| `error_type` | Meaning | What to tell the user / do |
|---|---|---|
| `not_configured` | `TIBBER_CLIENT_ID`/`TIBBER_CLIENT_SECRET` were never set (no env var, no credentials file) | Tell the user: register an OAuth2 client at https://data-api.tibber.com/clients/manage/, then set both values the way `message` describes (env var, or the credentials file at the path `message` names). **You cannot do the registration step for them** — it happens on Tibber's website, outside this server entirely, and you have no credentials to set until they've done it. Once they confirm it's done, retry the failing tool call — the server rereads a **credentials file** fresh on every reconnect attempt, so editing it takes effect without a restart; an **environment variable**, however, only takes effect for a process launched *after* it's set, so if that's how they configured it, a server restart genuinely is required this one time — tell them so rather than having them retry indefinitely. |
| `invalid_client` | Tibber rejected the *configured* `TIBBER_CLIENT_ID`/`TIBBER_CLIENT_SECRET` outright (client deleted, secret rotated, typo) | Tell the user this is **not** an expired-login problem — running the login command will not fix it and you should not attempt it. They need to check the client still exists and the secret matches at https://data-api.tibber.com/clients/manage/, then fix the configured value (same file/env `message` points at) and retry. |
| `reauth_required` | The one-time interactive login was never done, or the refresh token expired/was revoked (~30 days) | **If you have a shell/Bash tool for this same machine: run the fix yourself, don't just describe it to the user.** See the runbook below this table — this is the normal, expected path for an agent like Claude Code. Only fall back to giving the user the command from `message` to run themselves if you have no shell tool at all, or it's a remote/cloud MCP connection with no access to the server's host. |
| `network_error` | The server couldn't reach Tibber's API at all — token endpoint or data endpoint alike (DNS/connection/timeout) | Transient and unrelated to credentials. Tell the user it looks like a connectivity issue reaching Tibber, and suggest retrying shortly. Retries happen automatically (see below) — no restart needed either way. |
| `unavailable` | Generic fallback for a failure that doesn't fit the categories above (e.g. Tibber's token endpoint returned an unexpected 5xx, or an OAuth error code this server doesn't specifically recognize) | Report the `message` text to the user as-is; suggest retrying, and escalating to the server operator if it persists. |

#### Runbook: resolving `reauth_required` when you have shell access

This is the single most common failure a fresh setup hits (no login done yet), and — unlike
`not_configured`/`invalid_client` — it's one you can usually resolve completely yourself, without
making the user open a terminal at all. Concretely:

0. **Check whether `message` itself says this is a container/cloud deployment first.** If the
   server is running inside Docker/Railway, `message` already knows it and describes a completely
   different fix (run the login locally on the human's own machine, then bootstrap the deployment
   via `TIBBER_TOKEN_JSON`) instead of a command — in that case skip straight to relaying `message`
   to the user verbatim; you have shell access to the container, not to their machine, so you
   cannot run this step for them no matter how it's phrased.
1. **Otherwise, tell the user what's about to happen before you run anything**: this command opens
   a real browser tab and asks them to click through Tibber's own login/consent screen; it then
   waits (up to a few minutes) for that to complete. Ask for their OK to proceed — this opens a
   browser window and binds a local port, which warrants asking first even though it changes
   nothing risky.
2. **Run the exact command from `message` via your shell tool**, not a paraphrase of it. Use a
   generous timeout (a few minutes) since it blocks until the browser flow completes; do not treat
   "still running" as a hang and kill it prematurely — the human needs time to see the tab and click
   through it.
3. Its own output tells you whether it worked: a line starting `✓ Authorized...` plus a list of
   vehicles found means success. A `✗ ...` line or a non-zero exit means it failed — report that
   output to the user rather than guessing why (e.g. they closed the tab, or waited too long and the
   flow timed out).
4. **No server restart needed — just retry the tool call that originally failed (or wait for the
   next `/health` probe).** The server automatically retries connecting the next time any tool is
   called, or `/health` is checked, after a failure (see `ReconnectingAdapter` in
   `starting_adapter.py`), so once step 2 succeeded, the very next one picks up the fresh login
   itself. If that retry still fails, wait a bit and try once more first — the server cools down
   between reconnect attempts (starting at ~10s, backing off further the longer it stays broken, up
   to 5 minutes) so a persistently broken backend isn't retried on every single call — before
   concluding something else is wrong.

---

## Examples (Copy-Paste Ready)

### Example 1: Quick Status (Range + Charging Flag)
```python
vehicles = get_vehicles()
# Result: [{"name": "ID.7", "model": "ID.7", "vin": "WVWZZZ..."}]

info = get_vehicle_info("ID.7")
# Result: {"vin": "WVWZZZ...", "model": "ID.7", "name": "ID.7", "manufacturer": "Volkswagen",
#          "connection_state": "online", "last_seen": "2024-01-15T10:31:00Z",
#          "range_km": 346.0, "is_charging": false, "is_plugged_in": false}
```

### Example 2: Detailed Charging Status (SOC + Target)
```python
charging = get_charging_status("ID.7")
# Result: {"is_charging": false, "is_plugged_in": false, "charging_state": "idle",
#          "target_soc_percent": 80, "current_soc_percent": 74, "range_km": 346.0,
#          "last_seen": "2024-01-15T10:31:00Z"}
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
2. **There are only 3 tools, and all 3 work**: `get_vehicles`, `get_vehicle_info`, `get_charging_status`
3. **Nothing else exists** — no physical status, climate, position, maintenance, or command tool of any kind
4. **No control is possible** — if asked to lock/unlock/charge/climate/flash, say so directly, there's no tool to attempt
5. **No license plate field or lookup exists at all** — Tibber never provides one, so it isn't part of any tool's response or accepted as an identifier
6. **Cache is automatic** — 5 minutes
7. **Errors are JSON, two shapes** — `{"error": "..."}` for a per-request problem (bad `vehicle_id`, or unsupported charging query); `{"error": "server_unavailable", "error_type": "...", "message": "..."}` when the whole backend is down (auth/config/connectivity) — branch on `error_type`, see "Error Handling" for the full code list and what to do for each

**Most important**: Be upfront about the read-only, narrow-data nature of this server. Don't look for a tool that doesn't exist and then report its absence as a failure — check the 3-tool list above first.

---

## Technical Reference: Tool Tags

**Operation Type**: `read` (there is no `write`/`command` tag — no such tool exists)
**Functional Areas**: `discovery`, `vehicle-info`, `energy`
**Specific Features**: `charging`, `electric`

**Usage**: MCP clients can filter tools by tags. All 3 tools are fully functional, so tags here are purely organizational (unlike a hypothetical dual-backend deployment, there's no "check the description to see if it actually works" caveat needed).

---

## Maintainer note: keep docs in sync

**Whenever you add, remove, or rename MCP tools or prompts, you MUST update `README.md` accordingly** to avoid documentation drift.

The source of truth for the exposed interface is:
- **Read tools**: `src/weconnect_mcp/server/mixins/read_tools.py`
- **Prompts**: `src/weconnect_mcp/server/mixins/prompts.py`
- **Agent instructions**: this file (`AI_INSTRUCTIONS.md`)

All three locations (README, AI_INSTRUCTIONS.md, read_tools.py, prompts.py) must stay consistent at all times.
