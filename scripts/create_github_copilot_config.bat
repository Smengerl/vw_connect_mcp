@echo off
REM Script to help configure GitHub Copilot for WeConnect MCP Server

setlocal enabledelayedexpansion

echo Finding Python paths for GitHub Copilot configuration...
echo.

REM Auto-detect project directory (script is in scripts\ subdirectory)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

echo Project directory: %PROJECT_DIR%
echo.

if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo Virtual environment found!
    echo.
    echo Python executable in venv:
    dir "%PROJECT_DIR%\.venv\Scripts\python.exe" 2>nul
    echo.
    echo Use this path in your GitHub Copilot config:
    echo    "command": "%PROJECT_DIR%\.venv\Scripts\python.exe"
    echo.
    set "PYTHON_PATH=%PROJECT_DIR%\.venv\Scripts\python.exe"
) else (
    echo No virtual environment found at %PROJECT_DIR%\.venv
    echo.
    echo Looking for system Python...
    where python >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=*" %%i in ('where python') do set "PYTHON_PATH=%%i" & goto :found_python
    )
    where py >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=*" %%i in ('where py') do set "PYTHON_PATH=%%i" & goto :found_python
    )
    echo No Python found!
    exit /b 1
)

:found_python
echo Found Python at: %PYTHON_PATH%
echo.

REM Create tmp directory if it doesn't exist
if not exist "%PROJECT_DIR%\tmp\github_copilot_vscode" mkdir "%PROJECT_DIR%\tmp\github_copilot_vscode"

REM Save configuration to tmp file
set "CONFIG_FILE=%PROJECT_DIR%\tmp\github_copilot_vscode\settings.json"

REM Write the JSON configuration
(
echo {
echo   "github.copilot.chat.mcp": {
echo     "enabled": true
echo   },
echo   "github.copilot.chat.mcpServers": {
echo     "weconnect": {
echo       "command": "%PYTHON_PATH:\=\\%",
echo       "args": [
echo         "-m",
echo         "weconnect_mcp.cli.mcp_server_cli",
echo         "%PROJECT_DIR:\=\\%\\src\\config.json"
echo       ],
echo       "cwd": "%PROJECT_DIR:\=\\%",
echo       "env": {
echo         "PYTHONPATH": "%PROJECT_DIR:\=\\%\\src"
echo       }
echo     }
echo   }
echo }
) > "%CONFIG_FILE%"

echo.
echo Configuration saved to:
echo    %CONFIG_FILE%
echo.
echo To configure GitHub Copilot in VS Code:
echo.
echo 1. Open VS Code Settings (JSON):
echo    - Press Ctrl+Shift+P
echo    - Type 'Preferences: Open User Settings (JSON)'
echo    - Press Enter
echo.
echo 2. Add the configuration above to your settings.json
echo    (You can copy from %CONFIG_FILE%)
echo.
echo 3. Restart VS Code or reload the window:
echo    - Press Ctrl+Shift+P
echo    - Type 'Developer: Reload Window'
echo    - Press Enter
echo.
echo 4. Verify MCP server is running:
echo    - Open GitHub Copilot Chat
echo    - Type '@weconnect' to see if the server is available
echo.
echo Alternative: Direct file edit
echo    code "%%APPDATA%%\Code\User\settings.json"
echo.

exit /b 0
