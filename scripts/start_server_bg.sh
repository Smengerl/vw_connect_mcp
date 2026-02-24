#!/usr/bin/env bash
# Start the weconnect MCP server in background
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
# Usage: ./scripts/start_server_bg.sh [config.json]
# Defaults: config.json -> ../src/config.json

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
CONFIG=${1:-$ROOT_DIR/src/config.json}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
PID_FILE=${PID_FILE:-${LOG_DIR}/server.pid}
LOG_FILE=${LOG_FILE:-${LOG_DIR}/server.log}
TOKENSTORE="/tmp/tokenstore"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and get venv paths
detect_python || exit 1
get_venv_paths "$VENV_DIR"

mkdir -p "${LOG_DIR}"

echo "Starting server (background) with config=${CONFIG}"

if [ "$IS_WINDOWS" = true ]; then
  # On Windows, use 'start' command for background execution
  echo "Note: Server runs in background. Check logs at: ${LOG_FILE}"
  cmd /c "cd \"$ROOT_DIR\" && \"$VENV_PYTHON\" src/weconnect_mcp/cli/mcp_server_cli.py \"$CONFIG\" --tokenstorefile \"$TOKENSTORE\" --transport=http > \"$LOG_FILE\" 2>&1 &"
else
  # On Unix-like systems, use nohup
  nohup "$VENV_PYTHON" "${ROOT_DIR}/src/weconnect_mcp/cli/mcp_server_cli.py" "${CONFIG}" --tokenstorefile "$TOKENSTORE" --transport=http > "${LOG_FILE}" 2>&1 &
  PID=$!
  echo $PID > "${PID_FILE}"
  echo "Server started with PID=${PID}, logs -> ${LOG_FILE}, pidfile -> ${PID_FILE}"
fi