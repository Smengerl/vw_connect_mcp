#!/usr/bin/env bash
# Start the weconnect_mvp MCP-like HTTP server in foreground and write logs and pid.
# Usage: ./scripts/start_server_fg.sh [config.json] [port]
# Defaults: config.json -> ../src/config.json, port -> 8765

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG=${1:-$ROOT_DIR/src/config.json}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
PID_FILE=${PID_FILE:-${LOG_DIR}/server.pid}
LOG_FILE=${LOG_FILE:-${LOG_DIR}/server.log}

mkdir -p "${LOG_DIR}"

echo "Activating virtualenv"
${ROOT_DIR}/scripts/activate_venv.sh

echo "Starting server (foreground) with config=${CONFIG}"
python3 "${ROOT_DIR}/src/weconnect_mcp/cli/mcp_server_cli.py" "${CONFIG}" --tokenstorefile /tmp/tokenstore --log-level DEBUG "$@"
