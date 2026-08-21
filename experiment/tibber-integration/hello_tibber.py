#!/usr/bin/env python3
"""Hello-World for the Tibber Data API login flow.

Runs the OAuth2 Authorization Code + PKCE flow against Tibber, stores the
tokens locally (gitignored), and then makes a couple of read-only calls to
prove the connection works: list homes, then list vehicles.

Usage:
    1. Register an OAuth2 client at https://data-api.tibber.com/clients/manage/
       - Redirect URI must match TIBBER_REDIRECT_URI below
         (default http://localhost:8515/callback)
       - Scopes: at least data-api-user-read, data-api-homes-read,
         data-api-vehicles-read
    2. cp .env.example .env  and fill in client id/secret
    3. python hello_tibber.py

This intentionally focuses on the *login* first; reading detailed vehicle
capabilities (SoC, range, ...) is a thin follow-up once auth works.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Optional .env loading (python-dotenv is available in this project's venv).
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass

from tibber_client import TibberDataAPI, TokenStore

HERE = Path(__file__).parent
DEFAULT_TOKEN_PATH = HERE / ".tibber_tokens.json"
DEFAULT_REDIRECT = "http://localhost:8515/callback"


def main() -> int:
    client_id = os.environ.get("TIBBER_CLIENT_ID")
    client_secret = os.environ.get("TIBBER_CLIENT_SECRET")
    redirect_uri = os.environ.get("TIBBER_REDIRECT_URI", DEFAULT_REDIRECT)
    token_path = os.environ.get("TIBBER_TOKEN_PATH", str(DEFAULT_TOKEN_PATH))

    if not client_id:
        print(
            "Missing TIBBER_CLIENT_ID. Copy .env.example to .env and fill in "
            "the client id/secret from https://data-api.tibber.com/clients/manage/",
            file=sys.stderr,
        )
        return 2

    api = TibberDataAPI(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        store=TokenStore(token_path),
    )

    print("→ Ensuring authorization (browser flow runs only on first use)...")
    api.ensure_authorized()
    print("✓ Authorized. Tokens cached at:", token_path)

    print("\n→ GET /homes")
    homes = api.homes()
    if not homes:
        print("  (no homes returned)")
    for h in homes:
        print(f"  - {h.get('name', '?')}  (id={h.get('id')})")

    print("\n→ Vehicles across all homes")
    vehicles = api.vehicles()
    if not vehicles:
        print("  (no vehicles found — is a VW paired in your Tibber account?)")
    for v in vehicles:
        info = v.get("info", {})
        print(
            f"  - {info.get('brand', '?')} {info.get('model', '')} "
            f"'{info.get('name', '')}'  "
            f"externalId={v.get('externalId')}  "
            f"(deviceId={v.get('id')}, homeId={v.get('homeId')})"
        )

    print("\nDone. Next step: fetch device detail (SoC/range/charging) via "
          "api.device(homeId, deviceId).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
