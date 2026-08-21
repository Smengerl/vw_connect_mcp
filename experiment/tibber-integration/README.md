# Tibber Data API — login-flow Hello World

Proof-of-concept for reaching VW vehicle data via the **Tibber Data API**
(the sanctioned route now that direct VW BFF access is blocked). This first
step focuses on the **OAuth2 login flow**; reading detailed vehicle state
(SoC, range, charging) is a thin follow-up once auth works.

See [`TIBBER_API.md`](TIBBER_API.md) for the full API reference and research
log. Modelled on evcc's implementation
([PR #30487](https://github.com/evcc-io/evcc/pull/30487)).

## Files

| File | Purpose |
|---|---|
| `tibber_client.py` | Reusable core: OAuth2 (auth code + PKCE), token store, REST calls. **This is the intended basis for the MCP adapter.** |
| `hello_tibber.py` | Entry point: run login flow, then list homes + vehicles. |
| `.env.example` | Template for client id/secret/redirect (copy to `.env`). |

## Setup

1. **Register an OAuth2 client** at
   <https://data-api.tibber.com/clients/manage/>:
   - Redirect URI: `http://localhost:8515/callback` (localhost http is fine
     for local dev per Tibber's docs). Must match `TIBBER_REDIRECT_URI`.
   - Scopes — the registration UI splits these into two groups; here's
     exactly what to do in each:

     **"Required scopes"** (`openid`, `profile`, `email`, `offline_access`,
     `data-api-user-read`) — nothing to do, the UI auto-includes all five,
     they aren't individually selectable. (`offline_access` is why a
     `refresh_token` shows up in the token response at all — without it
     you'd have to redo the browser login every ~1h.)

     **Category scopes** (labelled "these scopes are always included" /
     "select at least one additional scope" — confusing wording, but in
     practice it's a checklist you pick from) — **select exactly these two:**

     | Scope | Why |
     |---|---|
     | `data-api-homes-read` | grants `GET /v1/homes` — the first call in the chain (homes → devices → device detail); our code calls this before it can find any vehicle |
     | `data-api-vehicles-read` | the actual target: makes vehicle devices show up in `GET /v1/homes/{id}/devices`. **Without this scope specifically, the devices endpoint returns an empty list for the vehicle category — you'd get an authorized but data-less response, not an error** — the easy way to misdiagnose this as "no vehicle paired" when it's actually a scope problem. |

     Leave the other five category scopes (`data-api-chargers-read`,
     `data-api-thermostats-read`, `data-api-energy-systems-read`,
     `data-api-inverters-read`, `data-api-meters-read`) **unchecked** — they
     cover device categories (EVSEs, heat pumps, batteries, legacy
     inverters, live meters) this PoC doesn't touch; checking them just adds
     unnecessary consent-screen items for the user.

     End-to-end, the resulting scope string requested at authorize-time
     (what `tibber_client.py`'s `DEFAULT_SCOPES` sends) is:
     ```
     openid profile email offline_access data-api-user-read data-api-homes-read data-api-vehicles-read
     ```
     — five auto-included + the two you actively checked.
   - Copy the **client secret** — it is shown only once.

2. **Configure credentials** (never committed):
   ```bash
   cp .env.example .env
   # edit .env, fill in TIBBER_CLIENT_ID / TIBBER_CLIENT_SECRET
   ```
   The file with your real secrets must be named exactly **`.env`** (not
   `.env.example`) and live in this same directory
   (`experiment/tibber-integration/.env`) — `hello_tibber.py` loads it via
   `load_dotenv(Path(__file__).with_name(".env"))`, so a different name or
   location is silently ignored (the script falls through to "Missing
   TIBBER_CLIENT_ID" instead of erroring on a wrong path). It's covered by
   `.gitignore` under that exact name, so it's never accidentally committed.

3. **Run** (uses the project venv, which already has `httpx` + `python-dotenv`):
   ```bash
   ../../.venv/bin/python hello_tibber.py
   ```
   A browser opens for Tibber login + consent. On success, tokens are cached
   in `.tibber_tokens.json` (gitignored) and subsequent runs reuse/refresh
   them without opening a browser.

Expected output: your Tibber home(s) and the VW vehicle(s) paired to the
account, followed by the full raw device detail (see below).

## Security

- `.env` and `.tibber_tokens.json` are gitignored (locally here **and** at
  the repo root). Secrets/tokens must never be committed.
- The token cache is written with `0600` permissions.
- The client never logs the client secret or tokens (only HTTP error bodies
  from the token endpoint, which do not echo the request).

## Notes / limitations

- The Tibber Data API is **read-only** — there is no charging/climate
  control endpoint (see `TIBBER_API.md` §5). This PoC can read status only.
- `offline_access` scope is required to receive a refresh token.

## Data point comparison: Tibber Data API vs. CarConnectivity

This project's current MCP adapter reads vehicle state from
[`CarConnectivity`](https://github.com/tillsteinbach/CarConnectivity)
(specifically its generic `vehicle`/`ElectricVehicle` model plus the
`doors`/`windows`/`lights`/`climatization`/`window_heating`/`position`/
`maintenance`/`battery`/`charging`/`drive` submodules — see
`src/weconnect_mcp/adapter/mixins/state_extraction_mixin.py` and
`src/weconnect_mcp/adapter/abstract_adapter.py` for exactly what's
currently extracted). The table below compares every data point exposed by
that model against what the Tibber Data API's 5 vehicle capabilities
(confirmed complete set, see `TIBBER_API.md` §5.2) can actually provide,
so it's clear at a glance how much of a migration to Tibber would cost in
lost data.

Legend: ✓ available · — not available via this source.

| Category | Data point | CarConnectivity (attribute) | Tibber Data API (field) | CarConnectivity | Tibber |
|---|---|---|---|:---:|:---:|
| **Identity** | VIN | `vehicle.vin` | `externalId` / `attributes[vinNumber]` | ✓ | ✓ |
| | Brand / manufacturer | `vehicle.manufacturer` | `info.brand` | ✓ | ✓ |
| | Model | `vehicle.model` | `info.model` | ✓ | ✓ |
| | Name / nickname | `vehicle.name` | `info.name` | ✓ | ✓ |
| | Model year | `vehicle.model_year` | — | ✓ | — |
| | License plate | `vehicle.license_plate` | — | ✓ | — |
| | Vehicle type (car/van/…) | `vehicle.type` | — | ✓ | — |
| | Steering wheel position | `vehicle.specification.steering_wheel_position` | — | ✓ | — |
| | Gearbox type | `vehicle.specification.gearbox` | — | ✓ | — |
| | Odometer (total distance) | `vehicle.odometer` | — | ✓ | — |
| | Vehicle state (parked/driving/…) | `vehicle.state` | — | ✓ | — |
| | Online/connection state | `vehicle.connection_state` | `attributes[isOnline]` | ✓ | ✓ |
| | Last-seen timestamp | *(per-attribute internal, not surfaced as a vehicle-level field)* | `status.lastSeen` | — | ✓ |
| | Outside temperature | `vehicle.outside_temperature` | — | ✓ | — |
| | Software version | `vehicle.software.version` | — | ✓ | — |
| | Vehicle images | `vehicle.images` | — | ✓ | — |
| **Battery / charging** | State of charge (%) | `drive.level` (`ElectricDrive`) | `storage.stateOfCharge` | ✓ | ✓ |
| | Target charge limit (%) | `charging.settings.target_level` | `storage.targetStateOfCharge` | ✓ | ✓ |
| | Range (km) | `drives.total_range` / `drive.range` | `range.remaining` | ✓ | ✓ |
| | Plug connected state | `charging.connector.connection_state` | `connector.status` | ✓ | ✓ |
| | Charging active state | `charging.state` (`CHARGING`/`READY_FOR_CHARGING`/`OFF`/`ERROR`) | `charging.status` (`charging`/`idle`/`unknown`) | ✓ *(richer enum)* | ✓ *(coarser)* |
| | Charging power (kW) | `charging.power` | — | ✓ | — |
| | Charging rate | `charging.rate` | — | ✓ | — |
| | Charging type (AC/DC) | `charging.type` | — | ✓ | — |
| | Estimated time/date charged | `charging.estimated_date_reached` | — | ✓ | — |
| | Max charging current | `charging.settings.maximum_current` | — | ✓ | — |
| | Plug auto-unlock setting | `charging.settings.auto_unlock` | — | ✓ | — |
| | Connector lock state | `charging.connector.lock_state` | — | ✓ | — |
| | External power present | `charging.connector.external_power` | — | ✓ | — |
| | Battery total/available capacity (kWh) | `drive.battery.total_capacity` / `.available_capacity` | — | ✓ | — |
| | Battery temperature (cur/min/max) | `drive.battery.temperature` / `_min` / `_max` | — | ✓ | — |
| | Fuel tank level (%, combustion) | `drive.level` (`CombustionDrive`) | — *(n/a, EV only anyway)* | ✓ | — |
| | AdBlue range/level (diesel) | `drive.adblue_range` / `.adblue_level` | — *(n/a)* | ✓ | — |
| **Doors** | Lock/open state (overall + per door) | `vehicle.doors` (+ 6 individual doors) | — | ✓ | — |
| **Windows** | Open state (overall + per window) | `vehicle.windows` (+ 4 individual windows) | — | ✓ | — |
| **Window heating** | Heating state (overall + front/rear) | `vehicle.window_heatings` | — | ✓ | — |
| **Lights** | Exterior light state (left/right) | `vehicle.lights` | — | ✓ | — |
| **Tyres** | Pressure / temperature per tyre | *(referenced in our mixin, but no `tyres` module exists in the installed `carconnectivity==0.9.2` — resolves to `None` today)* | — | ✗ *(not in this lib version)* | — |
| **Climatization** | State (off/heating/cooling/ventilation) | `climatization.state` | — | ✓ | — |
| | Target temperature | `climatization.settings.target_temperature` | — | ✓ | — |
| | Estimated time remaining | `climatization.estimated_date_reached` | — | ✓ | — |
| | Seat heating enabled | `climatization.settings.seat_heating` | — | ✓ | — |
| | Climatization-at-unlock enabled | `climatization.settings.climatization_at_unlock` | — | ✓ | — |
| | Without-external-power setting | `climatization.settings.climatization_without_external_power` | — | ✓ | — |
| | Heater source | `climatization.settings.heater_source` | — | ✓ | — |
| **Location** | Latitude / longitude | `vehicle.position.latitude` / `.longitude` | — | ✓ | — |
| | Altitude | `vehicle.position.altitude` | — | ✓ | — |
| | Heading | `vehicle.position.heading` | — | ✓ | — |
| | Position type (parked/moving) | `vehicle.position.position_type` | — | ✓ | — |
| **Maintenance** | Inspection due date/distance | `maintenance.inspection_due_at` / `_after` | — | ✓ | — |
| | Oil service due date/distance | `maintenance.oil_service_due_at` / `_after` | — | ✓ | — |

**Bottom line:** of the 51 distinct data points listed above, CarConnectivity
provides **49** (everything except tyres, which isn't in the installed
library version, and a vehicle-level last-seen timestamp, which it doesn't
surface). Tibber provides **11**: VIN, brand, model, name, online state,
the 5 charging-related capabilities, and one field — last-seen — that
CarConnectivity doesn't even have. Everything physical (doors, windows,
tyres, lights, window heating), all of climatization, GPS position, and
maintenance schedule has **no Tibber equivalent at all** —
not a mapping gap, but data Tibber's API genuinely does not expose (see
`TIBBER_API.md` §5 — confirmed to be the complete capability set for our
paired vehicle). A Tibber-backed adapter would only ever be a
charging/range-status source, not a drop-in replacement for the
`carconnectivity` VW-direct adapter — see `TIBBER_API.md` §1.1 for why
(Tibber's own product scoping, not a technical ceiling from Enode
underneath it).
