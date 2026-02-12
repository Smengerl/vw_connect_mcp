# Scripts Directory

This directory contains utility scripts for the weconnect_mvp project.

## Platform Support

All scripts are available for both Unix-like systems (Linux/macOS) and Windows:
- **Unix/Linux/macOS**: Use `.sh` scripts (e.g., `./scripts/setup.sh`)
- **Windows**: Use `.bat` scripts (e.g., `scripts\setup.bat`)

The functionality is identical across platforms.

---

## Available Scripts

### test.sh / test.bat
Run the test suite with optional filtering.

**Linux/macOS:**
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

**Windows:**
```cmd
REM Run all tests (including slow real API tests)
scripts\test.bat

REM Run only fast mock tests (recommended for CI/CD)
scripts\test.bat --skip-slow

REM Run with verbose output
scripts\test.bat --skip-slow -v

REM Show help
scripts\test.bat --help
```

**Options:**
- `--skip-slow` - Skip tests marked as 'slow' or 'real_api'
- `-v, --verbose` - Run pytest in verbose mode
- `-h, --help` - Show help message

**Test Statistics:**
- 197 fast mock tests (~2-4 seconds, no VW account needed)
- 18 slow real API tests (require valid `src/config.json`)

---

### vehicle_command.sh / vehicle_command.bat
Send commands to VW vehicles using CarConnectivityAdapter.

**Linux/macOS:**
```bash
# Show help
./scripts/vehicle_command.sh --help

# Lock vehicle
./scripts/vehicle_command.sh ID7 lock

# Unlock vehicle
./scripts/vehicle_command.sh Golf unlock

# Start charging
./scripts/vehicle_command.sh ID7 start_charging

# Start climate control
./scripts/vehicle_command.sh ID7 start_climatization
```

**Windows:**
```cmd
REM Show help
scripts\vehicle_command.bat --help

REM Lock vehicle
scripts\vehicle_command.bat ID7 lock

REM Unlock vehicle
scripts\vehicle_command.bat Golf unlock

REM Start charging
scripts\vehicle_command.bat ID7 start_charging

REM Start climate control
scripts\vehicle_command.bat ID7 start_climatization
```

**⚠️ WARNING:** This will ACTUALLY execute commands on your vehicle! Only use for testing in safe conditions.

**Available Commands:**

**Lock/Unlock:**
- `lock` - Lock the vehicle
- `unlock` - Unlock the vehicle

**Climatization:**
- `start_climatization` - Start climate control
- `stop_climatization` - Stop climate control

**Charging (BEV/PHEV only):**
- `start_charging` - Start charging
- `stop_charging` - Stop charging

**Lights/Horn:**
- `flash_lights` - Flash lights only
- `honk_and_flash` - Honk and flash lights

**Window Heating:**
- `start_window_heating` - Start window heating
- `stop_window_heating` - Stop window heating

**Requirements:**
- Valid VW credentials in `src/config.json`
- Vehicle must be connected and online

**Technical Details:**
- Uses `CarConnectivityAdapter` (not direct carconnectivity library)
- Automatically activates virtualenv
- Validates vehicle existence before execution
- Returns proper exit codes (0 = success, 1 = failure)

---

### start_server_fg.sh / start_server_fg.bat
Start the MCP server in foreground mode (with console output).

**Linux/macOS:**
```bash
./scripts/start_server_fg.sh
# or with custom config
./scripts/start_server_fg.sh path/to/config.json
```

**Windows:**
```cmd
scripts\start_server_fg.bat
REM or with custom config
scripts\start_server_fg.bat path\to\config.json
```

---

### start_server_bg.sh / start_server_bg.bat
Start the MCP server in background mode (logs to file).

**Linux/macOS:**
```bash
./scripts/start_server_bg.sh
# or with custom config
./scripts/start_server_bg.sh path/to/config.json
```

**Windows:**
```cmd
scripts\start_server_bg.bat
REM or with custom config
scripts\start_server_bg.bat path\to\config.json
```

Logs are written to `logs/server.log`.

---

### stop_server_bg.sh / stop_server_bg.bat
Stop the background server.

**Linux/macOS:**
```bash
./scripts/stop_server_bg.sh
```

**Windows:**
```cmd
scripts\stop_server_bg.bat
```

