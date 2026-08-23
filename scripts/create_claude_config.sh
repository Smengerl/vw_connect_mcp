#!/usr/bin/env bash
# Script to help find the correct Python path for Claude Desktop config
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

set -euo pipefail

echo "🔍 Finding Python paths for Claude Desktop configuration..."
echo ""

# Auto-detect project directory (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and OS
detect_python || exit 1
get_claude_config_path

echo "Project directory: $PROJECT_DIR"
echo "OS: $OS_TYPE"
echo ""

# Source venv init helper
# shellcheck source=./lib/init_venv.sh
source "$(dirname "$0")/lib/init_venv.sh"

# Initialize venv (activates automatically)
init_venv_or_exit "$PROJECT_DIR/.venv"
PYTHON_PATH="$VENV_PYTHON"
echo ""
echo "Python executable in venv:"
echo "   $PYTHON_PATH"
echo ""
echo "Use this path in your Claude Desktop config:"
echo "   \"command\": \"$PYTHON_PATH\""
echo ""

# Credentials live in a gitignored JSON file rather than environment
# variables, because Claude Desktop launches the server with its own
# environment, not your shell's -- env vars set via `export` never reach it.
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
mkdir -p "$PROJECT_DIR/tmp/claude_desktop"

# Save configuration to tmp file
CONFIG_FILE="$PROJECT_DIR/tmp/claude_desktop/claude_desktop_config.json"
cat << EOF > "$CONFIG_FILE"
{
  "mcpServers": {
    "weconnect": {
      "command": "$PYTHON_PATH",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "$TIBBER_CONFIG"
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
echo "📋 Copy the configuration to Claude Desktop:"
echo "   $CLAUDE_CONFIG"
echo ""
echo "You can either:"
echo "1. Copy from the file above (using File Explorer)"
echo "   Source: $CONFIG_FILE"
echo "   Destination: $CLAUDE_CONFIG"
echo ""
echo "2. Or manually copy the JSON output from $CONFIG_FILE"
echo ""
echo "After editing, restart Claude Desktop completely!"
