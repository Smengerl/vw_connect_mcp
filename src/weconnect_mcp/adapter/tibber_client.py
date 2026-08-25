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

Concurrent instances: Tibber rotates refresh tokens (every successful
refresh returns a new one, invalidating the old), so if more than one
instance of this server shares one token file, refreshing needs to be
coordinated or the "losing" instance burns its already-superseded
refresh_token and gets stuck failing forever. See TokenStore.locked() and
the "Token refresh" section (ARCHITECTURE.md §2.4) for the fix and its
limits (same-machine/shared-filesystem only, not multi-host).
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import logging
import os
import secrets
import sys
import threading
import time
import webbrowser
from contextlib import contextmanager
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


def default_login_command(config_path: str | None = None) -> str:
    """Build an always-runnable login command for *this exact process's*
    interpreter, optionally pointed at a credentials file.

    Deliberately uses ``sys.executable`` (the interpreter currently
    running this code) instead of a bare ``python``/``python3`` or the
    installed ``weconnect-tibber-login`` console script name -- both of
    those only work if the right venv happens to already be active and on
    PATH in whatever shell runs the command, which is *not* the shell an
    MCP client (or a human copy-pasting from a chat) starts from. Reusing
    sys.executable sidesteps that entirely: it's the literal path this
    server process was launched with (e.g.
    ``/path/to/project/.venv/bin/python``), so the same command works
    regardless of PATH or which venv (if any) is active elsewhere --
    *except* inside a container (see ``_running_in_container()``), where
    that path exists only inside the container and ``login_instruction()``
    below stops using it entirely for exactly that reason.
    """
    cmd = f"{sys.executable} -m weconnect_mcp.cli.tibber_login_cli"
    if config_path:
        cmd += f" {config_path}"
    return cmd


def _running_in_container() -> bool:
    """Best-effort detection of a Docker/Railway-style container
    deployment, where the interactive login flow cannot run at all (no
    browser) and any path this process names via ``sys.executable`` is
    only valid inside the container, never on the operator's own machine.

    ``/.dockerenv`` is the standard Docker-created marker file. Railway
    injects several ``RAILWAY_*`` environment variables into every
    deployment regardless of which one exactly, so checking the prefix is
    more robust than pinning to one variable name.
    """
    return os.path.exists("/.dockerenv") or any(k.startswith("RAILWAY_") for k in os.environ)


def login_instruction(login_command: str) -> str:
    """Human-facing instruction for completing the interactive Tibber
    login -- correct whether this process is running locally or inside a
    container, which need entirely different advice, not just different
    wording (see _running_in_container()'s docstring)."""
    if _running_in_container():
        return (
            "this looks like a container/cloud deployment (Docker or "
            "Railway) -- the interactive login cannot run here at all (no "
            "browser, and the only command this process could name would "
            "point inside this container, not at your own machine). Run "
            "`weconnect-tibber-login` (or `python3 -m "
            "weconnect_mcp.cli.tibber_login_cli`) on your own machine "
            "instead, then set TIBBER_TOKEN_JSON to bootstrap this "
            "deployment -- see README.md's Cloud Deployment section"
        )
    return (
        f"run `{login_command}` on the server host (interactive -- opens a "
        "browser, needs a human to click through Tibber's consent screen)"
    )


def _reauth_required_message(login_command: str) -> str:
    return (
        "Tibber authorization has expired and could not be refreshed "
        "automatically. This server cannot fetch vehicle data until a "
        f"human re-authorizes it: {login_instruction(login_command)}. No "
        "server restart needed -- the next call automatically retries "
        "once that's done."
    )


_INVALID_CLIENT_MESSAGE_TEMPLATE = (
    "Tibber rejected the configured OAuth2 client credentials "
    "(TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET) as invalid ({error}). This is "
    "NOT an expired-token problem -- re-running the login flow will not fix "
    "it. Check that the client still exists and the secret matches at "
    "https://data-api.tibber.com/clients/manage/, then correct the "
    "configured value(s). No server restart needed -- the next call "
    "automatically retries once that's done."
)


