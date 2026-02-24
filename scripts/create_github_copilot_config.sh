#!/bin/bash
# Script to configure GitHub Copilot MCP Server for WeConnect
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)

set -e  # Exit on error

# Auto-detect project directory (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source the shared detection library
# shellcheck source=./lib/detect_python.sh
source "$(dirname "$0")/lib/detect_python.sh"

# Detect Python and OS
detect_python || exit 1
get_mcp_file_path

echo "🚀 WeConnect MCP Server Setup for VS Code"
echo "=========================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "OS: $OS_TYPE"
echo ""

# Find Python executable
if [ -d "$PROJECT_DIR/.venv" ]; then
    get_venv_paths "$PROJECT_DIR/.venv"
    PYTHON_PATH="$VENV_PYTHON"
    echo "✅ Virtual environment found: $PYTHON_PATH"
else
    PYTHON_PATH="$PYTHON_BIN"
    if [ -z "$PYTHON_PATH" ]; then
        echo "❌ Error: No Python found!"
        exit 1
    fi
    echo "⚠️  Using system Python: $PYTHON_PATH"
fi

echo ""

# Create tmp directory for backup config
mkdir -p "$PROJECT_DIR/tmp/github_copilot_vscode"
CONFIG_FILE="$PROJECT_DIR/tmp/github_copilot_vscode/mcp.json"

# Generate MCP configuration
cat << EOF > "$CONFIG_FILE"
{
  "servers": {
    "weconnect": {
      "command": "$PYTHON_PATH",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "$PROJECT_DIR/src/config.json",
        "--log-level",
        "ERROR",
        "--log-file",
        "$PROJECT_DIR/logs/mcp_server.log"
      ],
      "cwd": "$PROJECT_DIR",
      "env": {
        "PYTHONPATH": "$PROJECT_DIR/src"
      },
      "type": "stdio"
    }
  },
  "inputs": []
}
EOF

echo "📝 Configuration saved to: $CONFIG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Choose your installation method:"
echo ""
echo "  1) 🎯 AUTOMATIC (Recommended) - Auto-merge into mcp.json"
echo "  2) 🖱️  GUI - Install via VS Code Command Palette"
echo "  3) ✏️  MANUAL - Edit mcp.json file manually"
echo "  4) ℹ️  Show all methods"
echo ""
read -p "Enter your choice (1-4): " choice
echo ""

