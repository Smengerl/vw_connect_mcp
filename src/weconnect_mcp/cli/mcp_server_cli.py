"""CLI shim to start the MCP server against the Tibber Data API.

See ARCHITECTURE.md for background. Credentials
can come from a JSON file (pass it as the 'config' positional argument --
see src/tibber_config.example.json) and/or these environment variables,
which override the file when both are present:
  TIBBER_CLIENT_ID       Required (file or env).
  TIBBER_CLIENT_SECRET   Required (file or env).
  TIBBER_REDIRECT_URI    Optional, default http://localhost:8515/callback.
  TIBBER_TOKEN_PATH      Optional, default ./tibber_tokens.json.
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

    Raises RuntimeError with a clear message if required credentials are
    missing from both sources, so the failure is obvious in server logs at
    startup rather than surfacing as a confusing later error.

    Args:
        config_path: Optional path to a Tibber credentials JSON file
            (keys: client_id, client_secret, redirect_uri, token_path).
            This file is optional even when given a path — env vars alone
            are sufficient, and a missing/nonexistent path is not an error.
    """
    from weconnect_mcp.adapter.tibber_adapter import TibberAdapter

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
        or "./tibber_tokens.json"
    )

    if not client_id or not client_secret:
        raise RuntimeError(
            "TIBBER_CLIENT_ID and TIBBER_CLIENT_SECRET must be set (via "
            "environment variables or a credentials file passed as the "
            "'config' argument, see src/tibber_config.example.json). "
            "Register an OAuth2 client at "
            "https://data-api.tibber.com/clients/manage/ first."
        )

    _seed_tibber_token_from_env(token_path)

    return TibberAdapter(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
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

    if transport == "http":
        # ── HTTP / cloud mode ─────────────────────────────────────────────────
        # Start the HTTP server FIRST so cloud health-checks pass immediately,
        # then connect the Tibber adapter in the background thread.
        # The server is built around a mutable proxy so all tool closures
        # transparently use the real adapter once the connection completes.
        import threading
        from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
        from weconnect_mcp.adapter.starting_adapter import StartingAdapter, UnavailableAdapter
        from weconnect_mcp.adapter.tibber_client import TibberAuthError

        class _AdapterProxy(AbstractAdapter):
            """Thin proxy that delegates to whichever adapter is current."""
            _ready = False
            def __init__(self, initial: AbstractAdapter) -> None:
                self._delegate = initial
            def _swap(self, real: AbstractAdapter) -> None:
                self._delegate = real
                self._ready = True
            def list_vehicles(self): return self._delegate.list_vehicles()  # type: ignore[override]
            def get_vehicle(self, v): return self._delegate.get_vehicle(v)  # type: ignore[override]
            def get_energy_status(self, v): return self._delegate.get_energy_status(v)  # type: ignore[override]
            def shutdown(self): return self._delegate.shutdown()  # type: ignore[override]

        proxy = _AdapterProxy(StartingAdapter())
        real_adapter: list[AbstractAdapter] = []

        server = get_server(proxy, api_key=resolved_api_key)

        def _connect_backend() -> None:
            try:
                adapter = _build_tibber_adapter(config_path)
                adapter.__enter__()
                real_adapter.append(adapter)
                proxy._swap(adapter)
                logger.info("Tibber adapter connected – server fully ready")
            except TibberAuthError as exc:
                # No cached tokens, or a refresh that was genuinely rejected
                # (ARCHITECTURE.md §2.4) -- won't resolve itself. Swap in a
                # stub that reports this clearly on every tool call instead
                # of leaving StartingAdapter's silent "still starting"
                # responses in place forever.
                logger.error("Tibber adapter unavailable: %s", exc)
                proxy._swap(UnavailableAdapter(str(exc)))
            except Exception as exc:
                logger.error("Tibber adapter failed to connect: %s", exc)

        threading.Thread(target=_connect_backend, daemon=True, name="tibber-connect").start()

        try:
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
        finally:
            logger.debug("Shutdown server")
            for a in real_adapter:
                try:
                    a.__exit__(None, None, None)
                except Exception:
                    pass

    else:
        # ── stdio mode (local) ────────────────────────────────────────────────
        # A failed Tibber login (no cached tokens, or a refresh that was
        # genuinely rejected -- see ARCHITECTURE.md §2.4) must not crash the
        # whole process before any MCP client ever connects. Start the
        # server anyway with a stub adapter so every tool call reports the
        # real cause via a clean "server_unavailable" response instead of
        # the client just seeing the server fail to launch.
        from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
        from weconnect_mcp.adapter.starting_adapter import UnavailableAdapter
        from weconnect_mcp.adapter.tibber_client import TibberAuthError

        try:
            adapter: AbstractAdapter = _build_tibber_adapter(config_path)
        except TibberAuthError as exc:
            logger.error("Tibber adapter unavailable at startup: %s", exc)
            adapter = UnavailableAdapter(str(exc))

        with adapter:
            logger.debug("Starting MCP server")
            server = get_server(adapter, api_key=resolved_api_key)
            try:
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
