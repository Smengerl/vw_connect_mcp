#!/usr/bin/env bash
# test_mcp_auth.sh – Führt den vollständigen MCP OAuth-Flow durch und ruft tools/list auf
#
# Usage:
#   ./scripts/test_mcp_auth.sh [http://localhost:8089]

set -euo pipefail

HOST="${1:-http://localhost:8089}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
VENV_DIR="$ROOT_DIR/.venv"

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$SCRIPT_DIR/lib/init_venv.sh"

# Initialize and activate venv
init_venv_or_exit "$VENV_DIR"

# .env lesen
if [[ ! -f "$ENV_FILE" ]]; then echo "❌ .env nicht gefunden"; exit 1; fi
MCP_API_KEY=$(grep -E '^MCP_API_KEY=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '\r')
echo "🔑 Key: ${MCP_API_KEY:0:10}...  🌐 Host: $HOST"

# Schritt 1: Health
echo -e "\n━━━ Health ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -sf "$HOST/health" | "$VENV_PYTHON" -m json.tool

# Schritt 2: OAuth Discovery
echo -e "\n━━━ OAuth Discovery ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DISCOVERY=$(curl -sf "$HOST/.well-known/oauth-authorization-server")
echo "$DISCOVERY" | "$VENV_PYTHON" -m json.tool
TOKEN_ENDPOINT=$(echo "$DISCOVERY" | "$VENV_PYTHON" -c "import sys,json; print(json.load(sys.stdin)['token_endpoint'])")
REGISTRATION_ENDPOINT=$(echo "$DISCOVERY" | "$VENV_PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('registration_endpoint','$HOST/register'))")

# Schritt 3: Client registrieren
echo -e "\n━━━ Client Registration ━━━━━━━━━━━━━━━━━━━━━━━"
REG=$(curl -sf -X POST "$REGISTRATION_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"client_name":"mcp-test","grant_types":["client_credentials"],"token_endpoint_auth_method":"client_secret_post"}')
echo "$REG" | "$VENV_PYTHON" -m json.tool
CLIENT_ID=$(echo "$REG" | "$VENV_PYTHON" -c "import sys,json; print(json.load(sys.stdin)['client_id'])")
CLIENT_SECRET=$(echo "$REG" | "$VENV_PYTHON" -c "import sys,json; print(json.load(sys.stdin)['client_secret'])")

# Schritt 4: Access Token holen
echo -e "\n━━━ Token Request ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOKEN_RESP=$(curl -sf -X POST "$TOKEN_ENDPOINT" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}")
echo "$TOKEN_RESP" | "$VENV_PYTHON" -m json.tool
ACCESS_TOKEN=$(echo "$TOKEN_RESP" | "$VENV_PYTHON" -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Token: ${ACCESS_TOKEN:0:20}..."

# Schritt 5: tools/list
echo -e "\n━━━ tools/list ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -sf -X POST "$HOST/mcp" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | "$VENV_PYTHON" -m json.tool