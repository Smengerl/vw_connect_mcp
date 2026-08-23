# Architecture: Tibber Data API Integration

This is the durable technical reference for how this project talks to vehicles via the
[Tibber Data API](https://data-api.tibber.com/docs/) — the OAuth2 flow, the API surface, the
current adapter architecture, and what was lost/gained moving here from the original VW-direct
integration. See the root [README.md](README.md) for setup/usage instructions; this doc is about
*why* and *how it works*, not day-to-day operation.

## 1. Why Tibber, not VW directly

VW closed direct third-party access to its WeConnect backend (`emea.bff.cariad.digital`) in
May 2026, requiring cryptographic device attestation that open-source projects can't obtain. This
project's original integration (the [`carconnectivity`](https://github.com/tillsteinbach/CarConnectivity)
library) stopped working as a result; its code lives on, unmaintained, on the permanent
[`carconnectivity` branch](https://github.com/Smengerl/vw_connect_mcp/tree/carconnectivity).

Tibber is an official VW integration partner and exposes vehicle data (paired via the user's
Tibber account) through a public, documented **Tibber Data API** — a different API from the older
Tibber GraphQL API (`developer.tibber.com`, prices/consumption/Pulse only, no vehicles).

### 1.1 Background: Enode (Tibber's backend for vehicles)

Tibber does not talk to vehicle manufacturers directly for this integration. A paired vehicle's
device `id` is an unpadded-base64url string that decodes to human-readable text like
`"volkswagen enode vehicle:<uuid>"` (confirmed live against our own paired VW vehicle) — i.e.
Tibber's vehicle support is itself built on **[Enode](https://enode.com)**, a third-party
middleware/aggregator API giving one unified integration surface across **30+ EV brands** (VW
Group included) plus solar inverters, home batteries, and thermostats.

**This is why the integration is not VW-specific.** Nothing in `tibber_client.py` or
`TibberAdapter` assumes VW — any vehicle paired to the connected Tibber account works identically,
regardless of make. The research and examples throughout this document use a specific paired VW
vehicle (that's what motivated the project), but the finding generalizes.

Enode's own API reportedly supports write operations (start/stop charging, smart-charging
schedules) — but Tibber's public Data API only ever exposes `GET` endpoints (confirmed via its full
OpenAPI schema, see §3). That looks like a deliberate product choice by Tibber, not a technical
ceiling from Enode: Tibber likely keeps charging control inside its own app/orchestration layer.

## 2. Authentication

OAuth2 **Authorization Code Flow** with PKCE. No personal access tokens, no `client_credentials`
grant (confirmed live — see below).

| Item | Value |
|---|---|
| Client registration UI | `https://data-api.tibber.com/clients/manage/` |
| Authorize endpoint | `GET https://thewall.tibber.com/connect/authorize` |
| Token endpoint | `POST https://thewall.tibber.com/connect/token` |
| API base | `https://data-api.tibber.com/v1` |
| Access token lifetime | ~1 hour |
| Refresh token lifetime | ~30 days, **rotating** (every refresh returns a new one, invalidating the old) |

### 2.1 Registering an OAuth2 client

