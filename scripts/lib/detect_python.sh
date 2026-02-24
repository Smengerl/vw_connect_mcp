#!/usr/bin/env bash
# Shared utility library for Python executable detection
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
# 
# Usage in your script:
#   source "$(dirname "$0")/lib/detect_python.sh"
#   detect_python
#   # Now you have: PYTHON_BIN, VENV_PYTHON, VENV_PIP, IS_WINDOWS, OS_TYPE

# Detect OS type
detect_os() {
    OS_TYPE=$(uname -s)
    
    if [[ "$OS_TYPE" == "MINGW64"* ]] || [[ "$OS_TYPE" == "MSYS"* ]]; then
        IS_WINDOWS=true
    else
        IS_WINDOWS=false
    fi
}

# Validate that Python executable is real (not Microsoft Store alias)
# Returns 0 if executable is valid, 1 if it's a Store alias
is_valid_python() {
    local python_path="$1"
    
    if [ -z "$python_path" ]; then
        return 1
    fi
    
    # Check if it's a Microsoft Store alias (contains WindowsApps in path)
    # This applies to both Git Bash and WSL
    if echo "$python_path" | grep -iq "WindowsApps"; then
        return 1
    fi
    
    # Verify it's actually executable
    if [ ! -x "$python_path" ]; then
        return 1
    fi
    
    return 0
}

# Find Python executable (tries multiple options)
# On Windows: 'python' is usually the real installation, 'python3' may be a Microsoft Store alias
# On Unix: prefers 'python3' over 'python'
find_python_bin() {
    PYTHON_BIN=""
    
    # On Windows, try 'python' first (real installation), then 'python3'
    # On Unix, try 'python3' first, then 'python'
    if [ "$IS_WINDOWS" = true ]; then
        # Try 'python' first
        local python_candidate="$(command -v python 2>/dev/null)"
        if is_valid_python "$python_candidate"; then
            PYTHON_BIN="$python_candidate"
        else
            # Fall back to 'python3', but skip Microsoft Store alias
            local python3_candidate="$(command -v python3 2>/dev/null)"
            if is_valid_python "$python3_candidate"; then
                PYTHON_BIN="$python3_candidate"
            fi
        fi
    else
        # Try 'python3' first
        local python3_candidate="$(command -v python3 2>/dev/null)"
        if is_valid_python "$python3_candidate"; then
            PYTHON_BIN="$python3_candidate"
        else
            # Fall back to 'python'
            local python_candidate="$(command -v python 2>/dev/null)"
            if is_valid_python "$python_candidate"; then
                PYTHON_BIN="$python_candidate"
            fi
        fi
    fi
    
    if [ -z "$PYTHON_BIN" ]; then
        echo "❌ Error: Python not found on PATH" >&2
        echo "   Please install Python 3.10+ and add it to PATH" >&2
        echo "   Note: Windows Microsoft Store Python is not supported" >&2
        return 1
    fi
}

# Get virtualenv python paths based on OS
get_venv_paths() {
    local venv_dir="$1"
    
    if [ ! -d "$venv_dir" ]; then
        echo "❌ Error: Virtual environment not found at $venv_dir" >&2
        return 1
    fi
    
    if [ "$IS_WINDOWS" = true ]; then
        VENV_PYTHON="$venv_dir/Scripts/python.exe"
        VENV_PIP="$venv_dir/Scripts/pip.exe"
    else
        VENV_PYTHON="$venv_dir/bin/python"
        VENV_PIP="$venv_dir/bin/pip"
    fi
}

# Get venv activation script path
get_venv_activate_script() {
    local venv_dir="$1"
    
    if [ "$IS_WINDOWS" = true ]; then
        VENV_ACTIVATE="$venv_dir/Scripts/activate"
    else
        VENV_ACTIVATE="$venv_dir/bin/activate"
    fi
}

# Get MCP file path for current OS
get_mcp_file_path() {
    if [ "$IS_WINDOWS" = true ]; then
        local appdata_path="${APPDATA:-$HOME/AppData/Roaming}"
        MCP_FILE="$appdata_path\\Microsoft\\VSCode\\mcp.json"
    elif [ "$(uname)" = "Darwin" ]; then
        MCP_FILE="$HOME/Library/Application Support/Code/User/mcp.json"
    else
        MCP_FILE="$HOME/.config/Code/User/mcp.json"
    fi
}

# Get Claude Desktop config path for current OS
get_claude_config_path() {
    if [ "$IS_WINDOWS" = true ]; then
        local appdata_path="${APPDATA:-$HOME/AppData/Roaming}"
        CLAUDE_CONFIG="$appdata_path\\Claude\\claude_desktop_config.json"
    else
        CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    fi
}

# Get Copilot Desktop config path for current OS
get_copilot_config_path() {
    if [ "$IS_WINDOWS" = true ]; then
        local appdata_path="${APPDATA:-$HOME/AppData/Roaming}"
        COPILOT_CONFIG="$appdata_path\\Microsoft\\Copilot\\mcp.json"
    else
        COPILOT_CONFIG="$HOME/Library/Application Support/Microsoft/Copilot/mcp.json"
    fi
}

# Main detection function - call this to initialize all variables
detect_python() {
    detect_os
    find_python_bin || return 1
}

# Print detection summary (useful for debugging)
print_detection_summary() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Python & Platform Detection Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "OS Type:              $OS_TYPE"
    echo "Is Windows:           $IS_WINDOWS"
    echo "System Python:        $PYTHON_BIN"
    if [ -n "$VENV_PYTHON" ]; then
        echo "Venv Python:          $VENV_PYTHON"
        echo "Venv Pip:             $VENV_PIP"
    fi
    if [ -n "$VENV_ACTIVATE" ]; then
        echo "Venv Activate:        $VENV_ACTIVATE"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}
