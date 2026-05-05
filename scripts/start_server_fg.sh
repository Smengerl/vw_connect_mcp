#!/usr/bin/env bash
# Start the weconnect MCP server in foreground
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
# Usage: ./scripts/start_server_fg.sh [config.json] [port]
# Defaults: config.json -> ../src/config.json, port -> 8765

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
CONFIG=${1:-$ROOT_DIR/src/config.json}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
TOKENSTORE="/tmp/tokenstore"

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize and activate venv
init_venv_or_exit "$VENV_DIR"

mkdir -p "${LOG_DIR}"

echo "Starting server (foreground) with config=${CONFIG}"
PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli "${CONFIG}" --tokenstorefile "$TOKENSTORE" --log-level DEBUG "$@"
