# Tibber Data API as an indirect path to VW vehicle data

**Status:** Research only, no code written yet. API confirmed **read-only**
(no control/command endpoints exist as of this writing) — see §5.
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

Mandatory OpenID: `openid profile email offline_access` (the last one is
required to get a refresh token at all).

Data API category scopes (a device only shows up if the token has the
matching scope):

| Scope | Grants |
|---|---|
| `data-api-user-read` | basic user context — required baseline |
| `data-api-homes-read` | list homes |
| `data-api-vehicles-read` | **electric vehicles — this is the one we need** |
| `data-api-chargers-read` | EV chargers / EVSEs |
| `data-api-thermostats-read` | thermostats/heat pumps/space heaters |
| `data-api-energy-systems-read` | batteries/hybrid systems |
| `data-api-inverters-read` | legacy inverter category |
| `data-api-meters-read` | live real-time meter measurements (Pulse/Watty) |

Minimal set for our use case: `openid profile email offline_access data-api-user-read data-api-homes-read data-api-vehicles-read`.

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

### 5.2 Vehicle data fields (from a working third-party implementation, see §6)

- State of charge (SoC)
- Range (km)
- Charging status (charging / not charging)
- Plug status (connected / disconnected)
- Target SoC (read-only — the charge limit configured elsewhere, not settable here)
- VIN
- Brand / model / name (static identity attributes)

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

<!--
Add new entries above this line, newest at the bottom, oldest at the top —
do not delete or rewrite prior entries, append instead. Update §1's Status
line whenever the overall state changes materially (e.g. once a client is
registered, once live calls succeed, once/if a command endpoint ever
appears).
-->
