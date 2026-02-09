# Scripts Directory

This directory contains utility scripts for the weconnect_mvp project.

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

### vehicle_command.sh
Send commands to VW vehicles using CarConnectivityAdapter.

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

Copy the output to your Claude Desktop configuration file or use the generated file from `tmp/claude_desktop/claude_desktop_config.json`.

---

### create_github_copilot_config.sh
Generate MCP configuration for GitHub Copilot (VS Code).

```bash
./scripts/create_github_copilot_config.sh
```

Copy the output to your VS Code settings.json or use the generated file from `tmp/github_copilot_vscode/settings.json`.

---

### create_copilot_desktop_config.sh
Generate MCP configuration for Microsoft Copilot Desktop.

```bash
./scripts/create_copilot_desktop_config.sh
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
```bash
# Fast - only mock tests
./scripts/test.sh --skip-slow

# Complete - all tests including real API
./scripts/test.sh
```

### Testing Vehicle Commands
```bash
# Check if vehicle is accessible
./scripts/vehicle_command.sh ID7 lock

# Test climate control
./scripts/vehicle_command.sh Golf start_climatization

# Test charging (BEV/PHEV only)
./scripts/vehicle_command.sh ID7 start_charging
```

### Development Workflow
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

---

## Exit Codes

All scripts follow standard Unix exit codes:
- `0` - Success
- `1` - Error/Failure

This allows for easy integration in CI/CD pipelines and shell scripts.

## Virtual Environment

All scripts automatically activate the virtual environment using `activate_venv.sh`. You don't need to manually activate it before running scripts.
