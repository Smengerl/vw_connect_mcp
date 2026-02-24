# weconnect_mvp

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-197%20passing-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](http://creativecommons.org/licenses/by-sa/4.0/)

**MCP Server for Volkswagen Vehicles**  
A developer-focused server that exposes information from VW vehicles via a Model Context Protocol (MCP) interface. This project is designed for integration, automation, and experimentation with connected car data.

---

## Quick Start

Get up and running in 3 steps:

1. **Install**
   ```bash
   git clone https://github.com/Smengerl/weconnect_mvp.git
   cd weconnect_mvp
   ./scripts/setup.sh
   ```

2. **Configure**  
   Edit `src/config.json` with your VW credentials (username, password, spin)

3. **Use with Claude Desktop**
   ```bash
   ./scripts/create_claude_config.sh  # Copy output to Claude config
   ```
   Restart Claude Desktop and ask: *"What vehicles are available?"*

For detailed instructions, see sections below.

---

## Features

- **MCP Server**: Provides a standard MCP interface for accessing vehicle data
- **Volkswagen Integration**: Connects to VW vehicles using the `carconnectivity` library
- **AI Assistant Ready**: Works with Claude Desktop, VS Code Copilot, and other MCP-compatible tools
- **Flexible CLI**: Multiple transport modes (stdio for AI, HTTP for API access)
- **Configurable**: Easily adapt connection and authentication settings via config file


## Getting Started

### Prerequisites

- Python 3.8+
- VW account credentials (username, password, and optionally a spin)
- (Recommended) Virtual environment

### Installation

**Quick Start (Recommended):**

Simply run the setup script which handles everything automatically:

```bash
git clone https://github.com/Smengerl/weconnect_mvp.git
cd weconnect_mvp
./scripts/setup.sh
```

The script will:
- ✅ Detect your Python installation
- ✅ Create a virtual environment at `.venv/`
- ✅ Install all dependencies
- ✅ Create configuration template

**Manual Installation (Alternative):**

```bash
git clone https://github.com/Smengerl/weconnect_mvp.git
cd weconnect_mvp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Windows-Specific Notes

⚠️ **Important for Windows Users:**

The setup script automatically detects and avoids Microsoft Store Python (which doesn't work). If you see errors about Python not found:

1. **Install Python from python.org** (not Microsoft Store)
   - Download from [python.org](https://www.python.org)
   - ✅ Check "Add Python to PATH" during installation

2. **Disable Microsoft Store Python alias** (if you have it):
   - Settings → Apps → Advanced app settings → App execution aliases
   - Turn OFF: `python.exe`, `python3.exe`, `python3.x.exe`

3. **Verify your Python installation:**
   ```bash
   # Should return a path like: C:\Program Files\PythonXXX\python.exe
   where python
   ```

4. **Run diagnostic tool:**
   ```powershell
   & .\scripts\diagnose_python.ps1
   ```


### Configuration

The server requires a configuration file (default: `src/config.json`).  
**You must create this file based on the provided example and add your VW credentials.**

**Step 1: Copy the example configuration**
```bash
cp src/config.example.json src/config.json
```

**Step 2: Edit the configuration with your VW credentials**
```bash
# Use your preferred editor
nano src/config.json
# or
code src/config.json
```

Example configuration structure (from `src/config.example.json`):
```json
{
	"carConnectivity": {
		"log_level": "debug",
		"connectors": [
			{
				"type": "volkswagen",
				"disabled": false,
				"config": {
					"log_level": "error",
					"interval": 300,
					"username": "your_email@example.com",
					"password": "your_password_here",
					"spin": "1234",
					"api_log_level": "debug",
					"max_age": 300,
					"force_enable_access": false
				}
			}
		],
		"plugins": []
	}
}
```

**Configuration Parameters:**
- `username`: Your VW WeConnect account email
- `password`: Your VW WeConnect account password
- `spin`: Your VW S-PIN (4 digits, required for some vehicle commands)
- `interval`: Data refresh interval in seconds (default: 300 = 5 minutes)
- `max_age`: Maximum age of cached data in seconds

**Security Notice:**  
⚠️ **NEVER commit `src/config.json` to version control!**  
This file is automatically excluded via `.gitignore` to protect your credentials.

---

## Usage

The server supports two transport modes:
- **stdio**: For AI assistants (Claude Desktop, VS Code Copilot) - recommended for AI integration
- **http**: For programmatic API access - use when building custom applications

### CLI Options

You can start the MCP server using the provided CLI scripts or directly via Python:

#### 1. Starting the server in foreground (with logs to console)
```bash
./scripts/start_server_fg.sh
```

#### 2. Starting the server in background (with logs to file)
```bash
./scripts/start_server_bg.sh
```

#### 3. Starting the server directly via Python
```bash
python -m weconnect_mcp.cli.mcp_server_cli path/to/config.json --port 8765
```

#### 4. Stopping the Server

If started in the background, stop the server using the script:
```bash
./scripts/stop_server.sh
```

Alternatively, kill the process via PID.


### CLI Parameters

The MCP server can be started with several command-line parameters to control its behavior:

| Parameter           | Default                                   | Description                                                      |
|---------------------|-------------------------------------------|------------------------------------------------------------------|
| `config`            | (required)                                | Path to the configuration file                                   |
| `--tokenstorefile`  | `/tmp/tokenstore`                         | Path for the token store file                                    |
| `--log-level`       | `INFO`                                    | Set logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file`        | (stderr only)                             | Path to log file (if not set, logs to stderr only)              |
| `--transport`       | `stdio`                                   | Transport mode: `stdio` (for AI) or `http` (for API)            |
| `--port`            | `8667`                                    | Port for HTTP mode                                               |

**Example:**

```bash
python -m weconnect_mcp.cli.mcp_server_cli src/config.json --log-level DEBUG --log-file server.log --transport http --port 8765
```

---

## AI Integration

This MCP server provides **5 tools** that AI assistants can use to interact with your VW vehicle:

| Tool | Description |
|------|-------------|
| `list_vehicles` | Get all available vehicle IDs |
| `get_vehicle_state` | Get complete vehicle state (battery, position, doors, windows, climate, tyres) |
| `get_vehicle_doors` | Get door lock and open/closed status |
| `get_vehicle_windows` | Get window open/closed status |
| `get_vehicle_tyres` | Get tyre pressure and temperature |

### What AI Assistants Can Do

✅ List vehicles and recognize their IDs  
✅ Intelligently interpret vehicle status  
✅ Retrieve specific information (doors, windows, tyres)  
✅ Answer natural questions like "Where is my car?"  
✅ Combine multiple queries for complex answers  

---

### Claude Desktop Integration

**Setup in 3 steps:**

#### Step 1: Generate Configuration

Interact with your VW car in Claude Desktop - here's how to set it up:

Generate your configuration for Claude Desktop with the following script:

```bash
cd /path/to/weconnect_mvp
./scripts/create_claude_config.sh
```

The script will:
- Automatically detect your Python path
- Generate the complete configuration
- Show you where to save it

#### Step 2: Copy Configuration

Copy the configuration output from the script to your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Note:** A template config is available in `examples/claude_desktop_config.json`, but using the script ensures all paths are correct for your system.

#### Step 3: Restart and Test

1. **Quit Claude Desktop completely** and restart (not just close the window)

2. **Test it** by asking Claude:
   - "What vehicles are available?"
   - "Show me my car's status"
   - "Are my doors locked?"
   - "How much battery does my car have?"

---

### GitHub Copilot (VS Code) Integration

**Setup in 3 steps:**

#### Step 1: Generate Configuration

Generate your configuration for GitHub Copilot with the following script:

```bash
cd /path/to/weconnect_mvp
./scripts/create_github_copilot_config.sh
```

The script will:
- Automatically detect your Python path
- Generate the complete MCP configuration for VS Code
- Show you step-by-step instructions

#### Step 2: Add Configuration to VS Code

1. Open VS Code Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux)
2. Type `Preferences: Open User MCP Settings (JSON)` and press Enter
3. Copy the configuration output from the script into your `mcp.json`

