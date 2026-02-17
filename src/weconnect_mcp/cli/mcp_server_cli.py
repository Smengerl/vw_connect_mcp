"""CLI shim to start MCP server with carconnectivity adapter."""
from __future__ import annotations

import argparse
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
DEFAULT_PORT = 8765




def run_server_from_cli(config_path: str, tokenstore_file: Optional[str] = None, transport: str = DEFAULT_TRANSPORT, port: int = DEFAULT_PORT, log_level: int = logging_config.DEFAULT_LOG_LEVEL, log_file: Optional[str] = None):
    import logging
    from weconnect_mcp.adapter.carconnectivity_adapter import CarConnectivityAdapter
    from weconnect_mcp.server.mcp_server import get_server

    # CRITICAL: If log_file is specified AND we're in stdio mode, redirect stderr to /dev/null
    # This is the ONLY way to keep stderr clean for MCP stdio protocol
    if log_file and transport == "stdio":
        sys.stderr = open(os.devnull, 'w')
    
    # Configure logging based on log_file and transport mode
    if log_file:
        # Create log directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger to write to file
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=log_file,
            filemode='a',
            force=True
        )
        
        # Remove stderr handlers to keep stderr clean for MCP stdio protocol
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and handler.stream in (sys.stderr, sys.__stderr__):
                root_logger.removeHandler(handler)
    else:
        # No log file - use stderr (only when transport is not stdio, or for debugging)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr,
            force=True
        )
    
    # Apply the same log level to third-party loggers (respect user's choice)
    # Only increase level (make less verbose) if user chose ERROR or higher
    third_party_level = max(log_level, logging.ERROR) if log_level < logging.ERROR else log_level
    
    logging.getLogger('carconnectivity').setLevel(third_party_level)
    logging.getLogger('carconnectivity.connectors.volkswagen-api-debug').setLevel(third_party_level)
    logging.getLogger('urllib3').setLevel(third_party_level)
    logging.getLogger('httpx').setLevel(third_party_level)
    
    logger = logging_config.get_logger(__name__)

    logger.debug("Starting adapter with config: %s", config_path)
    with CarConnectivityAdapter(config_path=config_path, tokenstore_file=tokenstore_file) as adapter:
        logger.debug("Starting MCP server")
        server = get_server(adapter)
        try:
            if transport == "http":
                server.run(show_banner=False, transport="http", host="0.0.0.0", port=port)
            elif transport == "stdio":
                server.run(show_banner=False, transport="stdio")
            else:
                raise ValueError(f"Unsupported transport: {transport}")
        finally:
            logger.debug("Shutdown server")


def build_parser():
    parser = argparse.ArgumentParser(prog='weconnect-mvp-server', description='Start MCP server for vehicles')
    parser.add_argument('config', help='Path to configuration file')
    default_temp = os.path.join(tempfile.gettempdir(), 'tokenstore')
    parser.add_argument('--tokenstorefile', default=default_temp, help=f'Token storage path (default: {default_temp})')
    default_level_name = next((name for name, val in logging_config.LEVEL_MAP.items() if val == logging_config.DEFAULT_LOG_LEVEL), str(logging_config.DEFAULT_LOG_LEVEL))
    parser.add_argument('--log-level', choices=list(logging_config.LEVEL_MAP.keys()), help=f'Log level (default: {default_level_name})')
    parser.add_argument('--log-file', help='Log file path (default: stderr only)')
    parser.add_argument('--transport', default=DEFAULT_TRANSPORT, choices=['http', 'stdio'], help=f'Transport mode (default: {DEFAULT_TRANSPORT})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'HTTP port (default: {DEFAULT_PORT})')
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
        log_file=args.log_file
    )

if __name__ == '__main__':
    main()



