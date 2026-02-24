# Scripts Directory

This directory contains utility scripts for the weconnect_mvp project.

## 🖥️ Platform Support

All scripts now work on:
- **macOS** (Bash / Zsh)
- **Linux** (Bash)
- **Windows** (Git Bash, WSL, MinGW, or PowerShell with Git Bash installed)

Python detection is automatic:
- Uses `python3` on macOS/Linux
- Uses `python` on Windows (falls back to `python3` if available)
- Uses virtualenv paths appropriate for each OS

## 🧰 Shared Library

All scripts now use a centralized Python detection library to eliminate code duplication.

### `lib/detect_python.sh`

Provides platform-aware utilities for:
- Detecting OS type (Windows, macOS, Linux)
- Finding Python executables
- Resolving virtualenv paths (platform-specific)
- Getting configuration file paths for VS Code, Claude Desktop, and Copilot Desktop

**Benefits**:
- ✅ Single source of truth for platform detection
- ✅ Consistent behavior across all scripts
- ✅ Easy to extend for new configuration paths
- ✅ No code duplication

See [lib/README.md](lib/README.md) for detailed documentation and usage examples.

### Running Scripts on Windows

#### Option 1: Git Bash (Recommended)
```bash
# Git Bash handles all scripts transparently
./scripts/setup.sh
./scripts/test.sh --skip-slow
./scripts/create_github_copilot_config.sh
```

#### Option 2: WSL (Windows Subsystem for Linux)
```bash
# Works exactly like Linux
bash scripts/setup.sh
bash scripts/test.sh
```

#### Option 3: MinGW / MSYS2
```bash
# Same as Git Bash
./scripts/setup.sh
```

#### Option 4: PowerShell with WSL
```powershell
wsl ./scripts/setup.sh
wsl ./scripts/test.sh --skip-slow
```

## Available Scripts

### test.sh
Run the test suite with optional filtering.

```bash
# Run all tests (including slow real API tests)
./scripts/test.sh

# Run only fast mock tests (recommended for CI/CD)
./scripts/test.sh --skip-slow

# Run with verbose output
./scripts/test.sh --skip-slow -v

# Show help
./scripts/test.sh --help
```

**Options:**
- `--skip-slow` - Skip tests marked as 'slow' or 'real_api'
- `-v, --verbose` - Run pytest in verbose mode
- `-h, --help` - Show help message

**Test Statistics:**
- 197 fast mock tests (~2-4 seconds, no VW account needed)
- 18 slow real API tests (require valid `src/config.json`)

---

### start_server_fg.sh
Start the MCP server in foreground (with console output).

```bash
./scripts/start_server_fg.sh
```

---

### start_server_bg.sh
Start the MCP server in background (with log file output).

```bash
./scripts/start_server_bg.sh
```

---

### stop_server_bg.sh
Stop the MCP server running in background.

```bash
./scripts/stop_server_bg.sh
```

---

### setup.sh
Initialize the project (install dependencies, create virtualenv).

```bash
./scripts/setup.sh
```

---

### activate_venv.sh
Activate the Python virtual environment.

```bash
source ./scripts/activate_venv.sh
```

---

### create_claude_config.sh
Generate MCP configuration for Claude Desktop.

```bash
./scripts/create_claude_config.sh
```

**Output locations:**
- Configuration saved to `tmp/claude_desktop/claude_desktop_config.json`
- On **macOS**: Copy to `~/Library/Application Support/Claude/claude_desktop_config.json`
- On **Windows**: Copy to `%APPDATA%\Claude\claude_desktop_config.json`
- On **Linux**: Varies by distribution

---

### create_github_copilot_config.sh
Generate MCP configuration for GitHub Copilot (VS Code).

```bash
./scripts/create_github_copilot_config.sh
```

**Output locations:**
- Configuration saved to `tmp/github_copilot_vscode/mcp.json`
- On **macOS**: `~/Library/Application Support/Code/User/mcp.json`
- On **Windows**: `%APPDATA%\Microsoft\VSCode\mcp.json`
- On **Linux**: `~/.config/Code/User/mcp.json`

**Interactive installation:**
The script offers 4 options:
1. **🎯 Automatic** - Auto-merges into existing `mcp.json` (requires `jq`)
2. **🖱️ GUI** - Instructions for VS Code Command Palette
3. **✏️ Manual** - Instructions for manual file editing
4. **ℹ️ Info** - Show all methods

**After Installation:**
- Restart VS Code (`Cmd+Shift+P` → `Developer: Reload Window`)
- Type `/list` in Copilot Chat to verify installation
- Look for tools starting with `mcp_weconnect_` (e.g., `mcp_weconnect_get_vehicles`)
- VS Code automatically prefixes tools with `mcp_{servername}_` to avoid naming conflicts

---

### create_copilot_desktop_config.sh
Generate MCP configuration for Microsoft Copilot Desktop.

```bash
./scripts/create_copilot_desktop_config.sh
```

**Output locations:**
- Configuration saved to `tmp/copilot_desktop/mcp.json`
- On **macOS**: `~/Library/Application Support/Microsoft/Copilot/mcp.json`
- On **Windows**: `%APPDATA%\Microsoft\Copilot\mcp.json`

---

## Development Notes

### Running Tests Before Commit
```bash
# Fast - only mock tests
./scripts/test.sh --skip-slow

# Complete - all tests including real API
./scripts/test.sh
```

### Development Workflow
```bash
# 1. Setup project
./scripts/setup.sh

# 2. Activate venv
source ./scripts/activate_venv.sh

# 3. Make changes to code

# 4. Run tests
./scripts/test.sh --skip-slow

# 5. Commit if all tests pass
```

---

## Exit Codes

All scripts follow standard Unix exit codes:
- `0` - Success
- `1` - Error/Failure

This allows for easy integration in CI/CD pipelines and shell scripts.

## Virtual Environment

All scripts automatically activate the virtual environment using `activate_venv.sh`. You don't need to manually activate it before running scripts.
