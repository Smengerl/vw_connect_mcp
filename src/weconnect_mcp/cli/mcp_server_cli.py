"""CLI shim to start MCP server with a vehicle-data adapter.

Two backends are available (--backend flag):

  carconnectivity (default)  VW-direct via the carconnectivity library.
      Environment variables (override config.json for cloud/container
      deployments):
        VW_USERNAME     VW account e-mail
        VW_PASSWORD     VW account password
        VW_SPIN         4-digit S-PIN

  tibber                     Read-only, via the Tibber Data API. See
      experiment/tibber-integration/TIBBER_API.md for background — no
      config.json needed, only these environment variables:
        TIBBER_CLIENT_ID       Required. OAuth2 client id.
        TIBBER_CLIENT_SECRET   Required. OAuth2 client secret.
        TIBBER_REDIRECT_URI    Optional, default http://localhost:8515/callback.
        TIBBER_TOKEN_PATH      Optional, default ./tibber_tokens.json.
      Run `python -m weconnect_mcp.cli.tibber_login_cli` once, interactively,
      before starting the server with this backend — see that module's
      docstring.

  MCP_API_KEY     Bearer token clients must send (HTTP mode only).
                  If unset, the server runs WITHOUT authentication.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import warnings
from typing import Optional

# CRITICAL: Suppress ALL warnings before any third-party imports
# This must be the FIRST thing we do to catch warnings from module imports
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

from weconnect_mcp.cli import logging_config

DEFAULT_TRANSPORT = "stdio"
DEFAULT_PORT = 8089


def _maybe_patch_config_from_env(config_path: str) -> str:
    """Overlay VW credentials from environment variables onto config.json.

    If any of VW_USERNAME, VW_PASSWORD, or VW_SPIN are set, the config is
    written to a temporary file with those values replaced so that the
    carconnectivity adapter picks them up without touching the source file.

    This enables cloud/container deployments where credentials are injected
    as environment variables (Docker secrets, Railway env, Fly.io secrets, …)
    instead of being baked into a config file.

    Args:
        config_path: Path to the original config.json.

    Returns:
        Path to use – either the original path (nothing changed) or a temp
        file path (env overrides applied).
    """
    username = os.environ.get("VW_USERNAME")
    password = os.environ.get("VW_PASSWORD")
    spin = os.environ.get("VW_SPIN")

    if not any([username, password, spin]):
        return config_path  # Nothing to override

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    connectors = (
        config.get("carConnectivity", {}).get("connectors", [])
    )
    for connector in connectors:
        cfg = connector.get("config", {})
        if username:
            cfg["username"] = username
        if password:
            cfg["password"] = password
        if spin:
            cfg["spin"] = spin

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(config, tmp, indent=2)
    tmp.close()
    return tmp.name


def _build_tibber_adapter():
    """Build a TibberAdapter from environment variables.

    Raises RuntimeError with a clear message if required env vars are
    missing, so the failure is obvious in server logs at startup rather
    than surfacing as a confusing later error.
    """
    from weconnect_mcp.adapter.tibber_adapter import TibberAdapter

    client_id = os.environ.get("TIBBER_CLIENT_ID")
    client_secret = os.environ.get("TIBBER_CLIENT_SECRET")
    redirect_uri = os.environ.get("TIBBER_REDIRECT_URI", "http://localhost:8515/callback")
    token_path = os.environ.get("TIBBER_TOKEN_PATH", "./tibber_tokens.json")

    if not client_id or not client_secret:
        raise RuntimeError(
            "TIBBER_CLIENT_ID and TIBBER_CLIENT_SECRET must be set to use "
            "--backend tibber. Register an OAuth2 client at "
            "https://data-api.tibber.com/clients/manage/ first."
        )

    return TibberAdapter(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        token_path=token_path,
    )


def run_server_from_cli(config_path: Optional[str] = None, tokenstore_file: Optional[str] = None, transport: str = DEFAULT_TRANSPORT, port: int = DEFAULT_PORT, log_level: int = logging_config.DEFAULT_LOG_LEVEL, log_file: Optional[str] = None, api_key: Optional[str] = None, backend: str = "carconnectivity"):
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

    if backend == "carconnectivity":
        if not config_path:
            raise RuntimeError("A config file path is required for --backend carconnectivity.")
        from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter

        # Apply env-variable credential overrides (for cloud/container deployments)
        effective_config_path = _maybe_patch_config_from_env(config_path)
        if effective_config_path != config_path:
            logger.info("VW credentials overridden from environment variables")

        logger.debug("Starting adapter with config: %s", effective_config_path)
    elif backend == "tibber":
        effective_config_path = None
        logger.debug("Starting Tibber adapter (config file not used for this backend)")
    else:
        raise RuntimeError(f"Unknown backend: {backend!r} (expected 'carconnectivity' or 'tibber')")

    if transport == "http":
        # ── HTTP / cloud mode ─────────────────────────────────────────────────
        # Start the HTTP server FIRST so cloud health-checks pass immediately,
        # then connect the VW adapter in the background thread.
        # The server is built around a mutable proxy so all tool closures
        # transparently use the real adapter once VW login completes.
        import threading
        from weconnect_mcp.adapter.abstract_adapter import AbstractAdapter
        from weconnect_mcp.adapter.starting_adapter import StartingAdapter

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
            def get_physical_status(self, v): return self._delegate.get_physical_status(v)  # type: ignore[override]
            def get_climate_status(self, v): return self._delegate.get_climate_status(v)  # type: ignore[override]
            def get_energy_status(self, v): return self._delegate.get_energy_status(v)  # type: ignore[override]
            def get_position(self, v): return self._delegate.get_position(v)  # type: ignore[override]
            def get_maintenance_info(self, v): return self._delegate.get_maintenance_info(v)  # type: ignore[override]
            def shutdown(self): return self._delegate.shutdown()  # type: ignore[override]
            def lock_vehicle(self, v): return self._delegate.lock_vehicle(v)  # type: ignore[override]
            def unlock_vehicle(self, v): return self._delegate.unlock_vehicle(v)  # type: ignore[override]
            def start_climatization(self, v, t=None): return self._delegate.start_climatization(v, t)  # type: ignore[override]
            def stop_climatization(self, v): return self._delegate.stop_climatization(v)  # type: ignore[override]
            def start_charging(self, v): return self._delegate.start_charging(v)  # type: ignore[override]
            def stop_charging(self, v): return self._delegate.stop_charging(v)  # type: ignore[override]
            def start_window_heating(self, v): return self._delegate.start_window_heating(v)  # type: ignore[override]
            def stop_window_heating(self, v): return self._delegate.stop_window_heating(v)  # type: ignore[override]
            def flash_lights(self, v, d=None): return self._delegate.flash_lights(v, d)  # type: ignore[override]
            def honk_and_flash(self, v, d=None): return self._delegate.honk_and_flash(v, d)  # type: ignore[override]

        proxy = _AdapterProxy(StartingAdapter())
        real_adapter: list[AbstractAdapter] = []

        server = get_server(proxy, api_key=resolved_api_key)

        def _connect_backend() -> None:
            try:
                if backend == "carconnectivity":
                    adapter = CarConnectivityAdapter(
                        config_path=effective_config_path,
                        tokenstore_file=tokenstore_file,
                    )
                    # Re-apply after CarConnectivity.__init__() may have reset
                    # levels by reading log_level from its own config file.
                    logging_config.apply_third_party_levels(log_level)
                else:
                    adapter = _build_tibber_adapter()
                adapter.__enter__()
                real_adapter.append(adapter)
                proxy._swap(adapter)
                logger.info("%s adapter connected – server fully ready", backend)
            except Exception as exc:
                logger.error("%s adapter failed to connect: %s", backend, exc)

        threading.Thread(target=_connect_backend, daemon=True, name=f"{backend}-connect").start()

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
        if backend == "carconnectivity":
            adapter_cm = CarConnectivityAdapter(config_path=effective_config_path, tokenstore_file=tokenstore_file)
        else:
            adapter_cm = _build_tibber_adapter()
        with adapter_cm as adapter:
            logger.debug("Starting MCP server")
            server = get_server(adapter, api_key=resolved_api_key)
            try:
                server.run(show_banner=False, transport="stdio")
            finally:
                logger.debug("Shutdown server")


def build_parser():
    parser = argparse.ArgumentParser(prog='weconnect-mvp-server', description='Start MCP server for vehicles')
    parser.add_argument('config', nargs='?', default=None, help='Path to configuration file (required for --backend carconnectivity, unused for --backend tibber)')
    parser.add_argument('--backend', default='carconnectivity', choices=['carconnectivity', 'tibber'], help="Vehicle data backend (default: carconnectivity). 'tibber' reads via the Tibber Data API instead of VW-direct -- see TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET/TIBBER_REDIRECT_URI/TIBBER_TOKEN_PATH env vars and weconnect_mcp.cli.tibber_login_cli.")
    default_temp = os.path.join(tempfile.gettempdir(), 'tokenstore')
    parser.add_argument('--tokenstorefile', default=default_temp, help=f'Token storage path (default: {default_temp})')
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
        tokenstore_file=args.tokenstorefile,
        transport=args.transport,
        port=args.port,
        log_level=log_level,
        log_file=args.log_file,
        api_key=args.api_key,
        backend=args.backend,
    )

if __name__ == '__main__':
    main()