case $choice in
    1)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎯 METHOD 1: Automatic Installation"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Target file: $MCP_FILE"
        echo ""
        
        # Check if MCP file exists
        if [ ! -f "$MCP_FILE" ]; then
            echo "📁 MCP file doesn't exist. Creating new file..."
            mkdir -p "$(dirname "$MCP_FILE")"
            cp "$CONFIG_FILE" "$MCP_FILE"
            echo "✅ Created: $MCP_FILE"
        else
            echo "📁 MCP file already exists."
            echo ""
            read -p "Do you want to merge the WeConnect server config? (y/n): " confirm
            
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                # Backup existing file
                BACKUP_FILE="${MCP_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
                cp "$MCP_FILE" "$BACKUP_FILE"
                echo "💾 Backup created: $BACKUP_FILE"
                echo ""
                
                # Check if 'jq' is available for JSON merging
                if command -v jq &> /dev/null; then
                    echo "🔧 Using jq to merge configurations..."
                    
                    # Extract weconnect server config
                    WECONNECT_SERVER=$(jq '.servers.weconnect' "$CONFIG_FILE")
                    
                    # Merge into existing mcp.json
                    jq --argjson server "$WECONNECT_SERVER" '.servers.weconnect = $server' "$MCP_FILE" > "${MCP_FILE}.tmp"
                    mv "${MCP_FILE}.tmp" "$MCP_FILE"
                    
                    echo "✅ Successfully merged WeConnect server into $MCP_FILE"
                else
                    echo "⚠️  'jq' command not found. Using manual merge..."
                    echo ""
                    echo "Please manually add the 'weconnect' server from:"
                    echo "  → $CONFIG_FILE"
                    echo ""
                    echo "To install jq:"
                    if [ "$IS_WINDOWS" = true ]; then
                        echo "  Windows: choco install jq"
                    else
                        echo "  macOS: brew install jq"
                        echo "  Linux: sudo apt install jq / sudo yum install jq"
                    fi
                fi
            else
                echo "Merge cancelled."
            fi
        fi
        
        echo ""
        echo "Next steps:"
        echo "  1. Restart VS Code or reload window (Cmd+Shift+P → 'Developer: Reload Window')"
        echo "  2. Trust the MCP server when prompted"
        echo "  3. Verify installation: Type '/list' in Copilot Chat to see all available tools"
        echo "     → Look for tools starting with 'mcp_weconnect_' (e.g., mcp_weconnect_get_vehicles)"
        echo "  4. Test it: Try '@mcp_weconnect_get_vehicles' in Copilot Chat"
        echo ""
        echo "ℹ️  Note: Tool names are prefixed with 'mcp_weconnect_' by VS Code"
        echo "   (Server name 'weconnect' + tool name = 'mcp_weconnect_get_vehicles')"
        echo ""
        ;;
        
    2)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🖱️  METHOD 2: GUI Installation (Command Palette)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Follow these steps in VS Code:"
        echo ""
        echo "1. Open Command Palette:"
        echo "   → Press Cmd+Shift+P (macOS) or Ctrl+Shift+P (Windows/Linux)"
        echo ""
        echo "2. Type and select:"
        echo "   → 'Preferences: Open User MCP Settings (JSON)'"
        echo ""
        echo "3. Copy the configuration from:"
        echo "   → $CONFIG_FILE"
        echo ""
        echo "4. Merge it into your mcp.json file"
        echo "   (Add the 'weconnect' entry to the 'servers' object)"
        echo ""
        echo "5. Save the file (Cmd+S / Ctrl+S)"
        echo ""
        echo "6. Reload VS Code:"
        echo "   → Press Cmd+Shift+P → 'Developer: Reload Window'"
        echo ""
        echo "7. Trust the MCP server when prompted"
        echo ""
        echo "8. Verify installation:"
        echo "   → Open Copilot Chat"
        echo "   → Type '/list' to see all available tools"
        echo "   → Look for tools starting with 'mcp_weconnect_'"
        echo ""
        echo "9. Test it:"
        echo "   → Type '@mcp_weconnect_get_vehicles' in Copilot Chat"
        echo ""
        echo "ℹ️  Note: Tool names are prefixed with 'mcp_weconnect_' by VS Code"
        echo "   (Server name 'weconnect' + tool name = 'mcp_weconnect_get_vehicles')"
        echo ""
        ;;
        
    3)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✏️  METHOD 3: Manual Installation (Direct File Edit)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Manually edit your VS Code MCP configuration file:"
        echo ""
        echo "📁 File location:"
        echo "   → $MCP_FILE"
        echo ""
        echo "📝 Configuration to add:"
        echo ""
        cat "$CONFIG_FILE"
        echo ""
        echo "Steps:"
        echo "  1. Open the file in your editor:"
        if [ "$IS_WINDOWS" = true ]; then
            echo "     code \"$MCP_FILE\""
        else
            echo "     $ open -a 'Visual Studio Code' \"$MCP_FILE\""
            echo "     or"
            echo "     $ code \"$MCP_FILE\""
        fi
        echo ""
        echo "  2. Add the 'weconnect' server configuration shown above"
        echo "     (Merge it into the 'servers' object)"
        echo ""
        echo "  3. Save the file"
        echo ""
        echo "  4. Restart VS Code or reload window (Cmd+Shift+P → 'Developer: Reload Window')"
        echo ""
        echo "  5. Trust the MCP server when prompted"
        echo ""
        echo "  6. Verify: Type '/list' in Copilot Chat to see all tools"
        echo "     (Look for tools starting with 'mcp_weconnect_')"
        echo ""
        echo "  7. Test: Type '@mcp_weconnect_get_vehicles' in Copilot Chat"
        echo ""
        ;;
        
    4)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "ℹ️  ALL INSTALLATION METHODS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "METHOD 1: Automatic (Script-based) ⭐ RECOMMENDED"
        echo "───────────────────────────────────────────────"
        echo "  Automatically merges config into: $MCP_FILE"
        echo ""
        echo "  Pros: Fastest, preserves existing config"
        echo "  Cons: Requires 'jq' for safe merging"
        echo ""
        echo ""
        echo "METHOD 2: GUI (Command Palette)"
        echo "────────────────────────────────"
        echo "  1. Cmd+Shift+P → 'Preferences: Open User MCP Settings (JSON)'"
        echo "  2. Copy config from: $CONFIG_FILE"
        echo "  3. Paste and save"
        echo ""
        echo "  Pros: User-friendly, visual"
        echo "  Cons: More manual steps"
        echo ""
        echo ""
        echo "METHOD 3: Manual (File Edit)"
        echo "─────────────────────────────"
        echo "  $ code \"$MCP_FILE\""
        echo ""
        echo "  Pros: Full control"
        echo "  Cons: Most manual steps"
        echo ""
        echo ""
        echo "Configuration file available at:"
        echo "  → $CONFIG_FILE"
        echo ""
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again and select 1-4."
        exit 1
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Additional Resources:"
echo "  • VS Code MCP Docs: https://code.visualstudio.com/docs/copilot/customization/mcp-servers"
echo "  • Project README: $PROJECT_DIR/README.md"
echo "  • Generated config: $CONFIG_FILE"
echo ""
echo "❓ Need help?"
echo "  • Check logs: $PROJECT_DIR/logs/mcp_server.log"
echo "  • VS Code Command Palette: 'MCP: List Servers' to see installed servers"
echo "  • VS Code → Help → Toggle Developer Tools → Console tab for errors"
echo ""
echo "⚠️  Note: The old 'github.copilot.chat.mcpServers' in settings.json is deprecated."
echo "   Always use mcp.json for MCP server configuration."
echo ""
