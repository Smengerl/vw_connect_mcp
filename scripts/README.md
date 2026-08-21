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

## Configuring Secrets

The server has two backends (`--backend tibber` (default) / `carconnectivity`,
see the main [README.md](../README.md#choosing-a-backend)), and each has its
own credential source, resolved in this order — **environment variables
override a credentials file** when both are present:

| Backend | File (gitignored) | Env vars |
|---|---|---|
| `tibber` (default) | `src/tibber_config.json` (template: `src/tibber_config.example.json`) | `TIBBER_CLIENT_ID`, `TIBBER_CLIENT_SECRET`, `TIBBER_REDIRECT_URI`, `TIBBER_TOKEN_PATH` |
| `carconnectivity` | `src/config.json` (template: `src/config.example.json`) | `VW_USERNAME`, `VW_PASSWORD`, `VW_SPIN` |

**Use the file for local/desktop clients** (Claude Desktop, VS Code Copilot,
Microsoft Copilot Desktop) — those launch the server with their own
environment, not your shell's, so anything set via `export` never reaches
it. The `create_*_config.sh` scripts already generate configs pointing at
the credentials file for exactly this reason; no secrets end up in the
generated `claude_desktop_config.json` / `mcp.json`.

**Use environment variables for Docker/Railway** — see the main README's
[Cloud Deployment](../README.md#cloud-deployment) section.

The `tibber` backend additionally needs a one-time interactive login before
first use (a browser step that can't run inside the MCP server process
itself):

```bash
python -m weconnect_mcp.cli.tibber_login_cli
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
Start the MCP server in foreground (with console output). Defaults to the
**tibber** backend (no config file needed); pass extra `mcp_server_cli` flags
after the config argument to change that.

```bash
./scripts/start_server_fg.sh

# VW-direct backend instead (currently blocked by VW, see README.md warning)
./scripts/start_server_fg.sh src/config.json --backend carconnectivity
```

---

### start_server_bg.sh
Start the MCP server in background (with log file output). Same defaults and
flag-forwarding as `start_server_fg.sh` above.

```bash
./scripts/start_server_bg.sh

# VW-direct backend instead
./scripts/start_server_bg.sh src/config.json --backend carconnectivity
```

---

### start_server_http.sh
Start the MCP server in HTTP mode with API-key authentication (foreground).
Reads `.env` from the project root if present. Defaults to the **tibber**
backend.

```bash
# tibber backend (default), reads TIBBER_CLIENT_ID/SECRET from env or
# src/tibber_config.json
MCP_API_KEY=secret ./scripts/start_server_http.sh 8089

# VW-direct backend instead (currently blocked by VW, see README.md warning)
MCP_API_KEY=secret VW_USERNAME=... VW_PASSWORD=... VW_SPIN=... \
  ./scripts/start_server_http.sh 8089 carconnectivity
```

**Required:** `MCP_API_KEY` always. For the tibber backend: either
`TIBBER_CLIENT_ID`/`TIBBER_CLIENT_SECRET` env vars, or `src/tibber_config.json`
(see [Configuring Secrets](#configuring-secrets) below). For the
carconnectivity backend: `VW_USERNAME`/`VW_PASSWORD`/`VW_SPIN`.

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
Generate MCP configuration for Claude Desktop. Points the generated config at
`src/tibber_config.json` with `--backend tibber` explicit — see
[Configuring Secrets](#configuring-secrets) below for why a file is used
here instead of environment variables. Prints setup instructions if that
file doesn't exist yet.

```bash
./scripts/create_claude_config.sh
```

**Output locations:**
- Configuration saved to `tmp/claude_desktop/claude_desktop_config.json`
- On **macOS**: Copy to `~/Library/Application Support/Claude/claude_desktop_config.json`
- On **Windows**: Copy to `%APPDATA%\Claude\claude_desktop_config.json`
- On **Linux**: Varies by distribution

To use the VW-direct backend instead, edit the generated config: replace the
`tibber_config.json` path with `src/config.json` and `"tibber"` with
`"carconnectivity"`.

---

### create_github_copilot_config.sh
Generate MCP configuration for GitHub Copilot (VS Code). Same
`src/tibber_config.json` + `--backend tibber` default and setup-instructions
behavior as `create_claude_config.sh` above.

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
Generate MCP configuration for Microsoft Copilot Desktop. Same
`src/tibber_config.json` + `--backend tibber` default and setup-instructions
behavior as `create_claude_config.sh` above.

```bash
./scripts/create_copilot_desktop_config.sh
```

**Output locations:**
- Configuration saved to `tmp/copilot_desktop/mcp.json`
- On **macOS**: `~/Library/Application Support/Microsoft/Copilot/mcp.json`
- On **Windows**: `%APPDATA%\Microsoft\Copilot\mcp.json`

---

### test_mcp_auth.sh
Run a full MCP OAuth flow against a running server and validate authenticated access via `tools/list`.

```bash
# Default host (=localhost:8089)
./scripts/test_mcp_auth.sh

# Test a custom host
./scripts/test_mcp_auth.sh http://localhost:8089
```

**Requirements:**
- Running MCP server (default: `http://localhost:8089`)
- `.env` file in project root with `MCP_API_KEY=...`
- Existing `.venv` (script activates it automatically)
- `curl` available in your shell

**What it does (end-to-end):**
1. Checks `GET /health`
2. Loads OAuth metadata from `/.well-known/oauth-authorization-server`
3. Registers a test client (`client_credentials`)
4. Requests an access token from `token_endpoint`
5. Calls MCP `tools/list` with `Authorization: Bearer <token>`

**Typical use case:**
- Quick smoke test after local startup or deployment changes
- Verify OAuth + MCP endpoint wiring before configuring external clients (VS Code, Claude, Copilot Desktop)

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
