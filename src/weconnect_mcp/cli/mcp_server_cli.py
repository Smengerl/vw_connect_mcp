"""Small CLI shim to start the MCP server backed by the carconnectivity adapter.

This script accepts the same arguments used by the tests (including an
optional --serve flag) and delegates the real work to
`carconnectivity_adapter.run_server_from_cli`.
"""
from __future__ import annotations

import argparse
import logging
import os
import tempfile
from typing import Optional

## Logger is now set up after parsing CLI args in main()
logger = None


# Import here so the module-level imports in the adapter don't run during test discovery
from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
from weconnect_mcp.server.mcp_server import get_server

DEFAULT_PORT = 8765

def run_server_from_cli(config_path: str, port: int = DEFAULT_PORT, tokenstore_file: Optional[str] = None):
    if logger is not None:
        logger.info("Starting CarConnectivity adapter with onfig: %s", config_path)
    adapter = CarConnectivityAdapter(config_path=config_path, tokenstore_file=tokenstore_file)  

    if logger is not None:
        logger.info("Starting CarConnectivity MCP server on port %d", port)
    server = get_server(adapter)
    try:
        server.run(port=port)
    finally:
        if logger is not None:
            logger.info("Shutdown server")
        adapter.shutdown()


def build_parser():
    parser = argparse.ArgumentParser(prog='weconnect-mvp-server', description='Start MCP server for vehicles')
    parser.add_argument('config', help='Path to configuration file')
    default_temp = os.path.join(tempfile.gettempdir(), 'tokenstore')
    parser.add_argument('--tokenstorefile', default=default_temp, help=f'path for tokenstore (default: {default_temp})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'port for HTTP server (default: {DEFAULT_PORT})')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set logging level')
    parser.add_argument('--log-file', help='Path to log file (default: stdout only)')
    return parser


def setup_logging_from_args(log_level_str: Optional[str], log_file: Optional[str]):
    import logging
    from weconnect_mcp.cli import logging_config
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    if log_level_str is None:
        log_level = logging_config.DEFAULT_LOG_LEVEL
    else:
        log_level = level_map.get(log_level_str, logging_config.DEFAULT_LOG_LEVEL)
    # Reconfigure logger
    global logger
    logger = logging_config.setup_logging(__name__, level=log_level, log_file=log_file)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup logging with CLI args
    setup_logging_from_args(args.log_level, args.log_file)

    # Run the adapter which will start the generic MCP server
    run_server_from_cli(args.config, port=args.port, tokenstore_file=args.tokenstorefile)

if __name__ == '__main__':
    main()



