#!/bin/bash
# Script to help find the correct Python path for Claude Desktop config
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

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

if [ -d "$PROJECT_DIR/.venv" ]; then
    get_venv_paths "$PROJECT_DIR/.venv"
    echo "Virtual environment found!"
    echo ""
    
    echo "Python executable in venv:"
    echo "   $VENV_PYTHON"
    echo ""
    echo "Use this path in your Claude Desktop config:"
    echo "   \"command\": \"$VENV_PYTHON\""
    PYTHON_PATH="$VENV_PYTHON"
    echo ""
else
    echo "No virtual environment found at $PROJECT_DIR/.venv"
    echo ""
    echo "Using system Python: $PYTHON_BIN"
    PYTHON_PATH="$PYTHON_BIN"
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
