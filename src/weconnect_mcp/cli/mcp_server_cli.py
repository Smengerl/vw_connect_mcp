"""CLI shim to start the MCP server against the Tibber Data API.

See ARCHITECTURE.md for background. Credentials
can come from a JSON file (pass it as the 'config' positional argument --
see src/tibber_config.example.json) and/or these environment variables,
which override the file when both are present:
  TIBBER_CLIENT_ID       Required (file or env).
  TIBBER_CLIENT_SECRET   Required (file or env).
  TIBBER_REDIRECT_URI    Optional, default http://localhost:8515/callback.
  TIBBER_TOKEN_PATH      Optional, default is an OS-standard per-user data
                         directory (see tibber_client.default_token_path) --
                         NOT the current working directory, precisely so
                         that multiple local MCP clients (Claude Desktop,
                         VS Code Copilot, Claude Code, ...) converge on the
                         same token file without any of them needing this
                         set explicitly. Set it yourself only to opt out
                         deliberately (e.g. isolated test accounts).
  TIBBER_TOKEN_JSON      Optional, headless bootstrap only (see below).

A file is recommended for local/desktop use (Claude Desktop, VS Code
Copilot launch the server with their own environment, not your shell's, so
env-var-only config would otherwise require embedding secrets in the
generated MCP client config instead of a separate gitignored file). Env
vars remain the natural choice for Docker/Railway deployments.

Run `python -m weconnect_mcp.cli.tibber_login_cli` once, interactively,
before starting the server -- see that module's docstring. Tibber has no
client_credentials grant (confirmed live, ARCHITECTURE.md §2.3), so the
resulting refresh_token must persist across restarts one way or another.
For headless deployments, TIBBER_TOKEN_JSON bootstraps the token file from
that env var on first boot only (see _seed_tibber_token_from_env
docstring); point TIBBER_TOKEN_PATH at a persisted volume so subsequent
token refreshes (which rewrite the file, including Tibber's rotating
refresh_token) survive future restarts instead of reverting to the stale
env var.

MCP_API_KEY     Bearer token clients must send (HTTP mode only).
                If unset, the server runs WITHOUT authentication.

Note: this project previously also supported a VW-direct backend via the
third-party `carconnectivity` library, selected with a `--backend` flag.
That backend was removed after VW blocked third-party access with no fix
in sight -- its code remains available, unmaintained, on the permanent
`carconnectivity` git branch.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from typing import Optional

# CRITICAL: Suppress ALL warnings before any third-party imports
# This must be the FIRST thing we do to catch warnings from module imports
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from weconnect_mcp.cli import logging_config

DEFAULT_TRANSPORT = "stdio"
DEFAULT_PORT = 8089


def _seed_tibber_token_from_env(token_path: str) -> None:
    """Seed the Tibber token file from TIBBER_TOKEN_JSON on first boot.

    Bootstrap mechanism for headless deployments (Docker/Railway), where the
    interactive login (tibber_login_cli) cannot run: run it once locally,
    then paste that run's token file contents verbatim into the
    TIBBER_TOKEN_JSON environment variable (same JSON shape TokenStore.save()
    writes -- access_token, refresh_token, expires_at, token_type, scope).

    This only ever fires once: if a file already exists at token_path, it is
    left untouched, since every subsequent refresh already rewrites it
    in-place (including Tibber's rotating refresh_token, see
    ARCHITECTURE.md §2.3) and is therefore always
    at least as current as the env var. For that rewrite to survive a
    restart, token_path should point at a persisted volume (see
    docker-compose.yml's tibber-tokens volume) -- without one, this seeds
    a fresh copy from the same (increasingly stale) env var on every
    restart, which works until the seeded refresh_token itself is rotated
    away by a run that *did* persist, or simply ages past ~30 days.

    No-op if the file already exists or the env var isn't set, so this is
    always safe to call unconditionally before constructing the adapter.
    """
    if os.path.exists(token_path):
        return
    seed = os.environ.get("TIBBER_TOKEN_JSON")
    if not seed:
        return

    try:
        json.loads(seed)  # validate before writing -- fail loudly, not silently
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"TIBBER_TOKEN_JSON is not valid JSON: {exc}") from exc

    parent = os.path.dirname(token_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(seed)
    try:
        os.chmod(token_path, 0o600)
    except OSError:
        pass  # best effort (e.g. filesystems without POSIX perms)

    logging_config.get_logger(__name__).info(
        "Seeded Tibber token file from TIBBER_TOKEN_JSON at %s", token_path
    )


def _load_tibber_file_config(config_path: Optional[str]) -> dict:
    """Load a Tibber credentials JSON file if given and present, else {}.

    Shared by _build_tibber_adapter() (server startup) and tibber_login_cli
    (the one-time interactive setup tool), so both read the exact same
    src/tibber_config.json a user sets up once.

    A missing/nonexistent path is not an error -- only malformed JSON at a
    path that does exist raises, with a clear message.
    """
    if not config_path:
        return {}
    if not os.path.exists(config_path):
        logging_config.get_logger(__name__).debug(
            "Tibber credentials file %s not found — using environment variables only",
            config_path,
        )
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse {config_path} as JSON: {exc}. Fix or remove the file."
        ) from exc


def _build_tibber_adapter(config_path: Optional[str] = None):
    """Build a TibberAdapter from a credentials file and/or environment variables.

    A JSON credentials file (same shape as src/tibber_config.example.json)
    is the base, environment variables override it. This lets local/desktop
    use (Claude Desktop, VS Code Copilot) keep secrets in a gitignored file
    — those clients launch the server with their own environment, not the
    user's shell, so env-var-only config would otherwise require embedding
    secrets in the generated MCP client config instead — while cloud/
    container deployments (Docker, Railway) keep using pure env vars, with
    no file needed.

    Raises TibberAuthError (error_type="not_configured") if required
    credentials are missing from both sources, so the failure is obvious
    in server logs at startup rather than surfacing as a confusing later
    error -- and so run_server_from_cli's existing TibberAuthError
    handling turns it into a clean UnavailableAdapter (server still starts
    and every tool call reports the real cause) instead of a bare
    RuntimeError crashing stdio mode or silently stalling http mode
    forever in "starting" state.

    Args:
        config_path: Optional path to a Tibber credentials JSON file
            (keys: client_id, client_secret, redirect_uri, token_path).
            This file is optional even when given a path — env vars alone
            are sufficient, and a missing/nonexistent path is not an error.
    """
    from weconnect_mcp.adapter.tibber_adapter import TibberAdapter
    from weconnect_mcp.adapter.tibber_client import (
        TibberAuthError, default_login_command, default_token_path, login_instruction,
    )

    login_command = default_login_command(config_path)
    file_config = _load_tibber_file_config(config_path)

    client_id = os.environ.get("TIBBER_CLIENT_ID") or file_config.get("client_id")
    client_secret = os.environ.get("TIBBER_CLIENT_SECRET") or file_config.get("client_secret")
    redirect_uri = (
        os.environ.get("TIBBER_REDIRECT_URI")
        or file_config.get("redirect_uri")
        or "http://localhost:8515/callback"
    )
    token_path = (
        os.environ.get("TIBBER_TOKEN_PATH")
        or file_config.get("token_path")
        or default_token_path()
    )

    if not client_id or not client_secret:
        missing = ", ".join(
            name for name, value in (("TIBBER_CLIENT_ID", client_id), ("TIBBER_CLIENT_SECRET", client_secret))
            if not value
        )
        config_hint = (
            f"the credentials file at {config_path}" if config_path
            else "environment variables (no credentials file was given)"
        )
        raise TibberAuthError(
            f"{missing} not set. Set them via {config_hint} -- see "
            "src/tibber_config.example.json for the file's shape. Register "
            "an OAuth2 client at https://data-api.tibber.com/clients/manage/ "
            f"first if you haven't already, then (once set) "
            f"{login_instruction(login_command)} once to complete the "
            "interactive login.",
            error_type="not_configured",
        )

    _seed_tibber_token_from_env(token_path)

    return TibberAdapter(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        login_command=login_command,
        token_path=token_path,
    )


def run_server_from_cli(config_path: Optional[str] = None, transport: str = DEFAULT_TRANSPORT, port: int = DEFAULT_PORT, log_level: int = logging_config.DEFAULT_LOG_LEVEL, log_file: Optional[str] = None, api_key: Optional[str] = None):
    from weconnect_mcp.server.mcp_server import get_server

    # Resolve API key: CLI argument > env variable > None (no auth)
    resolved_api_key = api_key or os.environ.get("MCP_API_KEY")

    # ── Logging setup ─────────────────────────────────────────────────────────
    # One call does everything: chooses the right stream (stdout for http,
    # stderr for stdio), optionally writes to a file, clamps third-party
    # library levels, and clears any handlers that third-party imports may
    # have already installed.  See logging_config for full documentation.
    logging_config.configure_logging(transport, level=log_level, log_file=log_file)

    logger = logging_config.get_logger(__name__)

    if config_path:
        logger.debug("Starting Tibber adapter (credentials file: %s, env vars override)", config_path)
    else:
        logger.debug("Starting Tibber adapter (credentials from environment variables only)")

    # ── Connect (or fall back), synchronously, for both transports ──────────────
    # Both transports connect before serving a single request -- there is no
    # more "start serving immediately, connect in a background thread" dance
    # for HTTP: Docker/Railway's health-check start-period (60s, see
    # Dockerfile/docker-compose.yml) comfortably covers the couple of seconds
    # a real Tibber connection attempt takes, so the extra machinery that
    # used to exist purely to answer /health during that window (a mutable
    # adapter proxy, a StartingAdapter stand-in, a background thread) bought
    # nothing a synchronous connect doesn't already handle just as well.
    #
    # A failed Tibber login (no cached tokens, invalid config, or a refresh
    # that was genuinely rejected -- see ARCHITECTURE.md §2.4) must not crash
    # the whole process before any MCP client ever connects. Start the
    # server anyway with a fallback adapter so every tool call reports the
    # real cause via a clean "server_unavailable" response instead of the
    # client just seeing the server fail to launch. In HTTP mode this also
    # catches completely unexpected errors (a bug, a malformed credentials
    # file) for the same reason cloud platforms need *something* answering
    # /health rather than a crash-looping container; stdio mode leaves those
    # uncaught since a human is right there to see the traceback.
    from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
    from weconnect_mcp.adapter.starting_adapter import ReconnectingAdapter, UnavailableAdapter
    from weconnect_mcp.adapter.tibber_client import TibberAuthError

    def _try_connect() -> AbstractAdapter:
        return _build_tibber_adapter(config_path)

    try:
        initial: AbstractAdapter = _try_connect()
    except TibberAuthError as exc:
        logger.error("Tibber adapter unavailable at startup (%s): %s", exc.error_type, exc)
        initial = UnavailableAdapter(str(exc), error_type=exc.error_type)
    except Exception as exc:
        if transport != "http":
            raise
        logger.error("Tibber adapter failed to connect: %s", exc, exc_info=True)
        initial = UnavailableAdapter(str(exc))

    # Wrapped in ReconnectingAdapter even on the happy path: if this adapter
    # is still healthy in 30 days when its refresh token finally does expire
    # (ARCHITECTURE.md §2.4), a human rerunning the login tool should heal it
    # on the next call too, not just the initial "never connected yet" case.
    adapter: AbstractAdapter = ReconnectingAdapter(_try_connect, initial)

    with adapter:
        server = get_server(adapter, api_key=resolved_api_key)
        try:
            if transport == "http":
                from starlette.middleware import Middleware as ASGIMiddleware
                from starlette.middleware.cors import CORSMiddleware

                cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
                cors_origins = [o.strip() for o in cors_origins if o.strip()] or ["*"]

                server.run(
                    show_banner=False, transport="http", host="0.0.0.0", port=port,
                    uvicorn_config={"log_config": logging_config.get_uvicorn_log_config()},
                    middleware=[ASGIMiddleware(CORSMiddleware,
                        allow_origins=cors_origins,
                        allow_methods=["GET", "POST", "OPTIONS"],
                        allow_headers=["Authorization", "Content-Type"],
                    )],
                )
            else:
                logger.debug("Starting MCP server")
                server.run(show_banner=False, transport="stdio")
        finally:
            logger.debug("Shutdown server")


def build_parser():
    parser = argparse.ArgumentParser(prog='weconnect-mvp-server', description='Start MCP server for vehicles (Tibber Data API backend)')
    parser.add_argument('config', nargs='?', default=None, help='Path to a Tibber credentials JSON file (see src/tibber_config.example.json). Optional -- if omitted, TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET env vars are used instead; env vars override file values when both are given.')
    default_level_name = next((name for name, val in logging_config.LEVEL_MAP.items() if val == logging_config.DEFAULT_LOG_LEVEL), str(logging_config.DEFAULT_LOG_LEVEL))
    parser.add_argument('--log-level', choices=list(logging_config.LEVEL_MAP.keys()), help=f'Log level (default: {default_level_name})')
    parser.add_argument('--log-file', help='Log file path (default: stderr only)')
    parser.add_argument('--transport', default=DEFAULT_TRANSPORT, choices=['http', 'stdio'], help=f'Transport mode (default: {DEFAULT_TRANSPORT})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'HTTP port (default: {DEFAULT_PORT})')
    parser.add_argument(
        '--api-key',
        default=None,
        help=(
            'Bearer token for HTTP authentication. '
            'Can also be set via MCP_API_KEY env variable. '
            'If neither is set, the server runs without authentication '
            '(suitable for local use only).'
        ),
    )
    return parser

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    # Convert log level string to int
    if args.log_level is None:
        log_level = logging_config.DEFAULT_LOG_LEVEL
    else:
        log_level = logging_config.LEVEL_MAP.get(args.log_level, logging_config.DEFAULT_LOG_LEVEL)

    run_server_from_cli(
        args.config,
        transport=args.transport,
        port=args.port,
        log_level=log_level,
        log_file=args.log_file,
        api_key=args.api_key,
    )

if __name__ == '__main__':
    main()
