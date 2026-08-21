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
   - Scopes — request exactly the following seven (all are consumed by
     `DEFAULT_SCOPES` in `tibber_client.py`; leaving one out breaks the flow
     in a specific way, see below):

     | Scope | Why it's needed |
     |---|---|
     | `openid` | standard OIDC — required baseline for any login |
     | `profile` | standard OIDC — required baseline |
     | `email` | standard OIDC — required baseline |
     | `offline_access` | without this, the token response has **no** `refresh_token` — you'd have to redo the browser login every ~1h |
     | `data-api-user-read` | Data-API baseline; without it, `/v1/homes` and everything downstream 403s even with the other scopes present |
     | `data-api-homes-read` | grants `GET /v1/homes` — the first call in the chain (homes → devices → device detail) |
     | `data-api-vehicles-read` | the actual target: makes vehicle devices show up in `GET /v1/homes/{id}/devices`. **Without this scope specifically, the devices endpoint returns an empty list for the vehicle category — you'd get an authorized but data-less response, not an error**, which is the easy way to misdiagnose this as "no vehicle paired" when it's actually a scope problem. |

     As one space-separated string for the client form / authorize URL:
     ```
     openid profile email offline_access data-api-user-read data-api-homes-read data-api-vehicles-read
     ```
     Do **not** request `data-api-chargers-read`, `data-api-thermostats-read`,
     `data-api-energy-systems-read`, `data-api-inverters-read`, or
     `data-api-meters-read` for this PoC — they exist (see `TIBBER_API.md`
     §4) but cover other device categories (EVSEs, heat pumps, batteries,
     meters) we don't touch here; requesting them just adds unnecessary
     consent-screen items for the user.
   - Copy the **client secret** — it is shown only once.

2. **Configure credentials** (never committed):
   ```bash
   cp .env.example .env
   # edit .env, fill in TIBBER_CLIENT_ID / TIBBER_CLIENT_SECRET
   ```

3. **Run** (uses the project venv, which already has `httpx` + `python-dotenv`):
   ```bash
   ../../.venv/bin/python hello_tibber.py
   ```
   A browser opens for Tibber login + consent. On success, tokens are cached
   in `.tibber_tokens.json` (gitignored) and subsequent runs reuse/refresh
   them without opening a browser.

Expected output: your Tibber home(s) and the VW vehicle(s) paired to the
account, with their `externalId` (`vendor:VIN`) and device id.

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