- **Redirect URI**: `http://localhost:8515/callback` (localhost http is fine for local dev per
  Tibber's docs) — must match `TIBBER_REDIRECT_URI`.
- **Scopes** — the registration UI splits these into two groups:
  - *Required scopes* (`openid`, `profile`, `email`, `offline_access`, `data-api-user-read`) —
    auto-included, not individually selectable. (`offline_access` is why a `refresh_token` is
    issued at all — without it you'd redo the browser login every ~1h.)
  - *Category scopes* (you must actively select at least one) — **select exactly**
    `data-api-homes-read` (grants `GET /v1/homes`, the first call in the chain) and
    `data-api-vehicles-read` (the actual target — makes vehicle devices show up in
    `GET /v1/homes/{id}/devices`; **without this specific scope the devices endpoint returns an
    empty list, not an error** — an easy way to misdiagnose a scope problem as "no vehicle
    paired"). Leave `data-api-chargers-read`/`-thermostats-read`/`-energy-systems-read`/
    `-inverters-read`/`-meters-read` unchecked (EVSEs, heat pumps, batteries, inverters, live
    meters — not used here).
- Resulting scope string at authorize-time:
  `openid profile email offline_access data-api-user-read data-api-homes-read data-api-vehicles-read`
- Copy the **client secret** — it is shown only once.
- Adding scopes later requires the user to re-run the consent flow; already-issued tokens don't
  retroactively gain scopes.

### 2.2 Token exchange and refresh

```
POST https://thewall.tibber.com/connect/token
grant_type=authorization_code&code=...&redirect_uri=...&client_id=...&client_secret=...&code_verifier=...
```
```
POST https://thewall.tibber.com/connect/token
grant_type=refresh_token&refresh_token=OLD_REFRESH&client_id=...&client_secret=...
```
React to `401 Unauthorized` by refreshing once and retrying.

### 2.3 No `client_credentials` grant — a refresh token must persist across restarts

**Confirmed live** by testing directly against the token endpoint:

| Request | Response |
|---|---|
| `grant_type=client_credentials` + client_id/secret only | `{"error":"unauthorized_client"}` |
| `grant_type=totally_bogus_grant` (control) | `{"error":"unsupported_grant_type"}` |
| `grant_type=refresh_token` + a real refresh_token | full token set, **including a new, different `refresh_token`** |

The differing error codes matter: `unauthorized_client` means the grant type is recognized but
this client isn't permitted to use it — not "unimplemented." Tibber's tokens represent a specific
end user's consent; `client_secret` alone only proves "this request comes from the registered
app," not *which* user's data to serve. There is no way to avoid persisting something across a
restart — either the `refresh_token` itself, or a full repeat of the interactive login. (This is
why `mcp_server_cli.py` needs `TIBBER_TOKEN_JSON` to bootstrap headless deployments — see the root
README's [Cloud Deployment](README.md#cloud-deployment) section.)

## 3. API reference

Confirmed directly from the OpenAPI playground (`https://data-api.tibber.com/playground/`) — this
is the **full** endpoint surface, nothing else exists:

```
GET /v1/homes
GET /v1/homes/{homeId}/devices
GET /v1/homes/{homeId}/devices/{deviceId}
GET /v1/homes/{homeId}/devices/{deviceId}/history
GET /v1/homes/{homeId}/live-events            (SSE, meters only)
GET /v1/homes/{homeId}/live-events/devices
```

**Every endpoint is `GET`.** There is no write/command endpoint anywhere in the schema — no
start/stop charging, no target-SoC set, no climate control trigger. This is a hard limitation
confirmed by reading the full OpenAPI 3.1 schema, not a documentation gap.

Vehicles are **not** scoped to a home (they're "ambulatory") — a vehicle device shows up under
every home the token can see, provided the vehicles scope is granted.

### 3.1 Vehicle data fields (confirmed live)

Full device-detail response shape (`GET /v1/homes/{homeId}/devices/{deviceId}`), values
genericized:

```json
{
  "id": "<base64url, decodes to 'volkswagen enode vehicle:<uuid>'>",
  "externalId": "<bare VIN, no vendor prefix>",
  "info": { "name": "ID.7", "brand": "Volkswagen", "model": "ID.7" },
  "supportedHistory": { "resolutions": [] },
  "status": { "lastSeen": "<ISO 8601 timestamp>" },
  "attributes": [
    { "id": "vinNumber", "value": "<VIN>" },
    { "id": "isOnline", "value": true }
  ],
  "capabilities": [
    { "id": "storage.stateOfCharge", "description": "state of charge", "value": 74, "unit": "%" },
    { "id": "storage.targetStateOfCharge", "description": "target state of charge", "value": 80, "unit": "%" },
    { "id": "range.remaining", "description": "estimated remaining driving range", "value": 356000, "unit": "m" },
    { "id": "connector.status", "description": "vehicle plug status", "value": "disconnected",
      "availableValues": ["connected", "disconnected", "unknown"] },
    { "id": "charging.status", "description": "vehicle charging status", "value": "idle",
      "availableValues": ["charging", "idle", "unknown"] }
  ]
}
```

- `attributes` — static identity data (`vinNumber`, `isOnline`), separate from `capabilities`.
- `status.lastSeen` — ISO 8601 timestamp of the last vehicle update; useful as a staleness
  indicator.
- `externalId` is the **bare VIN, no `vendor:` prefix** for this VW/Enode-backed vehicle — this
  contradicts the `vendor:VIN` format (e.g. `tesla:5YJSA1E26MF1234567`) that other Tibber-supported
  brands may use (per evcc's own code, see §5). `vin_from_external_id()` in
  `tibber_client.py` handles both: split on `:` and fall back to the whole string if there's no
  match.
- The device `id` is opaque in code — decoding it is informative for debugging only (it's what
  revealed the Enode backend, §1.1).

This is confirmed to be the **complete capability set**: 5 capabilities, no doors/windows/tyres/
lights/climatization/position/maintenance data of any kind for this backend.

| Capability id | Meaning | Unit / values |
|---|---|---|
| `storage.stateOfCharge` | State of charge | % |
| `storage.targetStateOfCharge` | Configured charge limit (read-only) | % |
| `range.remaining` | Estimated range | distance, typically `m` (convert to km) |
| `connector.status` | Plug status | `connected` / `disconnected` / `unknown` |
| `charging.status` | Charging status | `charging` / `idle` / `unknown` |

### 3.2 Mandatory request header

Every request needs a `User-Agent` following `<App>/<Version> [<Library>/<Version>] [(platform
hints)]` — missing/malformed risks throttling. Use exponential backoff with full jitter on
`429`/`5xx`; do not retry `400/401/403/404` — fix the cause instead.

## 4. Current architecture

```
src/weconnect_mcp/
├── adapter/
│   ├── abstract_adapter.py       # AbstractAdapter (ABC) + Pydantic models — the port
│   ├── tibber_adapter.py         # TibberAdapter(CacheMixin, VehicleResolutionMixin,
│   │                             #   TibberStateExtractionMixin, AbstractAdapter)
│   ├── starting_adapter.py       # No-op stub used during async startup (HTTP mode)
│   ├── tibber_client.py          # TibberDataAPI: OAuth2 (Auth Code + PKCE) client, TokenStore
│   └── mixins/
│       ├── cache_mixin.py                   # 5-min data cache
│       ├── vehicle_resolution_mixin.py      # VIN/name/license-plate → VIN resolution
│       └── tibber_state_extraction_mixin.py # Maps the 5 capabilities into ChargingModel/RangeModel
└── server/
    └── mixins/
        ├── read_tools.py         # The 5 MCP tools
        └── prompts.py            # 11 MCP workflow prompts
```

This is a clean ports-and-adapters split: `AbstractAdapter` is the port (an ABC declaring only
`list_vehicles`, `get_vehicle`, `get_energy_status`, `shutdown` — exactly what Tibber can back),
and the MCP tool/prompt registration layer depends only on that interface, never on `TibberAdapter`
directly. There is no Resources layer and no command/write tools — Tibber's API has none to back,
so none are registered (see `read_tools.py`'s module docstring for why this differs from just
returning an error for unsupported operations).

**Auth bootstrap split**: `TibberDataAPI` is constructed with `allow_interactive_login=False`
inside `TibberAdapter`, so the adapter itself can never open a browser or block on user input —
essential for running headless (a background thread in HTTP mode, or inside Docker/Railway). It
raises `TibberAuthError` immediately if no usable cached token exists. The one-time interactive
login that produces that token is a separate tool, `weconnect_mcp.cli.tibber_login_cli`
(`allow_interactive_login=True`), meant to be run locally, once, before first use.

**Why a direct adapter instead of a new CarConnectivity connector**: an earlier design considered
making Tibber a data source *for* the `carconnectivity` library instead (a new connector package
alongside the VW one, leaving the rest of that ecosystem intact). That path was rejected: it would
have required conforming Tibber's 5 flat data points to CarConnectivity's much richer typed
`Attribute`/vehicle object graph (built for a ~40-field source) for no data gain, and would have
coupled this project to `carconnectivity`'s own release/compatibility cadence indefinitely. The
direct `TibberAdapter(AbstractAdapter)` approach is less code, has no such coupling (its only
dependency is `httpx`), and was implemented and verified live end-to-end.

## 5. Data point comparison: Tibber Data API vs. the old VW-direct integration

This project's adapter used to read vehicle state from
[`CarConnectivity`](https://github.com/tillsteinbach/CarConnectivity)'s generic `vehicle`/
`ElectricVehicle` model (doors/windows/lights/climatization/window_heating/position/maintenance/
battery/charging/drive). The table below compares every data point that model exposed against what
the Tibber Data API's 5 vehicle capabilities can actually provide — so it's clear how much a
migration to Tibber cost in lost data, and how much was gained back in return (no longer being
VW-specific).

Legend: ✓ available · — not available via this source.

| Category | Data point | CarConnectivity | Tibber |
|---|---|:---:|:---:|
| **Identity** | VIN | ✓ | ✓ |
| | Brand / manufacturer | ✓ | ✓ |
| | Model | ✓ | ✓ |
| | Name / nickname | ✓ | ✓ |
| | Model year | ✓ | — |
| | License plate | ✓ | — |
| | Vehicle type (car/van/…) | ✓ | — |
| | Steering wheel position | ✓ | — |
| | Gearbox type | ✓ | — |
| | Odometer (total distance) | ✓ | — |
| | Vehicle state (parked/driving/…) | ✓ | — |
| | Online/connection state | ✓ | ✓ |
| | Last-seen timestamp | — | ✓ |
| | Outside temperature | ✓ | — |
| | Software version | ✓ | — |
| | Vehicle images | ✓ | — |
| **Battery / charging** | State of charge (%) | ✓ | ✓ |
| | Target charge limit (%) | ✓ | ✓ |
| | Range (km) | ✓ | ✓ |
| | Plug connected state | ✓ | ✓ |
| | Charging active state | ✓ *(richer enum)* | ✓ *(coarser)* |
| | Charging power (kW) | ✓ | — |
| | Charging rate | ✓ | — |
| | Charging type (AC/DC) | ✓ | — |
| | Estimated time/date charged | ✓ | — |
| | Max charging current | ✓ | — |
| | Plug auto-unlock setting | ✓ | — |
| | Connector lock state | ✓ | — |
| | External power present | ✓ | — |
| | Battery total/available capacity (kWh) | ✓ | — |
| | Battery temperature (cur/min/max) | ✓ | — |
| | Fuel tank level (%, combustion) | ✓ | — *(n/a, Tibber is EV-only anyway)* |
| | AdBlue range/level (diesel) | ✓ | — |
| **Doors** | Lock/open state (overall + per door) | ✓ | — |
| **Windows** | Open state (overall + per window) | ✓ | — |
| **Window heating** | Heating state (overall + front/rear) | ✓ | — |
| **Lights** | Exterior light state (left/right) | ✓ | — |
| **Tyres** | Pressure / temperature per tyre | ✗ *(not in the installed library version)* | — |
| **Climatization** | State, target temp, seat heating, etc. (7 fields) | ✓ | — |
| **Location** | Latitude / longitude / altitude / heading / type | ✓ | — |
| **Maintenance** | Inspection / oil service due date & distance | ✓ | — |

**Bottom line**: of 51 distinct data points, the old integration provided 49; Tibber provides 11
(identity fields + the 5 charging-related capabilities + one field — last-seen — the old
integration didn't even have). Everything physical (doors, windows, tyres, lights, window
heating), all of climatization, GPS position, and the maintenance schedule has **no Tibber
equivalent at all** — not a mapping gap, but data Tibber's API genuinely does not expose. In
exchange, the integration is no longer limited to VW: any of the 30+ brands Tibber/Enode support
works the same way.

## 6. Troubleshooting

**"TIBBER_CLIENT_ID and TIBBER_CLIENT_SECRET must be set"** — neither the config file nor
environment variables supplied credentials. Check `src/tibber_config.json` exists and has the
right keys, or that the env vars are actually reaching the process (an MCP client like Claude
Desktop does **not** inherit your shell's `export`s).

**"No cached Tibber tokens found" / `TibberAuthError`** — run
`python -m weconnect_mcp.cli.tibber_login_cli` once. This backend never opens a browser on its
own, by design, so a missing token always needs that manual step.

**"Token endpoint returned 400: `{\"error\":\"invalid_grant\"}`"** — the `refresh_token` has been
invalidated: either it expired (~30 days), was revoked, or was rotated away by a *different*
successful refresh (Tibber rotates refresh tokens — every successful `grant_type=refresh_token`
call returns a **new** refresh token, invalidating whichever one you had cached elsewhere). Not
recoverable from client id/secret alone (§2.3) — just re-run `tibber_login_cli`; your existing
`client_id`/`client_secret` remain valid, only the token needs regenerating. Don't repeatedly test
raw `refresh_token` grant calls outside this tool's own refresh logic (e.g. manual `curl`
experiments) — each one rotates the token, and if the rotated copy isn't the one your running
server actually persists, you'll invalidate your own working session this way.

## 7. Reference implementation

The open-source EV-charging-control project **evcc** implemented this same integration first:

- Feature request: <https://github.com/evcc-io/evcc/issues/30468>
- Implementation PR: <https://github.com/evcc-io/evcc/pull/30487>
- User docs: <https://docs.evcc.io/en/vehicles/tibber/>

Their vehicle template runs the OAuth2 flow, resolves homes → devices, and reads SoC/range/
charging-status/plug-status/target-SoC off the matched vehicle device (Go implementation).
Confirms independently that this is genuinely read-only in production use — evcc's own docs state
charging control still has to go through a separately-configured wallbox/charger, not through
Tibber.

## 8. Project history

- **2026-08-21** — Initial research: confirmed Tibber Data API as the sanctioned route to vehicle
  data, confirmed read-only via the OpenAPI schema, found evcc's reference implementation.
- **2026-08-21** — Built a standalone OAuth2 PoC, ran it live end-to-end against a real paired VW
  vehicle: login → homes → devices → full device detail with all 5 capabilities confirmed.
- **2026-08-21** — Architecture analysis: confirmed a direct `TibberAdapter(AbstractAdapter)`
  requires no changes to the existing MCP tool layer; compared against a CarConnectivity-connector
  alternative and chose the direct adapter (§4 above).
- **2026-08-21** — Implemented `TibberAdapter`, `tibber_client.py`, `tibber_login_cli.py`; verified
  live end-to-end including the headless-safety guarantee (no cached token → immediate error, no
  browser opened).
- **2026-08-21** — Rewrote the MCP server's self-description (tools/resources/prompts) to describe
  the Tibber backend on its own terms; made Tibber the default backend; closed the Docker/Railway
  token-bootstrap gap with a hybrid env-var-seed + persisted-volume design.
- **2026-08-23** — Removed the `carconnectivity` backend entirely (adapter, CLI flag, MCP
  resources/command tools, tests, docs, dependencies) on `cleanup/remove-carconnectivity`. Tibber
  became the project's only backend. The old code remains permanently available, unmaintained, on
  the `carconnectivity` branch.
- **2026-08-23** — Corrected recurring "VW-only" framing across the project's documentation:
  Tibber's vehicle integration is brand-generic (30+ EV brands via Enode), not VW-specific.
- **2026-08-23** — Consolidated this document and the standalone PoC scripts' README into this
  single architecture doc at the repo root; removed the `experiment/tibber-integration/` PoC
  scripts (superseded by the production code in `src/`).
