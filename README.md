
# weconnect_mvp

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-197%20passing-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Smengerl/weconnect_mvp.git
   cd weconnect_mvp
   ```

2. **Create and activate a virtual environment and install dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

	You can use the convenience scripts to automatically set up everything:
	```bash
	./scripts/setup.sh
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
- Generate the complete configuration for VS Code
- Show you step-by-step instructions

#### Step 2: Add Configuration to VS Code

1. Open VS Code Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux)
2. Type `Preferences: Open User Settings (JSON)` and press Enter
3. Copy the configuration output from the script into your `settings.json`

Alternatively, edit the settings file directly:
```bash
code ~/Library/Application\ Support/Code/User/settings.json  # macOS
```

#### Step 3: Restart and Test

1. **Reload VS Code window**: 
   - Open Command Palette (`Cmd+Shift+P`)
   - Type `Developer: Reload Window`
   - Press Enter

2. **Test it** in GitHub Copilot Chat:
   - Open Copilot Chat panel
   - Type `@weconnect` to verify the server is available
   - Ask questions like:
     - "What vehicles are available?"
     - "Show me my car's battery status"
     - "Are my doors locked?"

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

### VS Code Copilot Integration

For VS Code with GitHub Copilot:

1. Install the MCP extension for VS Code (if available)
2. Configure the server in VS Code settings under `mcp.servers`

---

### Other AI Tools (Cline)

The server uses the standard MCP protocol and works with all MCP-compatible tools.

**Cline (VS Code Extension)** - Configuration in `.vscode/cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "weconnect": {
      "command": "python",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "/path/to/your/config.json"
      ],
      "env": {
        "PYTHONPATH": "/path/to/weconnect_mvp/src"
      }
    }
  }
}
```

---

### HTTP Mode for API Access

You can also start the server in HTTP mode for programmatic access:

```bash
python -m weconnect_mcp.cli.mcp_server_cli \
    /path/to/config.json \
    --transport http \
    --port 8765
```

The server will then be available at `http://localhost:8765`.


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

### Security Best Practices

⚠️ **Never** commit `config.json` with your VW credentials!  
⚠️ Add `src/config.json` to `.gitignore` if not already done  
⚠️ The token store (default: `/tmp/tokenstore`) contains session tokens - keep it secure  
⚠️ Use environment variables for sensitive data in production  
⚠️ HTTP mode should only be used in trusted networks  
⚠️ Consider additional authentication for production deployments

---

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` and follow the code of conduct.

---

## License

This project is licensed under the terms of the MIT License. See `LICENSE.txt` for details.

---

## Credits

This project is built on top of the excellent **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** library by [Till Steinbach](https://github.com/tillsteinbach). CarConnectivity provides the core functionality for connecting to Volkswagen's WeConnect API and handling vehicle data retrieval.

---

## Additional Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)