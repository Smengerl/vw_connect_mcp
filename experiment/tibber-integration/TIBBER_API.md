# Tibber Data API as an indirect path to VW vehicle data

**Status:** **Confirmed working end-to-end (2026-08-21, live test, see §7).**
OAuth client registered, browser login/pairing completed, and the VW vehicle
was correctly returned from `GET /v1/homes` → `GET /v1/homes/{id}/devices`.
API confirmed **read-only** (no control/command endpoints exist as of this
writing) — see §5.
**Maintained by:** Simon Gerlach (simon.gerlach@gmail.com)
**Started:** 2026-08-21
**Affected/relevant systems:** `data-api.tibber.com` (Tibber Data API),
`thewall.tibber.com` (Tibber's OAuth2 authorization server). Relevant
background: `emea.bff.cariad.digital` (We Connect BFF) — see
[`../vw-device-flow-attestation-bypass/FINDING.md`](../vw-device-flow-attestation-bypass/FINDING.md)
for why the direct VW route is currently blocked.

## 1. Why this document exists

Since VW closed direct third-party BFF access to `emea.bff.cariad.digital`
(see the sibling experiment in this repo), this project has been looking
for an alternative, sanctioned route to read VW vehicle data. Tibber is an
official VW integration partner and exposes vehicle data (paired via the
user's Tibber account) through a public, documented **Tibber Data API**.
This is a *different* API from the older Tibber GraphQL API
(`developer.tibber.com`, used for prices/consumption/Pulse) — that one does
not expose vehicles at all.

### 1.1 Background: Enode (Tibber's backend for VW)

Tibber does not appear to talk to VW/CARIAD directly for this integration.
The device `id` returned for our paired vehicle is unpadded-base64url text
that decodes to `"volkswagen enode vehicle:<uuid>"` (confirmed live,
2026-08-21, see §7) — i.e. Tibber's VW support is itself built on
**[Enode](https://enode.com)**, a third-party middleware/aggregator API.

What Enode is: an API platform that gives one unified integration surface
across 30+ EV brands (VW Group included) plus solar inverters, home
batteries, and thermostats, so a company like Tibber doesn't have to build
and maintain 30 separate manufacturer integrations. Energy retailers,
charging networks, and smart-home platforms use it the same way.

Why this matters for scope/limitations here: **Enode's own API supports
write operations** for EVs — start/stop charging, smart-charging
activation, charging schedules (per Enode's public docs, not independently
verified by us). The fact that the *Tibber* Data API (§5) exposes only
`GET` endpoints therefore looks like **a deliberate choice by Tibber**, not
a technical ceiling imposed by Enode — Tibber likely keeps charging control
inside its own app/orchestration layer rather than exposing it publicly. If
direct control ever becomes a hard requirement, going straight to Enode
(a separate integration, with its own partner/access process — not explored
here) would be the technically-possible route; going through Tibber's
public API is not, today.

This doc is the durable record of what that API is, what it offers, and
how to connect to it, so this doesn't need to be re-researched in a future
session. **Keep this updated** as we build against it — append dated
entries to §7 rather than rewriting history.

## 2. Prerequisites (already satisfied on our side)

- A Tibber account (free tier is sufficient, no energy contract required)
- VW vehicle already paired/connected inside the Tibber account (done)

## 3. Authentication

OAuth2 **Authorization Code Flow** (PKCE optional but recommended). No
personal access tokens (unlike the old GraphQL API).

| Item | Value |
|---|---|
| Client registration UI | `https://data-api.tibber.com/clients/manage/` |
| Authorize endpoint | `GET https://thewall.tibber.com/connect/authorize` |
| Token endpoint | `POST https://thewall.tibber.com/connect/token` |
| API base | `https://data-api.tibber.com/v1` |
| Access token lifetime | ~1 hour (JWT, opaque to us — treat as bearer) |
| Refresh token lifetime | ~30 days, rotating / possibly one-time-use |

### 3.1 Authorization request

```
GET https://thewall.tibber.com/connect/authorize?response_type=code
  &client_id=YOUR_CLIENT_ID
  &redirect_uri=YOUR_ENCODED_REDIRECT_URI
  &scope=openid%20profile%20email%20offline_access%20data-api-user-read%20data-api-homes-read%20data-api-vehicles-read
  &state=opaqueState
```
Add `&code_challenge=...&code_challenge_method=S256` for PKCE.

### 3.2 Token exchange

```
POST https://thewall.tibber.com/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=AUTH_CODE
&redirect_uri=YOUR_REDIRECT_URI
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
```
(add `code_verifier=...` if PKCE was used). Response:
```json
{ "access_token": "...", "refresh_token": "...", "expires_in": 3600, "token_type": "Bearer" }
```

### 3.3 Refresh

```
POST https://thewall.tibber.com/connect/token
grant_type=refresh_token&refresh_token=OLD_REFRESH&client_id=...&client_secret=...
```
React to `401 Unauthorized` by refreshing once and retrying.

## 4. Scopes

**Correction (2026-08-21, see §7):** the client-registration UI at
`data-api.tibber.com/clients/manage/` groups scopes differently than earlier
wording here implied. There are two distinct groups, not one flat list:

**Required (baseline) — auto-included, not individually selectable in the UI:**

| Scope | Grants |
|---|---|
| `openid` | user identifier |
| `profile` | user profile (first/last name etc.) |
| `email` | email address |
| `offline_access` | refresh tokens — without this you'd have to redo the browser login every ~1h |
| `data-api-user-read` | basic user context |

**Category scopes — you must actively select at least one of these:**

| Scope | Grants |
|---|---|
| `data-api-homes-read` | list homes (`GET /v1/homes`) — **select this**, our flow enumerates homes before devices |
| `data-api-vehicles-read` | **electric vehicles — select this, it's the one we actually need** |
| `data-api-chargers-read` | EV chargers / EVSEs — not needed for this PoC |
| `data-api-thermostats-read` | thermostats/heat pumps/space heaters — not needed |
| `data-api-energy-systems-read` | batteries/hybrid systems — not needed |
| `data-api-inverters-read` | legacy inverter category — not needed |
| `data-api-meters-read` | live real-time meter measurements (Pulse/Watty) — not needed |

For our use case: select exactly `data-api-homes-read` and
`data-api-vehicles-read` from the category list; the five baseline scopes
come along automatically. The resulting scope string requested at
authorize-time is unchanged from before:
`openid profile email offline_access data-api-user-read data-api-homes-read data-api-vehicles-read`
— what changed is only which of these you pick vs. get for free in the
registration UI.

Adding scopes later requires the user to re-run the consent flow — tokens
already issued don't retroactively gain scopes.

## 5. Endpoints and what they return

Confirmed directly from the OpenAPI playground (`https://data-api.tibber.com/playground/`) — **this is the full endpoint surface, nothing else exists**:

```
GET /v1/homes
GET /v1/homes/{homeId}/devices
GET /v1/homes/{homeId}/devices/{deviceId}
GET /v1/homes/{homeId}/devices/{deviceId}/history
GET /v1/homes/{homeId}/live-events            (SSE, meters only — Pulse/Watty)
GET /v1/homes/{homeId}/live-events/devices
```

**Every endpoint is `GET`. There is no write/command endpoint anywhere in
the schema** — no start/stop charging, no target-SoC set, no climate
control trigger. This is a hard limitation, not something we're missing in
the docs: confirmed by reading the full OpenAPI 3.1 schema in the
playground on 2026-08-21.

Vehicles are **not** scoped to a home (they're "ambulatory") — a vehicle
device shows up under every home the token can see, provided the
`vehicles` scope is granted.

### 5.1 Practical call sequence

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" https://data-api.tibber.com/v1/homes
curl -H "Authorization: Bearer $ACCESS_TOKEN" https://data-api.tibber.com/v1/homes/HOME_ID/devices
curl -H "Authorization: Bearer $ACCESS_TOKEN" https://data-api.tibber.com/v1/homes/HOME_ID/devices/DEVICE_ID
```
Filter the devices list for the vehicle device (category/type indicates
"vehicle"), then match by VIN if multiple vehicles are present.

### 5.2 Vehicle data fields (confirmed live, 2026-08-21, see §7)

Full device detail response shape, confirmed against our own paired VW
(`GET /v1/homes/{homeId}/devices/{deviceId}`), values redacted/genericized
here per the redaction convention in the sibling FINDING.md:

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

Notes on fields beyond `capabilities`:
- `attributes` — a separate array (not `capabilities`) for mostly-static
  identity data; observed `vinNumber` (duplicates `externalId` for this
  vehicle) and `isOnline` (bool, connectivity status — this is the
  `attributes` category mentioned in the API overview as "seldom changing
  properties").
- `status.lastSeen` — ISO 8601 timestamp of last update from the vehicle;
  useful as a staleness indicator, no such field exists per-capability.
- `supportedHistory.resolutions` — empty array for this vehicle, i.e.
  `GET .../history` has nothing to return for it (history support is
  device-category/vendor dependent, not guaranteed for vehicles).
- Numeric capabilities carry a `unit` field; enum-valued ones
  (`connector.status`, `charging.status`) instead carry `availableValues`
  listing every possible value — useful for building an exhaustive mapping
  without guessing.

`externalId` was confirmed to be the **bare VIN, no `vendor:` prefix** —
this contradicts evcc's own doc comment (`Device.VIN()` in `api.go`)
suggesting a `vendor:VIN` format like `tesla:5YJSA1E26MF1234567`. Real
implementations should try splitting on `:` and fall back to the whole
string if there's no match (that's what evcc's own code already does
defensively, and what our Python client should do too once VIN extraction
is added — not implemented yet; `hello_tibber.py` currently just prints
the raw `externalId`).

The `id` (device id) is an **unpadded base64url string**; decoding it is
informative for debugging — see §1.1 for what it revealed (Tibber's VW
integration is Enode-backed). Treat it as opaque in code regardless — don't
rely on this internal structure, it's just useful for a human inspecting a
live response.

Relevant capability ids and their reported values:

| Capability id | Meaning | Unit / values |
|---|---|---|
| `storage.stateOfCharge` | State of charge | % |
| `storage.targetStateOfCharge` | Configured charge limit (read-only) | % |
| `range.remaining` | Estimated range | distance, typically `m` (convert to km) |
| `connector.status` | Plug status | `connected` / `disconnected` / `unknown` |
| `charging.status` | Charging status | `charging` / `idle` / `unknown` |

This is confirmed to be the **complete capability set** for this vehicle —
no doors/windows/tyres/lights/climatization/position/maintenance data of
any kind, unlike what the VW-direct `carconnectivity` adapter exposes (see
`src/weconnect_mcp/adapter/mixins/state_extraction_mixin.py` for that full
shape). A Tibber-backed adapter could only ever fill a small slice of the
MCP server's current `ChargingModel`/`RangeModel` fields — nothing else in
`abstract_adapter.py` (doors, windows, tyres, lights, climatization,
position, maintenance) has a Tibber equivalent.

### 5.3 Mandatory request header

Every request needs a `User-Agent` following `<App>/<Version> [<Library>/<Version>] [(platform hints)]`,
e.g. `weconnect-mcp/0.1.0 (github.com/<org>/weconnect_mvp)`. Missing/malformed
User-Agent risks throttling. Use exponential backoff with full jitter on
`429`/`5xx`; do **not** retry `400/401/403/404` — fix the cause instead.

## 6. Reference implementation (not ours, but working code to model against)

The open-source EV-charging-control project **evcc** already implemented
exactly this integration:

- Feature request: https://github.com/evcc-io/evcc/issues/30468
- Implementation PR: https://github.com/evcc-io/evcc/pull/30487
- User docs: https://docs.evcc.io/en/vehicles/tibber/

Their vehicle template (`type: template`, `template: tibber`) takes
`clientid`/`clientsecret`/`redirecturi`/`vin`/`capacity`, runs the OAuth2
flow, resolves homes → devices, and reads `Soc()`, `Range()`,
`ChargingStatus()`, `PlugStatus()`, `TargetSoc()` off the matched vehicle
device (Go implementation). Confirms independently that this is genuinely
read-only in production use — evcc's own docs state charging control still
has to go through a separately-configured wallbox/charger, not through
Tibber.

## 7. Session log

### 2026-08-21 — initial research, no code yet
- Established the Tibber Data API (`data-api.tibber.com`) is the correct,
  documented, currently-working route to VW vehicle data now that the
  direct BFF path is blocked (see sibling experiment
  `vw-device-flow-attestation-bypass`).
- Walked the full docs site (overview, auth, scopes, quick start,
  requirements) and the OpenAPI playground directly in a browser to get
  primary-source endpoint/scope/flow details rather than relying on
  secondhand summaries.
- **Confirmed the API is read-only**: the OpenAPI schema in the playground
  lists only `GET` operations, no command/control endpoints. This directly
  affects project scope — if remote *control* (start/stop charging,
  climate) is a goal, Tibber's public API cannot do that today; it can only
  supply status (SoC, range, charging/plug state).
- Identified evcc's existing implementation (§6) as a working reference we
  can model our own OAuth2 client/device-lookup code on.
- No OAuth client registered yet, no live calls made against
  `data-api.tibber.com` yet — next session should register a client at
  `data-api.tibber.com/clients/manage/` and run the flow end-to-end against
  our own paired vehicle.

### 2026-08-21 — login-flow Hello World implemented
- Read evcc's full Go implementation (`vehicle/tibber/{oauth,api,service}.go`,
  `vehicle/tibber.go`) as the reference. Confirmed the exact OAuth2 config
  (endpoints in §3, scope list in §4) and the precise capability ids now in
  §5.2 (`storage.stateOfCharge`, `range.remaining`, `connector.status`,
  `charging.status`, `storage.targetStateOfCharge`). evcc uses auth code +
  PKCE with a confidential client (sends both client_secret and PKCE).
- Built a dependency-light Python PoC in this directory:
  - `tibber_client.py` — reusable core (OAuth2 auth-code+PKCE via a local
    loopback redirect catcher, `TokenStore` with 0600 perms, `homes()` /
    `devices()` / `device()` / `vehicles()`). Intended basis for the MCP
    adapter later.
  - `hello_tibber.py` — runs the login flow, then lists homes + vehicles.
  - `.env.example`, `.gitignore`, `README.md`.
- Uses only `httpx` + `python-dotenv` (both already in the project venv) +
  stdlib — no new dependencies added to pyproject.
- Secrets hygiene verified: `.env` and `.tibber_tokens.json` confirmed
  gitignored (both here and via repo-root .gitignore); token cache written
  0600; client never logs secrets/tokens.
- Sanity-tested offline: syntax/import OK, PKCE S256 challenge matches,
  TokenSet expiry/refresh-skew logic correct, missing-credentials path
  exits cleanly. **Not yet run end-to-end** — needs a real OAuth client
  registered at `data-api.tibber.com/clients/manage/` with redirect URI
  `http://localhost:8515/callback`. That's the next step.

### 2026-08-21 — correction: scope grouping in the actual registration UI
- While registering a real OAuth client, Simon observed the actual
  `data-api.tibber.com/clients/manage/` UI groups scopes differently than
  §4 previously implied: `openid`, `profile`, `email`, `offline_access`,
  and **`data-api-user-read`** are a "Required scopes" group that's
  auto-included (not individually picked), and the seven `data-api-*-read`
  category scopes are a separate list from which the UI requires
  **selecting at least one**.
- This does **not** change the scope string requested at authorize-time
  (§3.1) or anything in `tibber_client.py`'s `DEFAULT_SCOPES` — only the
  earlier explanation of *which scopes you actively pick in the
  registration UI* was wrong (it implied `data-api-user-read` was one of
  three you'd select; it's actually auto-included, and only
  `data-api-homes-read` + `data-api-vehicles-read` need active selection).
  §4 corrected accordingly.

### 2026-08-21 — live end-to-end success: login + vehicle read confirmed
- Registered a real OAuth2 client at `data-api.tibber.com/clients/manage/`
  with the corrected scopes from §4 and redirect URI
  `http://localhost:8515/callback`.
- Ran `hello_tibber.py` end-to-end for the first time: browser login/consent
  completed, tokens issued and cached (`.tibber_tokens.json`, confirmed
  still gitignored/not committed), `GET /v1/homes` returned exactly one
  home, and `GET /v1/homes/{id}/devices` correctly returned the paired VW
  ID.7 as a vehicle device.
- **This is the first live confirmation that the whole chain works**:
  Tibber pairing → OAuth2 client → auth code + PKCE flow → homes → devices
  → a real VW vehicle, with no VW BFF access involved at any point.
- Two corrections to §5.2 from what was actually observed in the response
  (see there for detail): (a) `externalId` for this VW/Enode-backed vehicle
  is the bare VIN, not `vendor:VIN` as evcc's Tesla example suggested — code
  must not assume the `:` separator is always present; (b) the device `id`
  is unpadded-base64url and decodes to human-readable
  `"<backend> <category>:<uuid>"` text — decoding ours confirmed the VW
  integration is Enode-backed under the hood.
- Real VIN, home address, and device id from this run are deliberately
  **not** reproduced verbatim in this document, same rationale as the
  sibling `vw-device-flow-attestation-bypass/FINDING.md` — only the
  structural/format findings are kept.
- **Not yet done:** fetching device *detail* (`GET .../devices/{deviceId}`)
  to read the actual capability values (SoC, range, charging/plug status)
  — `hello_tibber.py` currently stops after listing vehicles. That's the
  next concrete step, then wiring this into the MCP adapter.

### 2026-08-21 — device-detail dump + Enode background documented
- Extended `hello_tibber.py` to fetch and print full device detail
  (`api.device(homeId, deviceId)`) for every vehicle found — raw JSON plus
  a per-capability table — so the shape can be visually compared against
  the MCP server's current target models in `abstract_adapter.py`. Ran it
  live; confirmed the full response shape now written into §5.2 (the
  `attributes` array with `vinNumber`/`isOnline`, `status.lastSeen`,
  `supportedHistory.resolutions`, and that `capabilities` really is only
  the same 5 entries already documented — nothing more was hiding).
- **Conclusion from the comparison:** Tibber's data can only ever populate
  a thin slice of `ChargingModel`/`RangeModel` — SoC, target SoC, range,
  plug/charging status. Everything else the MCP server currently exposes
  via `carconnectivity` (doors, windows, tyres, lights, climatization,
  position, maintenance) has **no Tibber equivalent** — confirmed absent
  from the capability list, not just unmapped. Any Tibber-backed adapter
  path would need to either accept that reduced feature set or combine
  Tibber with another data source for the rest.
- Added §1.1 documenting Enode as the middleware Tibber's VW integration is
  built on (per the device-id decoding finding from the previous session)
  and noting that Enode's own API supports write operations (start/stop
  charging etc.) even though Tibber's public Data API doesn't expose any —
  so the read-only limitation in §5 looks like Tibber's own product choice,
  not a hard ceiling from Enode.
- **Process note, unrelated to the API itself:** while tidying up after
  this test run, a cleanup command mistakenly deleted the real, working
  `.env` and `.tibber_tokens.json` (mistook them for leftover test
  artifacts from an earlier, unrelated gitignore check in this same
  session). `.tibber_tokens.json` is inconsequential — it regenerates on
  next run via the browser flow. `.env` (client id/secret) is only a
  problem if the client secret wasn't saved anywhere outside this
  directory, since Tibber shows it once at client-creation time; if lost,
  the fix is registering a new OAuth2 client. Flagging this here in case a
  future session needs the context for why credentials had to be
  re-entered.

<!--
Add new entries above this line, newest at the bottom, oldest at the top —
do not delete or rewrite prior entries, append instead. Update §1's Status
line whenever the overall state changes materially (e.g. once a client is
registered, once live calls succeed, once/if a command endpoint ever
appears).
-->
