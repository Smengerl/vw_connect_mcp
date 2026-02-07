
# weconnect_mvp

**MCP Server for Volkswagen Vehicles**  
A developer-focused server that exposes information from VW vehicles via a Model Context Protocol (MCP) interface. This project is designed for integration, automation, and experimentation with connected car data.

---

## Features

- **MCP Server**: Provides a standard MCP interface for accessing vehicle data.
- **Volkswagen Integration**: Connects to VW vehicles using the `carconnectivity` library.
- **Flexible CLI**: Multiple scripts and options for starting the server in different modes.
- **Configurable**: Easily adapt connection and authentication settings via a config file.

---

## Getting Started

### Prerequisites

- Python 3.8+
- VW account credentials (username, password, and optionally a spin)
- (Recommended) Virtual environment

### Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
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

---

## Configuration

The server requires a configuration file (default: `src/config.json`).  
**You must edit this file to provide your VW credentials and adjust settings as needed.**

Example (`src/config.json`):
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
					"username": "your@email.com",
					"password": "your_password",
					"spin": "your_spin",
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
**Do not commit your credentials!**  
Copy and edit `src/config.json` as needed.


---

## Usage

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

### 4. Stopping the Server

If started in the background, stop the server using the script:
```bash
./scripts/stop_server.sh
```

Alternatively, kill the process via PID.
---

## CLI Parameters

The MCP server can be started with several command-line parameters to control its behavior:

| Parameter           | Default                                   | Description                                                      |
|---------------------|-------------------------------------------|------------------------------------------------------------------|
| `config`            | (required)                                | Path to the configuration file                                   |
| `--tokenstorefile`  | `/tmp/tokenstore`                         | Path for the token store file                                    |
| `--log-level`       | (none; uses default if not set)           | Set logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file`        | (stdout only)                             | Path to log file (if not set, logs to stdout only)               |
| `--transport`       | `http`                                    | Transport mode: `http` or `stdio`                                |
| `--port`            | `8667`                                    | Port for HTTP mode                                               |

**Example:**

```bash
python -m weconnect_mcp.cli.mcp_server_cli src/config.json --log-level DEBUG --log-file server.log --transport http --port 8765
```

---

---

## AI Integration

This MCP server can be used with AI assistants like Claude Desktop, VS Code Copilot, and other MCP-compatible tools.

### Quick Start with Claude Desktop

#### Step 1: Generate Configuration Automatically

Generate your configuration for Claude Desktop with the following script:

```bash
cd /path/to/weconnect_mvp
./scripts/get_claude_config.sh
```

The script will:
- ✅ Automatically detect your Python path
- ✅ Generate the complete configuration
- ✅ Show you where to save it

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

### Available Tools for AI

The server provides these tools that AI assistants can use:

- **list_vehicles** - Get all available vehicle IDs
- **get_vehicle_state** - Get complete vehicle state (battery, position, doors, windows, climate, tyres)
- **get_vehicle_doors** - Get door lock and open/closed status
- **get_vehicle_windows** - Get window open/closed status  
- **get_vehicle_tyres** - Get tyre pressure and temperature

### What AI Assistants Can Do

✅ List vehicles and recognize their IDs  
✅ Intelligently interpret vehicle status  
✅ Retrieve specific information (doors, windows, tyres)  
✅ Answer natural questions like "Where is my car?"  
✅ Combine multiple queries for complex answers  

### Troubleshooting AI Integration

#### Common Problems:

**1. "Failed to spawn process: No such file or directory"**

- **Cause:** Claude Desktop cannot find the Python command
- **Solution:** Use full Python path from your venv (the script handles this automatically)
- **Helper script:** `./scripts/get_claude_config.sh`

**2. "Unexpected non-whitespace character after JSON"**

- **Cause:** Log outputs interfere with JSON-RPC communication over stdio
- **Solution:** ✅ Already fixed! All logs are now directed to stderr
- **If it persists:** Check for `print()` statements or third-party library outputs

**3. "TemporaryAuthenticationError: Token could not be fetched"**

- **Cause:** VW WeConnect server temporarily unavailable, incorrect credentials, or account issues
- **Solutions:**
  1. Wait and retry (VW servers can be overloaded)
  2. Check credentials in `src/config.json`
  3. Delete token store: `rm /tmp/tokenstore` and restart
  4. Test VW WeConnect app to ensure account is working

**4. DeprecationWarning about datetime.utcnow()**

- **Cause:** The carconnectivity library uses deprecated Python functions
- **Solution:** This warning is harmless and can be ignored
- **Suppress (optional):** Add `"PYTHONWARNINGS": "ignore::DeprecationWarning"` to env in config

**5. Server starts but tools are not displayed**

- **Diagnosis:** Check Claude Desktop logs (Help → View Logs) for `"tools":[...]`
- **Solutions:**
  - Ensure latest version of code is running
  - Completely restart Claude Desktop (not just close window)
  - Clear cache (uninstall and reinstall Claude Desktop)

**6. Server running but no vehicles found**

- **Symptom:** `list_vehicles` returns empty list
- **Causes:**
  1. Authentication failed (see problem 3)
  2. No vehicles in VW account
  3. API problems (check logs)

**7. Server not responding / Timeout**

- **Cause:** First request after server start can take 10-30 seconds (VW API login)
- **Solutions:**
  - Be patient with first tool call
  - Use token store to avoid re-login
  - Check network (VPN can cause problems)

#### Enable Debug Logs

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

#### Logging Configuration

**Recommended Production Configuration (minimal logs):**

```json
{
  "mcpServers": {
    "weconnect": {
      "command": "/path/to/weconnect_mvp/.venv/bin/python",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "/path/to/config.json"
      ],
      "cwd": "/path/to/weconnect_mvp",
      "env": {
        "PYTHONPATH": "/path/to/weconnect_mvp/src"
      }
    }
  }
}
```

**Debug Configuration (verbose logs):**

```json
{
  "mcpServers": {
    "weconnect": {
      "command": "/path/to/weconnect_mvp/.venv/bin/python",
      "args": [
        "-m",
        "weconnect_mcp.cli.mcp_server_cli",
        "/path/to/config.json",
        "--log-level", "debug",
        "--log-file", "/tmp/weconnect_mcp.log"
      ],
      "cwd": "/path/to/weconnect_mvp",
      "env": {
        "PYTHONPATH": "/path/to/weconnect_mvp/src"
      }
    }
  }
}
```

#### Setup Checklist

- [ ] Virtual environment activated and dependencies installed
- [ ] `src/config.json` configured with valid VW credentials
- [ ] Python path in Claude config correct (full path to `.venv/bin/python`)
- [ ] `PYTHONPATH` set in Claude config
- [ ] Claude Desktop completely restarted
- [ ] In case of problems: Logs enabled and checked
- [ ] Token store directory is writable (`/tmp/`)

#### Known Limitations

1. **First start takes time:** VW API login can take 10-30 seconds
2. **VW API rate limiting:** Too many requests may be blocked
3. **Token expiration:** After a few hours, re-authentication is required
4. **Read-only access:** Currently only data retrieval is possible, no control (opening doors, starting climate control, etc.)

### Integration with VS Code Copilot

For VS Code with GitHub Copilot you can also use the server:

1. Install the MCP extension for VS Code (if available)
2. Configure the server in VS Code settings under `mcp.servers`

### Integration with Other AI Tools

The server uses the standard MCP protocol and should work with all MCP-compatible tools.

#### Cline (VS Code Extension)

Configuration in `.vscode/cline_mcp_settings.json`:

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

### HTTP Mode for API Access

You can also start the server in HTTP mode for programmatic access:

```bash
python -m weconnect_mcp.cli.mcp_server_cli \
    /path/to/config.json \
    --transport http \
    --port 8765
