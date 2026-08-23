"""Tibber Data API client — OAuth2 (Authorization Code + PKCE) + REST.

Read-only vehicle data access via the Tibber Data API, used as an
alternative to the VW-direct carconnectivity adapter now that VW has
blocked third-party BFF access (see ../../../ARCHITECTURE.md for the full
research and current architecture this adapter is based on).

Ported from this project's original tibber-integration PoC script (see
ARCHITECTURE.md's project history, §8) with one structural change: the
interactive browser login flow is opt-in
(``allow_interactive_login``) and OFF by default here, because this module
runs inside the MCP server process, which must never block startup on
opening a browser (headless/cloud deployments have none). The one-time
interactive authorization is a separate step — see
weconnect_mcp.cli.tibber_login_cli — that produces the token file this
client then loads non-interactively.

SECURITY: This module never logs client secrets or tokens, and persists
tokens only to a local JSON file with 0600 permissions.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Constants (see ../../../ARCHITECTURE.md §2-3) ────────────────────────────
AUTH_URI = "https://thewall.tibber.com/connect/authorize"
TOKEN_URI = "https://thewall.tibber.com/connect/token"
API_BASE = "https://data-api.tibber.com/v1"

# Minimal scope set to read vehicles.
DEFAULT_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",  # required to receive a refresh token
    "data-api-user-read",
    "data-api-homes-read",
    "data-api-vehicles-read",
]

USER_AGENT = "weconnect-mcp/0.1.0 (github.com/weconnect_mvp)"

# Refresh the access token this many seconds before it actually expires.
_REFRESH_SKEW = 60


class TibberAuthError(RuntimeError):
    """Raised when the client needs authorization it isn't allowed to obtain."""


# ── Token storage ─────────────────────────────────────────────────────────────
@dataclass
class TokenSet:
    """OAuth2 tokens plus a computed absolute expiry (epoch seconds)."""

    access_token: str
    refresh_token: str | None
    expires_at: float
    token_type: str = "Bearer"
    scope: str = ""

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "TokenSet":
        expires_in = float(data.get("expires_in", 3600))
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=time.time() + expires_in,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", ""),
        )

    @property
    def expired(self) -> bool:
        return time.time() >= (self.expires_at - _REFRESH_SKEW)

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
            "scope": self.scope,
        }


