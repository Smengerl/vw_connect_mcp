#!/usr/bin/env bash
# Start the weconnect_mvp MCP-like HTTP server in foreground and write logs and pid.
# Usage: ./start_server_fg.sh [config.json] [port]
# Defaults: config.json -> src/config.json, port -> 8765

set -euo pipefail
CONFIG=${1:-src/config.json}
LOG_DIR=${LOG_DIR:-logs}
PID_FILE=${PID_FILE:-${LOG_DIR}/server.pid}
LOG_FILE=${LOG_FILE:-${LOG_DIR}/server.log}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${LOG_DIR}"

echo "Starting server (foreground) with config=${CONFIG}"
source "${SCRIPT_DIR}/.venv/bin/activate"
python3 "${SCRIPT_DIR}/src/weconnect_mcp/cli/mcp_server_cli.py" "${CONFIG}" --tokenstorefile /tmp/tokenstore

