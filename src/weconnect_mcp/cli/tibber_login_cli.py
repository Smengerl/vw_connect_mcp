"""One-time interactive Tibber Data API login.

Run this once, locally, before starting the MCP server. It runs the OAuth2
Authorization Code + PKCE flow interactively (opens a browser, needs a
human to consent), then caches the resulting tokens to disk. TibberAdapter
itself never does this — it only ever refreshes an existing token
non-interactively, since it must be able to start inside a headless server
process.

Usage:
    python -m weconnect_mcp.cli.tibber_login_cli [config.json]

Credentials come from the same optional JSON file the server itself reads
(src/tibber_config.json, see src/tibber_config.example.json) and/or these
environment variables, which override the file when both are present:
    TIBBER_CLIENT_ID       Required (file or env).
    TIBBER_CLIENT_SECRET   Required (file or env).
    TIBBER_REDIRECT_URI    Optional, default http://localhost:8515/callback.
                           Must match the redirect URI registered on the client.
    TIBBER_TOKEN_PATH      Optional, default is an OS-standard per-user data
                           directory (see tibber_client.default_token_path),
                           not the current directory -- so this and the
                           server default agree without needing to be set.

See ARCHITECTURE.md §2.1 for how to register an OAuth2 client and which
scopes to select.
"""

from __future__ import annotations

import os
import sys

from weconnect_mcp.adapter.tibber_client import (
    TibberAuthError, TibberDataAPI, TokenStore, default_token_path,
)

DEFAULT_REDIRECT = "http://localhost:8515/callback"


def main() -> int:
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    from weconnect_mcp.cli.mcp_server_cli import _load_tibber_file_config

    try:
        file_config = _load_tibber_file_config(config_path)
    except RuntimeError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2

    client_id = os.environ.get("TIBBER_CLIENT_ID") or file_config.get("client_id")
    client_secret = os.environ.get("TIBBER_CLIENT_SECRET") or file_config.get("client_secret")
    redirect_uri = (
        os.environ.get("TIBBER_REDIRECT_URI")
        or file_config.get("redirect_uri")
        or DEFAULT_REDIRECT
    )
    token_path = (
        os.environ.get("TIBBER_TOKEN_PATH")
        or file_config.get("token_path")
        or default_token_path()
    )

    if not client_id:
        print(
            "Missing TIBBER_CLIENT_ID. Register an OAuth2 client at "
            "https://data-api.tibber.com/clients/manage/ and set it via "
            "TIBBER_CLIENT_ID (env) or a credentials file passed as the "
            "first argument -- see src/tibber_config.example.json.",
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
        "default) when starting the server."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
