#!/bin/bash
# Script to generate a valid mcp.json for Microsoft Copilot Desktop
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

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

# Detect Python path
if [ -d "$PROJECT_DIR/.venv" ]; then
    get_venv_paths "$PROJECT_DIR/.venv"
    PYTHON_PATH="$VENV_PYTHON"
    echo "Using virtualenv Python: $PYTHON_PATH"
else
    PYTHON_PATH="$PYTHON_BIN"
    echo "Using system Python: $PYTHON_PATH"
fi

echo ""

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
        "$PROJECT_DIR/src/config.json"
      ],
      "cwd": "$PROJECT_DIR",
      "env": {
        "PYTHONPATH": "$PROJECT_DIR/src"
      }
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