```

The server will then be available at `http://localhost:8765`.

### Example AI Interactions

#### With Claude Desktop:

**You**: "List all my vehicles"  
**Claude** uses the `list_vehicles` tool and shows the results

---

**You**: "What's the status of my car?"  
**Claude** first uses `list_vehicles` to get the vehicle ID, then `get_vehicle_state` for details

---

**You**: "Are my windows closed?"  
**Claude** uses `get_vehicle_windows` and interprets the results

### Additional Resources

For more information:
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Carconnectivity Library](https://github.com/tillsteinbach/CarConnectivity)

**Helper Tools:**
- **Config Generator:** `./scripts/get_claude_config.sh` - Generates correct configuration
- **Test Script:** `./scripts/test_ai_integration.py` - Test AI integration locally
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Carconnectivity Library](https://github.com/tillsteinbach/CarConnectivity)

### Important Security Notes

⚠️ **Never** commit `config.json` with your VW credentials!  
⚠️ Add `src/config.json` to `.gitignore` if not already done  
⚠️ The token store (default: `/tmp/tokenstore`) contains session tokens - keep it secure  
⚠️ Use environment variables for sensitive data in production  
⚠️ HTTP mode should only be used in trusted networks  
⚠️ Consider additional authentication for production deployments

---

## Testing

Run the test suite with:
```bash
./scripts/tests.sh
```
or
```bash
pytest ./tests/test_mcp_server.py --verbose --asyncio-mode=auto
```

---

## Development Notes

- The main package source is under `src/`.
- For development, always use a virtual environment and install in editable mode.
- The CLI scripts activate the virtual environment automatically.

---

## Contributing

Contributions are welcome! Please see `CONTRIBUTING.md` and follow the code of conduct.

---

## License

This project is licensed under the terms of the MIT License. See `LICENSE.txt` for details.

---

