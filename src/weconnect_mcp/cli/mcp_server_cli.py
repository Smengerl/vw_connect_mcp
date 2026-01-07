"""Small CLI shim to start the MCP server backed by the carconnectivity adapter.

This script accepts the same arguments used by the tests (including an
optional --serve flag) and delegates the real work to
`carconnectivity_adapter.run_server_from_cli`.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Optional

from weconnect_mcp.cli import logging_config



def run_server_from_cli(config_path: str, tokenstore_file: Optional[str] = None, transport: str = "http", port: int = 5000):
    from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
    from weconnect_mcp.server.mcp_server import get_server

    logger = logging_config.get_logger(__name__)

    logger.info("Starting CarConnectivity adapter with config: %s", config_path)
    adapter = CarConnectivityAdapter(config_path=config_path, tokenstore_file=tokenstore_file)  

    logger.info("Starting CarConnectivity MCP server")
    server = get_server(adapter)
    try:
        if transport == "http":
            server.run(transport="http", host="0.0.0.0", port=port)
        elif transport == "stdio":
            server.run(transport="stdio")
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    finally:
        logger.info("Shutdown server")
        adapter.shutdown()



def build_parser():
    parser = argparse.ArgumentParser(prog='weconnect-mvp-server', description='Start MCP server for vehicles')
    parser.add_argument('config', help='Path to configuration file')
    default_temp = os.path.join(tempfile.gettempdir(), 'tokenstore')
    parser.add_argument('--tokenstorefile', default=default_temp, help=f'path for tokenstore (default: {default_temp})')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set logging level')
    parser.add_argument('--log-file', help='Path to log file (default: stdout only)')
    parser.add_argument('--transport', default='http', choices=['http', 'stdio'], help='Transport mode (default: http)')
    parser.add_argument('--port', type=int, default=8667, help='Port for HTTP mode (default: 8667)')
    return parser



def setup_logging_from_args(log_level_str: Optional[str], log_file: Optional[str]):
    import logging
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
    logging_config.setup_logging(__name__, level=log_level, log_file=log_file)



def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup logging with CLI args
    setup_logging_from_args(args.log_level, args.log_file)

    # Run the adapter which will start the generic MCP server
    run_server_from_cli(
        args.config,
        tokenstore_file=args.tokenstorefile,
        transport=args.transport,
        port=args.port
    )

if __name__ == '__main__':
    main()



