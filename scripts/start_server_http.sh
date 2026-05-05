#!/usr/bin/env bash
# Start the MCP server in HTTP mode with API-Key authentication.
#
# Usage:
#   ./scripts/start_server_http.sh [port]          # reads MCP_API_KEY from env
#   MCP_API_KEY=secret ./scripts/start_server_http.sh 8080
#
# Environment variables (all optional if config.json is complete):
#   MCP_API_KEY   Bearer token clients must send (REQUIRED for secure deployment)
#   VW_USERNAME   Overrides config.json username
#   VW_PASSWORD   Overrides config.json password
#   VW_SPIN       Overrides config.json spin

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
CONFIG=${CONFIG:-$ROOT_DIR/src/config.json}
PORT=${1:-8080}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
TOKENSTORE="/tmp/tokenstore"

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize and activate venv
init_venv_or_exit "$VENV_DIR"

mkdir -p "${LOG_DIR}"

# Load environment variables from .env file
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

# Check if all required environment variables are set
if [ -z "${MCP_API_KEY:-}" ]; then
  echo "❌ ERROR: MCP_API_KEY is not set. This is required for secure deployment."
  echo "   Generate a key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
  exit 1
fi

if [ -z "${VW_USERNAME:-}" ]; then
  echo "❌ ERROR: VW_USERNAME is not set. This overrides the username in config.json."
  exit 1
fi

if [ -z "${VW_PASSWORD:-}" ]; then
  echo "❌ ERROR: VW_PASSWORD is not set. This overrides the password in config.json."
  exit 1
fi

if [ -z "${VW_SPIN:-}" ]; then
  echo "❌ ERROR: VW_SPIN is not set. This overrides the S-PIN in config.json."
  exit 1
fi

if [ -z "${CORS_ORIGINS:-}" ]; then
  echo "⚠️  WARNING: CORS_ORIGINS is not set. Defaulting to '*' (all origins allowed)."
fi

echo "🚀 Starting WeConnect MCP server (HTTP, port ${PORT})"
echo "   Config:    ${CONFIG}"
echo "   Port:      ${PORT}"
echo "   Auth:      $([ -n "${MCP_API_KEY:-}" ] && echo 'API-Key enabled' || echo 'NONE (unsecured!)')"
echo ""

PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli \
  "${CONFIG}" \
  --transport http \
  --port ${PORT} \
  --tokenstorefile "$TOKENSTORE" \
  --log-level INFO