Alternatively, edit the MCP settings file directly:
```bash
code ~/Library/Application\ Support/Code/User/mcp.json  # macOS
```

**Note:** Use the standard `mcp.json` configuration, not the deprecated `github.copilot.chat.mcpServers` setting in `settings.json`.

#### Step 3: Restart and Test

1. **Reload VS Code window**: 
   - Open Command Palette (`Cmd+Shift+P`)
   - Type `Developer: Reload Window`
   - Press Enter

2. **Verify installation**:
   - Open Copilot Chat panel
   - Type `/list` to see all available tools
   - Look for tools starting with `mcp_weconnect_` (e.g., `mcp_weconnect_get_vehicles`)
   
   **Note:** VS Code automatically prefixes tool names with `mcp_{servername}_`. 
   Since your server is named `weconnect`, all tools appear as `mcp_weconnect_*`.

3. **Test the server**:
   - Try `@mcp_weconnect_get_vehicles` in Copilot Chat
   - Ask natural language questions:
     - "What vehicles are available?"
     - "Show me my car's battery status"
     - "Are my doors locked?"

**Available Tools:**
- `mcp_weconnect_get_vehicles` - List all vehicles
- `mcp_weconnect_get_vehicle_info` - Get vehicle information
- `mcp_weconnect_get_vehicle_state` - Get complete state
- `mcp_weconnect_get_vehicle_doors` - Check door status
- `mcp_weconnect_get_battery_status` - Battery info (BEV/PHEV)
- `mcp_weconnect_get_climatization_status` - Climate status
- `mcp_weconnect_get_charging_status` - Charging details (BEV/PHEV)
- `mcp_weconnect_get_vehicle_position` - GPS location
- Plus 10 command tools (`lock_vehicle`, `start_charging`, etc.)

