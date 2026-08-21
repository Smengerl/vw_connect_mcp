#!/usr/bin/env python3
"""Hello-World for the Tibber Data API login flow.

Runs the OAuth2 Authorization Code + PKCE flow against Tibber, stores the
tokens locally (gitignored), and then makes a couple of read-only calls to
prove the connection works: list homes, list vehicles, then dump the full
device detail (all capabilities Tibber reports) for each vehicle found.

The full-detail dump exists so the raw shape of Tibber's data can be
compared by eye against the target Pydantic models in
../../src/weconnect_mcp/adapter/abstract_adapter.py (ChargingModel,
RangeModel, PositionModel, ...) — the fields the MCP server currently
exposes for VW-direct data — before deciding how a Tibber-backed adapter
would map onto that shape.

Usage:
    1. Register an OAuth2 client at https://data-api.tibber.com/clients/manage/
       - Redirect URI must match TIBBER_REDIRECT_URI below
         (default http://localhost:8515/callback)
       - Scopes: at least data-api-user-read, data-api-homes-read,
         data-api-vehicles-read
    2. cp .env.example .env  and fill in client id/secret
    3. python hello_tibber.py

Note: this prints your real vehicle data (VIN, capability values) to your
own terminal for inspection — nothing here is written to a file or
committed anywhere.
"""

from __future__ import annotations

import json
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

    print("\n→ Full device detail per vehicle (everything Tibber reports)")
    for v in vehicles:
        info = v.get("info", {})
        label = f"{info.get('brand', '?')} {info.get('model', '')}".strip()
        print(f"\n{'=' * 70}\n{label or v.get('id')}\n{'=' * 70}")

        detail = api.device(v["homeId"], v["id"])

        print("\n-- raw JSON (compare against abstract_adapter.py models) --")
        print(json.dumps(detail, indent=2, ensure_ascii=False))

        capabilities = detail.get("capabilities", [])
        print(f"\n-- capabilities ({len(capabilities)} total) --")
        if not capabilities:
            print("  (none reported)")
        for cap in capabilities:
            unit = f" {cap.get('unit')}" if cap.get("unit") else ""
            print(
                f"  {cap.get('id', '?'):<32} = {cap.get('value')!r}{unit}"
                f"   ({cap.get('description', '')})"
            )

    print(
        "\nDone. Compare the capability ids/values above against "
        "TIBBER_API.md §5.2 and the target models in "
        "../../src/weconnect_mcp/adapter/abstract_adapter.py "
        "(ChargingModel, RangeModel/DriveModel, PositionModel, ...) to see "
        "how much of the MCP server's current vehicle-state shape Tibber "
        "can actually fill."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
