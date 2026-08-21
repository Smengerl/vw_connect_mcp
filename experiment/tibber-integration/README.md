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
   - Scopes: at least `data-api-user-read`, `data-api-homes-read`,
     `data-api-vehicles-read`.
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
