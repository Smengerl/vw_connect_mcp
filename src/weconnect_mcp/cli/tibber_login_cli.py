"""One-time interactive Tibber Data API login.

Run this once, locally, before starting the MCP server with the Tibber
backend (`--backend tibber`). It runs the OAuth2 Authorization Code + PKCE
flow interactively (opens a browser, needs a human to consent), then
caches the resulting tokens to disk. TibberAdapter itself never does this
— it only ever refreshes an existing token non-interactively, since it
must be able to start inside a headless server process.

Usage:
    python -m weconnect_mcp.cli.tibber_login_cli

Environment variables (same names TibberAdapter reads at server startup):
    TIBBER_CLIENT_ID       Required. OAuth2 client id.
    TIBBER_CLIENT_SECRET   Required. OAuth2 client secret.
    TIBBER_REDIRECT_URI    Optional, default http://localhost:8515/callback.
                           Must match the redirect URI registered on the client.
    TIBBER_TOKEN_PATH      Optional, default ./tibber_tokens.json.

See experiment/tibber-integration/README.md for how to register an OAuth2
client and which scopes to select.
"""

from __future__ import annotations

import os
import sys

from weconnect_mcp.adapter.tibber_client import TibberAuthError, TibberDataAPI, TokenStore

DEFAULT_REDIRECT = "http://localhost:8515/callback"
DEFAULT_TOKEN_PATH = "./tibber_tokens.json"


def main() -> int:
    client_id = os.environ.get("TIBBER_CLIENT_ID")
    client_secret = os.environ.get("TIBBER_CLIENT_SECRET")
    redirect_uri = os.environ.get("TIBBER_REDIRECT_URI", DEFAULT_REDIRECT)
    token_path = os.environ.get("TIBBER_TOKEN_PATH", DEFAULT_TOKEN_PATH)

    if not client_id:
        print(
            "Missing TIBBER_CLIENT_ID. Register an OAuth2 client at "
            "https://data-api.tibber.com/clients/manage/ and set "
            "TIBBER_CLIENT_ID / TIBBER_CLIENT_SECRET first.",
            file=sys.stderr,
        )
        return 2

    api = TibberDataAPI(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        store=TokenStore(token_path),
        allow_interactive_login=True,
    )

    print("→ Starting interactive Tibber login (browser will open)...")
    try:
        api.ensure_authorized()
    except TibberAuthError as exc:
        print(f"✗ Authorization failed: {exc}", file=sys.stderr)
        return 1
    print(f"✓ Authorized. Tokens cached at: {token_path}")

    print("\n→ Verifying: listing vehicles found in this Tibber account")
    vehicles = api.vehicles()
    if not vehicles:
        print("  (no vehicles found — is a vehicle paired in your Tibber account?)")
    for v in vehicles:
        info = v.get("info", {})
        print(f"  - {info.get('brand', '?')} {info.get('model', '')} '{info.get('name', '')}'")

    print(
        f"\nDone. Point TIBBER_TOKEN_PATH at {token_path} (or leave it at this "
        "default) when starting the server with --backend tibber."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
