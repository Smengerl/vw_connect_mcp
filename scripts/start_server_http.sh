#!/usr/bin/env bash
# Start the MCP server in HTTP mode with API-Key authentication.
#
# Usage:
#   ./scripts/start_server_http.sh [port]
#   MCP_API_KEY=secret ./scripts/start_server_http.sh 8089
#
# Port default is 8089 to avoid conflicts when multiple MCP servers run locally.
# Use 8080 only when replicating the Railway/cloud setup on a dedicated machine.
#
# Environment variables:
#   MCP_API_KEY            Bearer token clients must send (REQUIRED for secure deployment)
#   TIBBER_CLIENT_ID       Required (or use src/tibber_config.json)
#   TIBBER_CLIENT_SECRET   Required (or use src/tibber_config.json)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PORT=${1:-8089}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
CONFIG=${CONFIG:-$ROOT_DIR/src/tibber_config.json}

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

if [ -z "${TIBBER_CLIENT_ID:-}" ] && [ ! -f "$CONFIG" ]; then
  echo "❌ ERROR: Neither TIBBER_CLIENT_ID nor $CONFIG exist."
  echo "   Register an OAuth2 client at https://data-api.tibber.com/clients/manage/ and either:"
  echo "     export TIBBER_CLIENT_ID=... TIBBER_CLIENT_SECRET=..."
  echo "   or:"
  echo "     cp src/tibber_config.example.json $CONFIG"
  echo "     # edit $CONFIG with your client_id/client_secret"
  echo "   Then run the one-time interactive login:"
  echo "     $VENV_PYTHON -m weconnect_mcp.cli.tibber_login_cli"
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

"$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli \
  "${CONFIG}" \
  --transport http \
  --port ${PORT} \
  --log-level INFO
