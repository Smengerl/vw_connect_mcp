#!/usr/bin/env bash
# Start the MCP server in HTTP mode with API-Key authentication.
#
# Usage:
#   ./scripts/start_server_http.sh [port]                      # tibber backend (default)
#   ./scripts/start_server_http.sh [port] carconnectivity       # VW-direct (currently blocked)
#   MCP_API_KEY=secret ./scripts/start_server_http.sh 8089
#
# Port default is 8089 to avoid conflicts when multiple MCP servers run locally.
# Use 8080 only when replicating the Railway/cloud setup on a dedicated machine.
#
# Environment variables:
#   MCP_API_KEY            Bearer token clients must send (REQUIRED for secure deployment)
#   BACKEND                'tibber' (default) or 'carconnectivity'
#   TIBBER_CLIENT_ID       Required for tibber backend (or use src/tibber_config.json)
#   TIBBER_CLIENT_SECRET   Required for tibber backend (or use src/tibber_config.json)
#   VW_USERNAME             Overrides config.json username (carconnectivity backend only)
#   VW_PASSWORD             Overrides config.json password (carconnectivity backend only)
#   VW_SPIN                 Overrides config.json spin (carconnectivity backend only)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PORT=${1:-8089}
BACKEND=${2:-${BACKEND:-tibber}}
LOG_DIR=${LOG_DIR:-$ROOT_DIR/logs}
TOKENSTORE="/tmp/tokenstore"

if [ "$BACKEND" = "carconnectivity" ]; then
  CONFIG=${CONFIG:-$ROOT_DIR/src/config.json}
else
  CONFIG=${CONFIG:-$ROOT_DIR/src/tibber_config.json}
fi

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

if [ "$BACKEND" = "carconnectivity" ]; then
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
else
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
fi

if [ -z "${CORS_ORIGINS:-}" ]; then
  echo "⚠️  WARNING: CORS_ORIGINS is not set. Defaulting to '*' (all origins allowed)."
fi

echo "🚀 Starting WeConnect MCP server (HTTP, port ${PORT}, backend ${BACKEND})"
echo "   Config:    ${CONFIG}"
echo "   Port:      ${PORT}"
echo "   Auth:      $([ -n "${MCP_API_KEY:-}" ] && echo 'API-Key enabled' || echo 'NONE (unsecured!)')"
echo ""

"$VENV_PYTHON" -m weconnect_mcp.cli.mcp_server_cli \
  "${CONFIG}" \
  --backend "${BACKEND}" \
  --transport http \
  --port ${PORT} \
  --tokenstorefile "$TOKENSTORE" \
  --log-level INFO
