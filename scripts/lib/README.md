# Script Library - Shared Utilities

## Overview

This directory contains shared bash utility scripts that are used by multiple setup and configuration scripts in the project.

## Available Modules

### `detect_python.sh`

**Purpose**: Automatically detects and configures Python executable paths based on the operating system (Windows, macOS, Linux).

**Features**:
- ✅ OS detection (Windows via MinGW/MSYS, macOS, Linux)
- ✅ Python executable discovery (prefers `python3`, falls back to `python`)
- ✅ Virtual environment path resolution (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere)
- ✅ Configuration file paths for different platforms (VS Code, Claude Desktop, Copilot Desktop)

**Usage in Your Script**:

```bash
#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Source the detection library
source "$(dirname "$0")/lib/detect_python.sh"

# Initialize detection
detect_python || exit 1

# Get venv paths (if venv exists)
get_venv_paths "$ROOT_DIR/.venv"

# Get venv activation script
get_venv_activate_script "$ROOT_DIR/.venv"

# Now you have these variables available:
# - OS_TYPE          : "Linux", "Darwin", "MINGW64_NT", etc.
# - IS_WINDOWS       : "true" or "false"
# - PYTHON_BIN       : System Python executable path
# - VENV_PYTHON      : Virtual env Python executable path
# - VENV_PIP         : Virtual env Pip executable path
# - VENV_ACTIVATE    : Virtual env activation script path

echo "System Python: $PYTHON_BIN"
echo "Venv Python: $VENV_PYTHON"
```

**Available Functions**:

#### `detect_os()`
Detects the operating system and sets:
- `OS_TYPE`: uname output
- `IS_WINDOWS`: true/false flag

#### `find_python_bin()`
Finds system Python executable.
- **Windows**: Tries `python` first (real installation), falls back to `python3`
- **Unix**: Tries `python3` first, falls back to `python`
- Sets: `PYTHON_BIN`
- Returns: 1 if not found

**Note**: On Windows, `python3` may be a Microsoft Store alias that doesn't work. Always try `python` first on Windows.

#### `detect_python()`
Main initialization function - calls `detect_os()` and `find_python_bin()`.
- Call this first to initialize all variables
- Returns: 1 if Python not found

#### `get_venv_paths(venv_dir)`
Resolves virtual environment Python paths based on OS.
- Sets: `VENV_PYTHON`, `VENV_PIP`
- Argument: Path to `.venv` directory

#### `get_venv_activate_script(venv_dir)`
Gets the activation script path for the virtual environment.
- Sets: `VENV_ACTIVATE`
- Argument: Path to `.venv` directory

#### `get_mcp_file_path()`
Gets VS Code MCP configuration file path.
- Sets: `MCP_FILE`
- Windows: `%APPDATA%\Microsoft\VSCode\mcp.json`
- macOS: `~/Library/Application Support/Code/User/mcp.json`
- Linux: `~/.config/Code/User/mcp.json`

#### `get_claude_config_path()`
Gets Claude Desktop configuration file path.
- Sets: `CLAUDE_CONFIG`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS/Linux: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### `get_copilot_config_path()`
Gets Microsoft Copilot Desktop configuration file path.
- Sets: `COPILOT_CONFIG`
- Windows: `%APPDATA%\Microsoft\Copilot\mcp.json`
- macOS/Linux: `~/Library/Application Support/Microsoft/Copilot/mcp.json`

#### `print_detection_summary()`
Prints a formatted summary of all detected paths (useful for debugging).

**Platform-Specific Behavior**:

| OS | VENV_PYTHON | VENV_PIP | VENV_ACTIVATE |
|----|-------------|----------|---------------|
| Windows | `.venv/Scripts/python.exe` | `.venv/Scripts/pip.exe` | `.venv/Scripts/activate` |
| macOS/Linux | `.venv/bin/python` | `.venv/bin/pip` | `.venv/bin/activate` |

## Scripts Using This Library

The following scripts source and use `detect_python.sh`:

- `setup.sh` - Virtual environment setup
- `activate_venv.sh` - Venv activation
- `start_server_fg.sh` - Start server in foreground
- `start_server_bg.sh` - Start server in background
- `test.sh` - Run test suite
- `create_claude_config.sh` - Generate Claude Desktop config
- `create_copilot_desktop_config.sh` - Generate Copilot Desktop config
- `create_github_copilot_config.sh` - Generate VS Code GitHub Copilot config

## Benefits

- **DRY Principle**: Eliminates code duplication across multiple scripts
- **Maintainability**: Python path logic only lives in one place
- **Platform Agnostic**: Automatically handles Windows, macOS, and Linux differences
- **Testable**: Each function can be tested independently
- **Extensible**: Easy to add more platform-specific paths or utilities

## Example: Adding New Config Path

To add support for a new tool's configuration file:

```bash
# In detect_python.sh, add a new function:
get_mytool_config_path() {
    if [ "$IS_WINDOWS" = true ]; then
        local appdata_path="${APPDATA:-$HOME/AppData/Roaming}"
        MYTOOL_CONFIG="$appdata_path\\MyTool\\config.json"
    else
        MYTOOL_CONFIG="$HOME/Library/Application Support/MyTool/config.json"
    fi
}

# In your script:
source "$(dirname "$0")/lib/detect_python.sh"
detect_python || exit 1
get_mytool_config_path

echo "MyTool config: $MYTOOL_CONFIG"
```

## Testing the Library

```bash
# Source the library
source scripts/lib/detect_python.sh

# Run detection
detect_python

# View results
print_detection_summary
```

## Notes

- All functions use `shellcheck` annotations for linting compatibility
- The library is portable and works on Windows (Git Bash, WSL, MinGW), macOS, and Linux
- When sourcing, use the pattern: `source "$(dirname "$0")/lib/detect_python.sh"`