class TokenStore:
    """Persists a TokenSet to a local JSON file, written 0600."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> TokenSet | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text())
        return TokenSet(**data)

    def save(self, tokens: TokenSet) -> None:
        self.path.write_text(json.dumps(tokens.to_dict(), indent=2))
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass  # best effort (e.g. on filesystems without POSIX perms)

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)


# ── PKCE helpers ──────────────────────────────────────────────────────────────
def _pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# ── Loopback redirect catcher (interactive login only) ────────────────────────
class _CallbackHandler(BaseHTTPRequestHandler):
    """One-shot handler that captures the ?code=&state= redirect."""

    result: dict[str, str] = {}

    def do_GET(self):  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        _CallbackHandler.result = {k: v[0] for k, v in params.items()}

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if "code" in params:
            body = "<h2>Tibber login complete.</h2><p>You can close this tab.</p>"
        else:
            body = "<h2>Login failed.</h2><p>No authorization code received.</p>"
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, *args):  # silence default stderr logging
        pass


def _wait_for_redirect(host: str, port: int, timeout: float = 300.0) -> dict[str, str]:
    """Serve exactly one request on host:port and return its query params."""
    _CallbackHandler.result = {}
    server = HTTPServer((host, port), _CallbackHandler)
    server.timeout = timeout

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout)
    server.server_close()
    return _CallbackHandler.result


# ── The client ────────────────────────────────────────────────────────────────
@dataclass
class TibberDataAPI:
    """OAuth2 login + read-only Tibber Data API access.

    Set ``allow_interactive_login=False`` (the default) to guarantee this
    client never opens a browser or blocks on user input — appropriate for
    any code running inside the MCP server process. Use
    ``allow_interactive_login=True`` only in the standalone one-time setup
    tool (weconnect_mcp.cli.tibber_login_cli).
    """

    client_id: str
    client_secret: str | None
    redirect_uri: str
    store: TokenStore
    scopes: list[str] = field(default_factory=lambda: list(DEFAULT_SCOPES))
    allow_interactive_login: bool = False
    tokens: TokenSet | None = None

    def __post_init__(self):
        self.tokens = self.store.load()

    # ---- authorization ------------------------------------------------------
    def ensure_authorized(self) -> None:
        """Guarantee a valid access token.

        If no tokens are cached and interactive login is disallowed, raises
        TibberAuthError with a clear remediation message instead of opening
        a browser — the MCP server must never block startup on that.
        """
        if self.tokens is None:
            if not self.allow_interactive_login:
                raise TibberAuthError(
                    "No cached Tibber tokens found at "
                    f"{self.store.path}, and interactive login is disabled "
                    "in this context. Run the one-time setup tool first: "
                    "python -m weconnect_mcp.cli.tibber_login_cli "
                    "(see README for required env vars)."
                )
            self.tokens = self._interactive_login()
            self.store.save(self.tokens)
        elif self.tokens.expired:
            self._refresh()

    def _interactive_login(self) -> TokenSet:
        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(24)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{AUTH_URI}?{urlencode(params)}"

        parsed = urlparse(self.redirect_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        print("\nOpen this URL in your browser to authorize (also attempted "
              "automatically):\n")
        print(f"  {auth_url}\n")
        print(f"Waiting for the redirect to {self.redirect_uri} ...")
        webbrowser.open(auth_url)

        result = _wait_for_redirect(host, port)
        if "error" in result:
            raise TibberAuthError(
                f"Authorization failed: {result.get('error')} "
                f"{result.get('error_description', '')}".strip()
            )
        if result.get("state") != state:
            raise TibberAuthError("State mismatch — possible CSRF, aborting.")
        code = result.get("code")
        if not code:
            raise TibberAuthError("No authorization code in redirect.")

        return self._exchange_code(code, verifier)

    def _exchange_code(self, code: str, verifier: str) -> TokenSet:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": verifier,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        return self._token_request(data)

    def _refresh(self) -> None:
        assert self.tokens is not None
        if not self.tokens.refresh_token:
            if not self.allow_interactive_login:
                raise TibberAuthError(
                    "Cached Tibber token has no refresh_token and "
                    "interactive login is disabled in this context. Re-run "
                    "the one-time setup tool: python -m "
                    "weconnect_mcp.cli.tibber_login_cli"
                )
            self.tokens = self._interactive_login()
            self.store.save(self.tokens)
            return
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens.refresh_token,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        self.tokens = self._token_request(data)
        self.store.save(self.tokens)
        logger.info("Refreshed Tibber access token")

    def _token_request(self, data: dict[str, str]) -> TokenSet:
        resp = httpx.post(
            TOKEN_URI,
            data=data,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30.0,
        )
        if resp.status_code != 200:
            # Never echo the request body (contains secrets); response only.
            raise TibberAuthError(
                f"Token endpoint returned {resp.status_code}: {resp.text}"
            )
        return TokenSet.from_response(resp.json())

    # ---- REST calls ---------------------------------------------------------
    def _get(self, path: str) -> dict[str, Any]:
        self.ensure_authorized()
        assert self.tokens is not None
        resp = httpx.get(
            f"{API_BASE}{path}",
            headers={
                "Authorization": f"Bearer {self.tokens.access_token}",
                "User-Agent": USER_AGENT,
            },
            timeout=30.0,
        )
        if resp.status_code == 401:
            self._refresh()
            resp = httpx.get(
                f"{API_BASE}{path}",
                headers={
                    "Authorization": f"Bearer {self.tokens.access_token}",
                    "User-Agent": USER_AGENT,
                },
                timeout=30.0,
            )
        resp.raise_for_status()
        return resp.json()

    def homes(self) -> list[dict[str, Any]]:
        """GET /homes — the customer's homes."""
        return self._get("/homes").get("homes", [])

    def devices(self, home_id: str) -> list[dict[str, Any]]:
        """GET /homes/{homeId}/devices — devices in a home."""
        return self._get(f"/homes/{home_id}/devices").get("devices", [])

    def device(self, home_id: str, device_id: str) -> dict[str, Any]:
        """GET /homes/{homeId}/devices/{deviceId} — full device state."""
        return self._get(f"/homes/{home_id}/devices/{device_id}")

    def vehicles(self) -> list[dict[str, Any]]:
        """Vehicles across all homes, de-duplicated by device id.

        With only the vehicles scope granted, the devices endpoint returns
        vehicles only, so no extra filtering is strictly required.
        """
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for home in self.homes():
            for dev in self.devices(home["id"]):
                dev_id = dev.get("id")
                if dev_id and dev_id not in seen:
                    seen.add(dev_id)
                    dev = dict(dev, homeId=home["id"])
                    out.append(dev)
        return out


def vin_from_external_id(external_id: str) -> str:
    """Extract the VIN from a device's externalId.

    ARCHITECTURE.md §3.1: evcc's own source assumes ``vendor:VIN`` (e.g.
    ``tesla:5YJSA1E26MF1234567``), but our VW/Enode-backed vehicle reported
    the bare VIN with no prefix at all. Try splitting on ':' and fall back
    to the whole string if there's no match, same as evcc's own Device.VIN().
    """
    _, _, vin = external_id.rpartition(":")
    return vin or external_id