class TibberAuthError(RuntimeError):
    """Raised when the client needs authorization it isn't allowed to obtain.

    ``error_type`` is a short, stable, machine-readable code that lets
    callers -- ultimately the MCP tool layer, and the AI assistant on the
    other end of it -- branch on *which* auth problem this is instead of
    only having a free-text message to pattern-match. It's a constructor
    argument (see AdapterUnavailableError in abstract_adapter.py for the
    same pattern one layer up) rather than one subclass per code: nothing
    in this codebase ever dispatches on this exception's *type* -- every
    catch site catches this base class and reads ``.error_type`` off the
    instance -- so a family of near-empty subclasses used to exist purely
    to stamp a string and were collapsed away.

    Known codes: "not_configured", "invalid_client", "reauth_required",
    "network_error", and "unavailable" (the default, generic fallback for
    anything that doesn't fit a more specific category).
    """

    def __init__(self, message: str, error_type: str = "unavailable") -> None:
        super().__init__(message)
        self.error_type = error_type


class TibberTokenEndpointError(TibberAuthError):
    """Raised when Tibber's token endpoint responds with a non-200 status.

    Carries the raw status_code/body so callers can tell apart:
    - invalid_client / unauthorized_client -- the client registration
      itself is rejected (see is_invalid_client)
    - invalid_grant -- the refresh_token/authorization code is dead, but
      the client registration is fine (see is_invalid_grant)
    - anything else (5xx, rate limiting, ...) -- transient, worth leaving
      the stored token alone for and simply retrying later
    """

    _INVALID_CLIENT_ERRORS = {"invalid_client", "unauthorized_client"}
    _INVALID_GRANT_ERRORS = {"invalid_grant"}

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Token endpoint returned {status_code}: {body}")

    def _error_code(self) -> str | None:
        if self.status_code != 400:
            return None
        try:
            return json.loads(self.body).get("error")
        except (json.JSONDecodeError, AttributeError):
            return None

    @property
    def is_invalid_client(self) -> bool:
        """True if Tibber rejected the client_id/client_secret themselves --
        a configuration problem, not an expired token."""
        return self._error_code() in self._INVALID_CLIENT_ERRORS

    @property
    def is_invalid_grant(self) -> bool:
        """True if the refresh_token/authorization code itself is dead --
        not a transient server-side hiccup, and not a client-credential
        problem either."""
        return self._error_code() in self._INVALID_GRANT_ERRORS


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

    @contextmanager
    def locked(self):
        """Exclusive lock guarding read-modify-write access to the token
        file, so concurrent instances sharing this file don't race on
        Tibber's rotating (single-use) refresh_token -- see
        ARCHITECTURE.md §2.4.

        POSIX advisory lock (`flock`) on a sidecar `.lock` file -- only
        coordinates processes on the same machine with access to this same
        file, not multiple hosts. The OS releases the lock automatically if
        the holding process dies, so there's no stale-lock cleanup needed.
        """
        lock_path = self.path.with_name(self.path.name + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


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
    login_command: str = field(default_factory=default_login_command)
    """Exact, always-runnable command that performs the one-time
    interactive login -- baked into every auth-error message below instead
    of a generic/PATH-dependent hint, and set by the caller that knows the
    real credentials-file path (see mcp_server_cli._build_tibber_adapter)
    so the message a human (or an AI assistant with shell access) sees is
    copy-paste-correct for this exact deployment."""

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
                    f"{self.store.path}. The one-time interactive login has "
                    f"never been completed on this host: {login_instruction(self.login_command)}. "
                    "(TIBBER_CLIENT_ID/SECRET are set -- this is not a "
                    "configuration problem, just a missing one-time login "
                    "step.) No server restart needed -- the next call "
                    "automatically retries once that's done.",
                    error_type="reauth_required",
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
        """Refresh the access token, coordinating with any other instance
        sharing this token file (see TokenStore.locked() and
        ARCHITECTURE.md §2.4).

        Holds the lock for the whole read-check-refresh-write sequence, and
        always re-reads from disk once it's held -- another instance may
        have already refreshed (or already discovered the refresh_token is
        dead) while we were waiting, and its result is authoritative over
        whatever we loaded at construction or on a previous refresh.
        """
        assert self.tokens is not None
        with self.store.locked():
            current = self.store.load()

            if current is None:
                # Another instance already confirmed the refresh_token is
                # dead and cleared it -- that verdict still holds, no need
                # to spend another call on Tibber's token endpoint.
                self.tokens = None
                raise TibberAuthError(
                    _reauth_required_message(self.login_command),
                    error_type="reauth_required",
                )

            if not current.expired:
                # Another instance already refreshed while we waited for
                # the lock -- adopt its result instead of refreshing again
                # (and instead of burning our own now-superseded copy).
                self.tokens = current
                return

            if not current.refresh_token:
                if not self.allow_interactive_login:
                    raise TibberAuthError(
                        "Cached Tibber token has no refresh_token and "
                        "interactive login is disabled in this context. "
                        f"Re-run the one-time setup tool: "
                        f"{login_instruction(self.login_command)}. No "
                        "server restart needed -- the next call "
                        "automatically retries once that's done.",
                        error_type="reauth_required",
                    )
                self.tokens = self._interactive_login()
                self.store.save(self.tokens)
                return

            data = {
                "grant_type": "refresh_token",
                "refresh_token": current.refresh_token,
                "client_id": self.client_id,
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret
            try:
                self.tokens = self._token_request(data)
            except TibberTokenEndpointError as exc:
                if exc.is_invalid_client:
                    # The client_id/secret themselves are rejected -- the
                    # refresh_token may well still be fine, so leave the
                    # token file alone (nothing to gain from clearing it;
                    # re-authorizing won't fix a bad client registration).
                    logger.error(
                        "Tibber rejected the client credentials (%s) -- "
                        "not a token problem, check TIBBER_CLIENT_ID/SECRET",
                        exc,
                    )
                    raise TibberAuthError(
                        _INVALID_CLIENT_MESSAGE_TEMPLATE.format(error=exc),
                        error_type="invalid_client",
                    ) from exc
                if exc.status_code != 400:
                    raise  # genuinely transient (5xx, rate limit, ...) -- leave the store alone, retry later
                # Any 400 response is a client-side rejection by definition
                # (OAuth2/HTTP semantics) -- never something a blind retry
                # fixes, even when the specific `error` code isn't one of
                # the two we recognize by name (is_invalid_grant is False
                # for it). Treat it the same as a confirmed invalid_grant
                # rather than silently bucketing an unrecognized code as
                # "transient, just wait" -- clear the store and require
                # reauth, which is the closest broadly-correct remediation
                # even when the exact cause isn't one we've seen before.
                self.store.clear()
                self.tokens = None
                logger.error(
                    "Tibber rejected the refresh token (%s) -- cleared the "
                    "stale token file, interactive re-authorization required",
                    exc,
                )
                raise TibberAuthError(
                    _reauth_required_message(self.login_command),
                    error_type="reauth_required",
                ) from exc
            self.store.save(self.tokens)
            logger.info("Refreshed Tibber access token")

    def _token_request(self, data: dict[str, str]) -> TokenSet:
        try:
            resp = httpx.post(
                TOKEN_URI,
                data=data,
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise TibberAuthError(
                f"Could not reach Tibber's token endpoint ({TOKEN_URI}): "
                f"{exc}. This looks like a connectivity problem (DNS, "
                "network, or timeout), not a credentials problem -- retry "
                "once connectivity is restored.",
                error_type="network_error",
            ) from exc
        if resp.status_code != 200:
            # Never echo the request body (contains secrets); response only.
            raise TibberTokenEndpointError(resp.status_code, resp.text)
        return TokenSet.from_response(resp.json())

    # ---- REST calls ---------------------------------------------------------
    def _get(self, path: str) -> dict[str, Any]:
        """GET one Tibber Data API path, retrying once after a 401 refresh.

        Wraps the whole request (both attempts, plus the final status
        check) in the same httpx.HTTPError -> network_error translation
        _token_request() already had -- without this, a DNS blip, timeout,
        or unexpected 5xx here would crash the calling tool call with a raw
        exception instead of the clean server_unavailable JSON this
        project's whole error-differentiation design is built to produce
        (and would never trigger ReconnectingAdapter's retry either, since
        it isn't classified as an AdapterUnavailableError). Errors raised
        by self._refresh() below are TibberAuthError already -- not an
        httpx.HTTPError -- so they pass through this untouched.
        """
        self.ensure_authorized()
        assert self.tokens is not None
        try:
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
        except httpx.HTTPError as exc:
            raise TibberAuthError(
                f"Could not fetch data from Tibber's API ({API_BASE}{path}): "
                f"{exc}. This looks like a connectivity problem (DNS, "
                "network, timeout, or an unexpected server error), not a "
                "credentials problem -- retry once connectivity is "
                "restored.",
                error_type="network_error",
            ) from exc
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
