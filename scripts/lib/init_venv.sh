#!/usr/bin/env bash
# Utility library for virtual environment setup and activation
# Provides: init_venv_or_exit() function that handles detection, validation, and activation
# Works on macOS, Linux, and Windows (Git Bash / WSL / MinGW)
#
# Usage in your script:
#   source "$(dirname "$0")/lib/init_venv.sh"
#   init_venv_or_exit "$ROOT_DIR/.venv"
#   # Now VENV_PYTHON is available and venv is activated

# Initialize and activate virtual environment, or exit with error
# Arguments:
#   $1 - Path to virtual environment directory (e.g., "$ROOT_DIR/.venv")
# Outputs:
#   VENV_PYTHON   - Full path to Python in venv
#   VENV_PIP      - Full path to pip in venv
#   VENV_ACTIVATE - Full path to activate script
# Returns:
#   0 on success, 1 on failure (calls exit 1 on error)
init_venv_or_exit() {
    local venv_dir="$1"
    
    if [ -z "$venv_dir" ]; then
        echo "❌ Error: init_venv_or_exit requires venv_dir argument" >&2
        exit 1
    fi
    
    # Source the shared detection library (relative to this file, not the caller)
    local lib_dir
    lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # shellcheck source=./detect_python.sh
    source "$lib_dir/detect_python.sh"
    
    # Detect OS and Python
    detect_python || exit 1
    
    # Get venv paths
    get_venv_paths "$venv_dir"
    get_venv_activate_script "$venv_dir"
    
    # Check if venv exists
    if [ ! -f "$VENV_ACTIVATE" ]; then
        echo "❌ Error: Virtual environment not found at $venv_dir" >&2
        echo "   Run ./scripts/setup.sh to create it first." >&2
        exit 1
    fi
    
    # Activate venv
    echo "Activating virtualenv from $venv_dir"
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
    
    # Export paths for use in calling script
    export VENV_PYTHON
    export VENV_PIP
    export VENV_ACTIVATE
}