---

### Microsoft Copilot Desktop Integration

**Setup in 3 steps:**

#### Step 1: Generate Configuration

Generate your configuration for Microsoft Copilot Desktop with the following script:

```bash
cd /path/to/weconnect_mvp
./scripts/create_copilot_desktop_config.sh
```

The script will:
- Automatically detect your Python path
- Generate the complete configuration for Copilot Desktop
- Save the configuration to `tmp/copilot_desktop_mcp.json`

#### Step 2: Copy Configuration

Copy the configuration file to Microsoft Copilot Desktop's config directory:

```bash
mkdir -p ~/Library/Application\ Support/Microsoft/Copilot
cp tmp/copilot_desktop_mcp.json ~/Library/Application\ Support/Microsoft/Copilot/mcp.json
```

Alternatively, manually copy the JSON output from the script to the location above.

#### Step 3: Restart and Test

1. **Restart Microsoft Copilot Desktop completely**

2. **Test it** by asking Copilot:
   - "What vehicles are available?"
   - "Show me my car's status"
   - "What's my battery level?"

---

#### Example Interactions

**You**: "List all my vehicles"  
**Claude** uses the `list_vehicles` tool and shows the results

**You**: "What's the status of my car?"  
**Claude** first uses `list_vehicles` to get the vehicle ID, then `get_vehicle_state` for details

**You**: "Are my windows closed?"  
**Claude** uses `get_vehicle_windows` and interprets the results

---

#### Setup Checklist

- [ ] Virtual environment activated and dependencies installed
- [ ] `src/config.json` configured with valid VW credentials
- [ ] Python path in Claude config correct (full path to `.venv/bin/python`)
- [ ] `PYTHONPATH` set in Claude config
- [ ] Claude Desktop completely restarted
- [ ] In case of problems: Logs enabled and checked
- [ ] Token store directory is writable (`/tmp/`)

---

#### Known Limitations

1. **No license plate data (VW API limitation):** As of February 2026, the VW WeConnect API does not provide license plate information. All vehicles will show `license_plate: null`. This is a limitation of Volkswagen's official API, not this server.
2. **First start takes time:** VW API login can take 10-30 seconds
3. **VW API rate limiting:** Too many requests may be blocked
4. **Token expiration:** After a few hours, re-authentication is required
5. **Read-only access:** Currently only data retrieval is possible, no control (opening doors, starting climate control, etc.)

---

#### Troubleshooting 

**"Failed to spawn process: No such file or directory"**

- **Cause:** Claude Desktop cannot find the Python command
- **Solution:** Use full Python path from your venv (the script handles this automatically)
- **Helper script:** `./scripts/create_claude_config.sh`

**"TemporaryAuthenticationError: Token could not be fetched"**

- **Cause:** VW WeConnect server temporarily unavailable, incorrect credentials, or account issues
- **Solutions:**
  1. Wait and retry (VW servers can be overloaded)
  2. Check credentials in `src/config.json`
  3. Delete token store: `rm /tmp/tokenstore` and restart
  4. Test VW WeConnect app to ensure account is working

**Server starts but tools are not displayed**

- **Diagnosis:** Check Claude Desktop logs (Help → View Logs) for `"tools":[...]`
- **Solutions:**
  - Ensure latest version of code is running
  - Completely restart Claude Desktop (not just close window)
  - Clear cache (uninstall and reinstall Claude Desktop)

