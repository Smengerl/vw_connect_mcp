#!/usr/bin/env bash
# Start the weconnect MCP server in background
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
# Usage: ./scripts/start_server_bg.sh [config.json] [extra mcp_server_cli args...]
#   e.g. ./scripts/start_server_bg.sh src/tibber_config.json --port 8765
# Defaults: config.json -> unset (TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET env vars used instead)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
CONFIG=${1:-}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
PID_FILE=${PID_FILE:-${LOG_DIR}/server.pid}
LOG_FILE=${LOG_FILE:-${LOG_DIR}/server.log}

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize and activate venv
init_venv_or_exit "$VENV_DIR"

mkdir -p "${LOG_DIR}"

# Drop the consumed positional $1 (config path) so "$@" below only carries
# extra mcp_server_cli flags, e.g. --port 8765.
if [ "$#" -gt 0 ]; then
  shift
fi

echo "Starting server (background) with config=${CONFIG:-<none, env vars>} extra_args=$*"

if [ "$IS_WINDOWS" = true ]; then
  # On Windows, use start command with proper quoting for background execution
  echo "Note: Server runs in background. Check logs at: ${LOG_FILE}"
  # shellcheck disable=SC2086
  cmd /c "cd /d \"$ROOT_DIR\" && \"$VENV_PYTHON\" -m weconnect_mcp.cli.mcp_server_cli \"$CONFIG\" --transport=http $* > \"$LOG_FILE\" 2>&1" &
else
  # On Unix-like systems, use nohup for true background execution
  nohup "$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli "${CONFIG}" --transport=http "$@" > "${LOG_FILE}" 2>&1 &
  PID=$!
  echo "$PID" > "${PID_FILE}"
  echo "Server started with PID=${PID}, logs -> ${LOG_FILE}, pidfile -> ${PID_FILE}"
fi
