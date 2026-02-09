#!/bin/bash
# Script to generate a valid mcp.json for Microsoft Copilot Desktop (macOS)
# for the WeConnect MCP Server

echo "🔧 Generating Copilot Desktop MCP configuration..."
echo ""

# Detect project directory (script is inside scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project directory: $PROJECT_DIR"
echo ""

# Detect Python
if [ -d "$PROJECT_DIR/.venv" ]; then
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
    echo "Using virtualenv Python: $PYTHON_PATH"
else
    PYTHON_PATH=$(which python3)
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
echo "   ~/Library/Application Support/Microsoft/Copilot/mcp.json"
echo ""
echo "You can either:"
echo "1. Copy from the file above:"
echo "   mkdir -p ~/Library/Application\\ Support/Microsoft/Copilot"
echo "   cp $CONFIG_FILE ~/Library/Application\\ Support/Microsoft/Copilot/mcp.json"
echo ""
echo "2. Or manually copy the JSON output above"
echo ""
echo "To edit the Copilot Desktop config file directly:"
echo "   open ~/Library/Application\\ Support/Microsoft/Copilot/mcp.json"
echo ""
echo "After editing, restart Microsoft Copilot Desktop completely!"
echo ""
