#!/usr/bin/env bash
# Generate an MCP client config for weconnect-mcp.
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
#
# Usage: ./scripts/create_mcp_config.sh <claude|copilot-desktop|vscode>
#
# Replaces the three near-identical scripts this project used to ship
# (create_claude_config.sh, create_copilot_desktop_config.sh,
# create_github_copilot_config.sh) -- they differed only in the JSON root
# key, the destination path, and VS Code getting two extra CLI flags plus
# an interactive auto-merge wizard. That wizard is gone here: all three
# clients now get the same simple "here's the file, here's where it goes,
# here's a one-line jq merge if you have it" flow instead of VS Code's
# multi-option menu -- less to maintain, at the cost of that one client
# losing its guided merge-with-backup convenience.

set -euo pipefail

CLIENT="${1:-}"
if [[ "$CLIENT" != "claude" && "$CLIENT" != "copilot-desktop" && "$CLIENT" != "vscode" ]]; then
  echo "Usage: $0 <claude|copilot-desktop|vscode>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=./lib/detect_python.sh
source "$SCRIPT_DIR/lib/detect_python.sh"
detect_python || exit 1

# shellcheck source=./lib/init_venv.sh
source "$SCRIPT_DIR/lib/init_venv.sh"
init_venv_or_exit "$PROJECT_DIR/.venv"
PYTHON_PATH="$VENV_PYTHON"

echo "Project directory: $PROJECT_DIR"
echo "OS: $OS_TYPE"
echo "Using virtual environment: $PYTHON_PATH"
echo ""

# Credentials live in a gitignored JSON file rather than environment
# variables, because these clients all launch the server with their own
# environment, not your shell's -- env vars set via `export` never reach it.
TIBBER_CONFIG="$PROJECT_DIR/src/tibber_config.json"
if [ ! -f "$TIBBER_CONFIG" ]; then
  echo "⚠️  $TIBBER_CONFIG not found."
  echo "   Register an OAuth2 client at https://data-api.tibber.com/clients/manage/"
  echo "   (see ARCHITECTURE.md for the exact scopes/redirect URI),"
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

# Per-client shape: JSON root key, output staging path, real destination,
# and (VS Code only) two extra CLI flags this client's config has always
# carried (a quieter default log level plus a log file, since VS Code
# otherwise has no console to show server stderr in).
case "$CLIENT" in
  claude)
    JSON_ROOT_KEY="mcpServers"
    OUTPUT_FILE="$PROJECT_DIR/tmp/claude_desktop/claude_desktop_config.json"
    get_claude_config_path
    DEST="$CLAUDE_CONFIG"
    EXTRA_ARGS=()
    ;;
  copilot-desktop)
    JSON_ROOT_KEY="servers"
    OUTPUT_FILE="$PROJECT_DIR/tmp/copilot_desktop/mcp.json"
    get_copilot_config_path
    DEST="$COPILOT_CONFIG"
    EXTRA_ARGS=()
    ;;
  vscode)
    JSON_ROOT_KEY="servers"
    OUTPUT_FILE="$PROJECT_DIR/tmp/vscode/mcp.json"
    get_mcp_file_path
    DEST="$MCP_FILE"
    EXTRA_ARGS=("--log-level" "ERROR" "--log-file" "$PROJECT_DIR/logs/mcp_server.log")
    ;;
esac

mkdir -p "$(dirname "$OUTPUT_FILE")"

# Built via python3 -c (already a hard requirement of this script, through
# init_venv_or_exit above) rather than hand-rolled heredoc/printf string
# concatenation: json.dumps() correctly escapes PYTHON_PATH/PROJECT_DIR/
# TIBBER_CONFIG regardless of their content, and each arg reaches Python
# as its own argv entry (no shell-string-interpolation step at all) --
# unlike the previous approach, a path containing a `"` or `\` (plausible
# on a Windows path not fully translated by Git Bash) can't produce
# invalid JSON here.
args=("-m" "weconnect_mcp.cli.mcp_server_cli" "$TIBBER_CONFIG")
args+=(${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"})

PYTHON_PATH="$PYTHON_PATH" PROJECT_DIR="$PROJECT_DIR" JSON_ROOT_KEY="$JSON_ROOT_KEY" CLIENT="$CLIENT" \
"$PYTHON_PATH" -c '
import json
import os
import sys

server = {
    "command": os.environ["PYTHON_PATH"],
    "args": sys.argv[1:],
    "cwd": os.environ["PROJECT_DIR"],
}
if os.environ["CLIENT"] == "vscode":
    server["type"] = "stdio"

doc = {os.environ["JSON_ROOT_KEY"]: {"weconnect": server}}
if os.environ["CLIENT"] == "vscode":
    doc["inputs"] = []

print(json.dumps(doc, indent=2))
' "${args[@]}" > "$OUTPUT_FILE"

echo "✅ Configuration saved to: $OUTPUT_FILE"
echo ""
echo "📋 Copy it into: $DEST"
echo ""

if command -v jq &> /dev/null && [ -f "$DEST" ]; then
  echo "Tip: jq is available and a config already exists there -- merge instead of overwriting"
  echo "(back up '$DEST' first if it's not under version control):"
  echo "  jq --argjson server \"\$(jq '.\"$JSON_ROOT_KEY\".weconnect' '$OUTPUT_FILE')\" \\"
  echo "     '.\"$JSON_ROOT_KEY\".weconnect = \$server' '$DEST' > '$DEST.tmp' && mv '$DEST.tmp' '$DEST'"
  echo ""
fi

echo "After editing, restart $CLIENT completely."