**Note:** Windows version provides instructions for manual process termination due to platform limitations.

---

### setup.sh / setup.bat
Initialize the project (install dependencies, create virtualenv).

**Linux/macOS:**
```bash
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

---

### activate_venv.sh / activate_venv.bat
Activate the Python virtual environment.

**Linux/macOS:**
```bash
source ./scripts/activate_venv.sh
```

**Windows:**
```cmd
call scripts\activate_venv.bat
```

---

### create_claude_config.sh / create_claude_config.bat
Generate MCP configuration for Claude Desktop.

**Linux/macOS:**
```bash
./scripts/create_claude_config.sh
```

**Windows:**
```cmd
scripts\create_claude_config.bat
```

Copy the output to your Claude Desktop configuration file or use the generated file from `tmp/claude_desktop/claude_desktop_config.json`.

---

### create_github_copilot_config.sh / create_github_copilot_config.bat
Generate MCP configuration for GitHub Copilot (VS Code).

**Linux/macOS:**
```bash
./scripts/create_github_copilot_config.sh
```

**Windows:**
```cmd
scripts\create_github_copilot_config.bat
```

Copy the output to your VS Code settings.json or use the generated file from `tmp/github_copilot_vscode/settings.json`.

---

### create_copilot_desktop_config.sh / create_copilot_desktop_config.bat
Generate MCP configuration for Microsoft Copilot Desktop.

**Linux/macOS:**
```bash
./scripts/create_copilot_desktop_config.sh
```

**Windows:**
```cmd
scripts\create_copilot_desktop_config.bat
```

Copy the output or use the generated file from `tmp/copilot_desktop/mcp.json`.

---

## Development Scripts

### carconnectivity/
Contains legacy scripts that directly use the carconnectivity library (without adapter layer).

**⚠️ Deprecated:** Use `vehicle_command.sh` instead for new development.

---

## Usage Patterns

### Running Tests Before Commit

**Linux/macOS:**
```bash
# Fast - only mock tests
./scripts/test.sh --skip-slow

# Complete - all tests including real API
./scripts/test.sh
```

**Windows:**
```cmd
REM Fast - only mock tests
scripts\test.bat --skip-slow

REM Complete - all tests including real API
scripts\test.bat
```

### Testing Vehicle Commands

**Linux/macOS:**
```bash
# Check if vehicle is accessible
./scripts/vehicle_command.sh ID7 lock

# Test climate control
./scripts/vehicle_command.sh Golf start_climatization

# Test charging (BEV/PHEV only)
./scripts/vehicle_command.sh ID7 start_charging
```

**Windows:**
```cmd
REM Check if vehicle is accessible
scripts\vehicle_command.bat ID7 lock

REM Test climate control
scripts\vehicle_command.bat Golf start_climatization

REM Test charging (BEV/PHEV only)
scripts\vehicle_command.bat ID7 start_charging
```

### Development Workflow

**Linux/macOS:**
```bash
# 1. Activate venv
source ./scripts/activate_venv.sh

# 2. Make changes to code

# 3. Run tests
./scripts/test.sh --skip-slow

# 4. Test with real vehicle (optional)
./scripts/vehicle_command.sh ID7 lock

# 5. Commit if all tests pass
```

**Windows:**
```cmd
REM 1. Activate venv
call scripts\activate_venv.bat

REM 2. Make changes to code

REM 3. Run tests
scripts\test.bat --skip-slow

REM 4. Test with real vehicle (optional)
scripts\vehicle_command.bat ID7 lock

REM 5. Commit if all tests pass
```

---

## Exit Codes

All scripts follow standard exit codes:
- `0` - Success
- `1` - Error/Failure

This allows for easy integration in CI/CD pipelines and shell scripts.

## Virtual Environment

All scripts automatically activate the virtual environment (using `activate_venv.sh` or `activate_venv.bat`). You don't need to manually activate it before running scripts.

## Windows Notes

- The Windows `.bat` scripts provide the same functionality as their Unix `.sh` equivalents
- Some features like background process management differ slightly due to Windows limitations (documented in the scripts)
- All scripts use `%TEMP%` for temporary files on Windows (equivalent to `/tmp` on Unix)
- Path separators are automatically handled (`\` on Windows, `/` on Unix)