**Server not responding / Timeout**

- **Cause:** First request after server start can take 10-30 seconds (VW API login)
- **Solutions:**
  - Be patient with first tool call
  - Use token store to avoid re-login
  - Check network (VPN can cause problems)

**Enable Debug Logs**

If problems occur, add logging parameters to your Claude config:

```json
{
  "mcpServers": {
    "weconnect": {
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "/path/to/config.json",
        "--log-level", "debug",
        "--log-file", "/tmp/weconnect_mcp.log"
      ],
      ...
    }
  }
}
```

View logs with:
```bash
tail -f /tmp/weconnect_mcp.log
```

You can also check Claude Desktop logs via: **Help → View Logs** (search for "weconnect")

---

## 📚 Documentation

For detailed setup and configuration guidance:

- **[scripts/README.md](scripts/README.md)** - All available scripts and how to use them
- **[scripts/lib/README.md](scripts/lib/README.md)** - Python detection library documentation
- **[tests/README.md](tests/README.md)** - Test suite overview
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

---

## Testing

Run the test suite with:

```bash
# Run all tests (including slow real API tests)
./scripts/test.sh

# Run only fast mock tests (skip real API tests - recommended for CI/CD)
./scripts/test.sh --skip-slow

# Run with verbose output
./scripts/test.sh --skip-slow -v

# Show help
./scripts/test.sh --help
```

**Test Structure:**
- **197 fast mock tests** - Run in ~4 seconds, no VW credentials needed
- **18 slow real API tests** - Require valid VW account in `src/config.json`

For detailed test documentation, see [tests/README.md](tests/README.md)

---

## Development Notes

- For development, always use a virtual environment and install in editable mode
- The CLI scripts activate the virtual environment automatically
- Main package source is under `src/`

### Publication Readiness Agent

The project includes a custom GitHub Copilot agent to ensure publication readiness. This agent verifies:

- ✅ Code documentation quality (docstrings, type hints)
- ✅ README.md completeness
- ✅ License file presence
- ✅ Unit test coverage
- ✅ CLI scripts documentation

**Usage:**
```bash
# Via GitHub Copilot
@workspace /agent publication-readiness Run publication check

# Or follow the manual checklist
cat .github/agents/publication-readiness.md
```

For more information, see [.github/agents/README.md](.github/agents/README.md).

### Security Best Practices

⚠️ **Never** commit `config.json` with your VW credentials!  
⚠️ Add `src/config.json` to `.gitignore` if not already done  
⚠️ The token store (default: `/tmp/tokenstore`) contains session tokens - keep it secure  
⚠️ Use environment variables for sensitive data in production  
⚠️ HTTP mode should only be used in trusted networks  
⚠️ Consider additional authentication for production deployments

---

## Frequently Asked Questions (FAQ)

### VS Code / GitHub Copilot

**Q: Why are my tools named `mcp_weconnect_*` instead of just `get_vehicles`?**

A: VS Code automatically prefixes MCP tools with `mcp_{servername}_`. Since your server is named `weconnect` in `mcp.json`, all tools become `mcp_weconnect_*`. This is standard behavior and prevents naming conflicts between different MCP servers.

**Q: How do I see which tools are available?**

A: In Copilot Chat, type `/list` to see all available tools. Look for tools starting with `mcp_weconnect_`.

**Q: The MCP server isn't working after installation. What should I check?**

A: Follow these steps:
1. Restart VS Code (`Cmd+Shift+P` → `Developer: Reload Window`)
2. Check if the server is running: `Cmd+Shift+P` → `MCP: List Servers`
3. Check logs: `$PROJECT_DIR/logs/mcp_server.log`
4. Verify trust: You must trust the MCP server when prompted
5. Check VS Code Developer Console: `Help` → `Toggle Developer Tools` → `Console` tab

**Q: Can I rename the server to avoid the `mcp_weconnect_` prefix?**

A: Yes, change the server name in `mcp.json` from `"weconnect"` to something shorter like `"wc"`. However, we recommend keeping it as `weconnect` for clarity.

---

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` and follow the code of conduct.

---

## License

This project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0) — see `LICENSE.txt` for details or visit http://creativecommons.org/licenses/by-sa/4.0/

---

## Credits

This project is built on top of the excellent **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** library by [Till Steinbach](https://github.com/tillsteinbach). CarConnectivity provides the core functionality for connecting to Volkswagen's WeConnect API and handling vehicle data retrieval.

---

## Additional Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)