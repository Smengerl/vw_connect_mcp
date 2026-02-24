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

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and get venv paths
detect_python || exit 1
get_venv_paths "$VENV_DIR"
get_venv_activate_script "$VENV_DIR"

mkdir -p "${LOG_DIR}"

echo "Activating virtualenv"
# Source activation script if it exists
if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
fi

echo "Starting server (foreground) with config=${CONFIG}"
"$VENV_PYTHON" "${ROOT_DIR}/src/weconnect_mcp/cli/mcp_server_cli.py" "${CONFIG}" --tokenstorefile "$TOKENSTORE" --log-level DEBUG "$@"
