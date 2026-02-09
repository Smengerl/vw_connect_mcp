#!/bin/bash
# Script to help configure GitHub Copilot for WeConnect MCP Server

echo "🔍 Finding Python paths for GitHub Copilot configuration..."
echo ""

# Auto-detect project directory (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project directory: $PROJECT_DIR"
echo ""

if [ -d "$PROJECT_DIR/.venv" ]; then
    echo "Virtual environment found!"
    echo ""
    echo "Python executables in venv:"
    ls -l "$PROJECT_DIR/.venv/bin/python"* 2>/dev/null || echo "No python found in venv"
    echo ""
    echo "Use this path in your GitHub Copilot config:"
    echo "   \"command\": \"$PROJECT_DIR/.venv/bin/python\""
    echo ""
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
else
    echo "No virtual environment found at $PROJECT_DIR/.venv"
    echo ""
    echo "Looking for system Python..."
    PYTHON_PATH=$(which python3)
    if [ -n "$PYTHON_PATH" ]; then
        echo "Found Python 3 at: $PYTHON_PATH"
        echo ""
        echo "Use this path in your GitHub Copilot config:"
        echo "   \"command\": \"$PYTHON_PATH\""
    else
        echo "No Python found!"
        exit 1
    fi
fi


# Create tmp directory if it doesn't exist
mkdir -p "$PROJECT_DIR/tmp/github_copilot_vscode"

# Save configuration to tmp file
CONFIG_FILE="$PROJECT_DIR/tmp/github_copilot_vscode/settings.json"
cat << EOF > "$CONFIG_FILE"
{
  "github.copilot.chat.mcp": {
    "enabled": true
  },
  "github.copilot.chat.mcpServers": {
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
echo "📝 To configure GitHub Copilot in VS Code:"
echo ""
echo "1. Open VS Code Settings (JSON):"
echo "   - Press Cmd+Shift+P"
echo "   - Type 'Preferences: Open User Settings (JSON)'"
echo "   - Press Enter"
echo ""
echo "2. Add the configuration above to your settings.json"
echo "   (You can copy from $CONFIG_FILE)"
echo ""
echo "3. Restart VS Code or reload the window:"
echo "   - Press Cmd+Shift+P"
echo "   - Type 'Developer: Reload Window'"
echo "   - Press Enter"
echo ""
echo "4. Verify MCP server is running:"
echo "   - Open GitHub Copilot Chat"
echo "   - Type '@weconnect' to see if the server is available"
echo ""
echo "Alternative: Direct file edit"
echo "   code ~/Library/Application\\ Support/Code/User/settings.json"
echo ""
