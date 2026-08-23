#!/usr/bin/env bash
# Start the weconnect MCP server in foreground
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
# Usage: ./scripts/start_server_fg.sh [config.json] [extra mcp_server_cli args...]
#   e.g. ./scripts/start_server_fg.sh src/tibber_config.json --port 8765
# Defaults: config.json -> unset (TIBBER_CLIENT_ID/TIBBER_CLIENT_SECRET env vars used instead)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
CONFIG=${1:-}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}

# Drop the consumed positional $1 (config path) so "$@" below only carries
# extra mcp_server_cli flags, e.g. --port 8765. Without this, $1 would be
# passed twice (once as "${CONFIG}", once inside "$@"), which argparse
# rejects as an unrecognized second positional argument.
if [ "$#" -gt 0 ]; then
  shift
fi

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize and activate venv
init_venv_or_exit "$VENV_DIR"

mkdir -p "${LOG_DIR}"

echo "Starting server (foreground) with config=${CONFIG:-<none, env vars>} extra_args=$*"
"$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli "${CONFIG}" --log-level DEBUG "$@"
