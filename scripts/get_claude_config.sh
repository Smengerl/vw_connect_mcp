#!/bin/bash
# Script to help find the correct Python path for Claude Desktop config

echo "🔍 Finding Python paths for Claude Desktop configuration..."
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
    echo "Use this path in your Claude Desktop config:"
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
        echo "Use this path in your Claude Desktop config:"
        echo "   \"command\": \"$PYTHON_PATH\""
    else
        echo "No Python found!"
        exit 1
    fi
fi

echo ""
echo "Complete Claude Desktop configuration:"
echo ""
cat << EOF
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
echo "Copy the configuration above to:"
echo "   ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "To edit the file:"
echo "   open ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo ""
echo "After editing, restart Claude Desktop completely!"
