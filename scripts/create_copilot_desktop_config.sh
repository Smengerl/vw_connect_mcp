#!/usr/bin/env bash
# Script to generate a valid mcp.json for Microsoft Copilot Desktop
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

set -euo pipefail

echo "🔧 Generating Copilot Desktop MCP configuration..."
echo ""

# Detect project directory (script is inside scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and OS
detect_python || exit 1
get_copilot_config_path

echo "Project directory: $PROJECT_DIR"
echo "OS: $OS_TYPE"
echo ""

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize venv (activates automatically)
init_venv_or_exit "$PROJECT_DIR/.venv"
PYTHON_PATH="$VENV_PYTHON"
echo "Using virtual environment: $PYTHON_PATH"

echo ""

# Default backend is Tibber (read-only, works today -- VW-direct is
# currently blocked, see the warning in README.md). Credentials live in a
# gitignored JSON file rather than environment variables, because Copilot
# Desktop launches the server with its own environment, not your shell's --
# env vars set via `export` never reach it.
TIBBER_CONFIG="$PROJECT_DIR/src/tibber_config.json"
if [ ! -f "$TIBBER_CONFIG" ]; then
  echo "⚠️  $TIBBER_CONFIG not found."
  echo "   Register an OAuth2 client at https://data-api.tibber.com/clients/manage/"
  echo "   (see experiment/tibber-integration/README.md for the exact scopes/redirect URI),"
  echo "   then create the file:"
  echo "     cp src/tibber_config.example.json src/tibber_config.json"
  echo "     # edit src/tibber_config.json with your client_id/client_secret"
  echo "   and run the one-time interactive login:"
  echo "     $PYTHON_PATH -m weconnect_mcp.cli.tibber_login_cli"
  echo ""
  echo "   Continuing to generate the config anyway -- the server will fail to"
  echo "   start until src/tibber_config.json exists (or TIBBER_CLIENT_ID/"
  echo "   TIBBER_CLIENT_SECRET are set some other way)."
  echo ""
fi

# Create tmp directory if it doesn't exist
mkdir -p "$PROJECT_DIR/tmp/copilot_desktop"

# Save configuration to tmp file
CONFIG_FILE="$PROJECT_DIR/tmp/copilot_desktop/mcp.json"
cat << EOF > "$CONFIG_FILE"
{
  "servers": {
    "weconnect": {
      "command": "$PYTHON_PATH",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "$TIBBER_CONFIG",
        "--backend",
        "tibber"
      ],
      "cwd": "$PROJECT_DIR"
    }
  }
}
EOF

echo ""
echo "✅ Configuration saved to:"
echo "   $CONFIG_FILE"
echo ""
echo "📋 Copy the configuration to Microsoft Copilot Desktop:"
echo "   $COPILOT_CONFIG"
echo ""
echo "You can either:"
echo "1. Copy from the file above (using File Explorer)"
echo "   Source: $CONFIG_FILE"
echo "   Destination: $COPILOT_CONFIG"
echo ""
echo "2. Or manually copy the JSON output from $CONFIG_FILE"
echo ""
echo "After editing, restart Microsoft Copilot Desktop completely!"
echo ""
echo "ℹ️  To use the VW-direct backend instead (currently blocked by VW, see"
echo "   README.md warning): edit the generated config, replace"
echo "   \"$TIBBER_CONFIG\" with \"$PROJECT_DIR/src/config.json\" and"
echo "   \"tibber\" with \"carconnectivity\"."
