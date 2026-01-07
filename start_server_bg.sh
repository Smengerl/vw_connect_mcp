#!/usr/bin/env bash
# Start the weconnect_mvp MCP-like HTTP server in background (nohup) and write logs and pid.
# Usage: ./start_server_bg.sh [config.json] [port]
# Defaults: config.json -> src/config.json, port -> 8765

set -euo pipefail
CONFIG=${1:-src/config.json}
PORT=${2:-8765}
LOG_DIR=${LOG_DIR:-logs}
PID_FILE=${PID_FILE:-${LOG_DIR}/server.pid}
LOG_FILE=${LOG_FILE:-${LOG_DIR}/server.log}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${LOG_DIR}"

echo "Starting server (background) with config=${CONFIG} on port=${PORT}"
source "${SCRIPT_DIR}/.venv/bin/activate"
nohup python3 "${SCRIPT_DIR}/src/weconnect_mcp/cli/mcp_server_cli.py" "${CONFIG}" --tokenstorefile /tmp/tokenstore --port "${PORT}" > "${LOG_FILE}" 2>&1 &
PID=$!
echo $PID > "${PID_FILE}"
echo "Server started with PID=${PID}, logs -> ${LOG_FILE}, pidfile -> ${PID_FILE}"
