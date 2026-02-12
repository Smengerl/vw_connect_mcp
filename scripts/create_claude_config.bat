@echo off
REM Script to help find the correct Python path for Claude Desktop config

setlocal enabledelayedexpansion

echo Finding Python paths for Claude Desktop configuration...
echo.

REM Auto-detect project directory (script is in scripts\ subdirectory)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

echo Project directory: %PROJECT_DIR%
echo.

REM Check if virtual environment exists
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo Virtual environment found!
    echo.
    echo Python executable in venv:
    dir "%PROJECT_DIR%\.venv\Scripts\python.exe" 2>nul
    echo.
    echo Use this path in your Claude Desktop config:
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
if not exist "%PROJECT_DIR%\tmp\claude_desktop" mkdir "%PROJECT_DIR%\tmp\claude_desktop"

REM Save configuration to tmp file
set "CONFIG_FILE=%PROJECT_DIR%\tmp\claude_desktop\claude_desktop_config.json"

REM Write the JSON configuration
(
echo {
echo   "mcpServers": {
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
echo Copy the configuration to Claude Desktop:
echo    Windows: %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo You can either:
echo 1. Copy from the file above:
echo    copy "%CONFIG_FILE%" "%%APPDATA%%\Claude\claude_desktop_config.json"
echo.
echo 2. Or manually copy the JSON content from the file
echo.
echo To edit the Claude config file directly:
echo    notepad "%%APPDATA%%\Claude\claude_desktop_config.json"
echo.
echo After editing, restart Claude Desktop completely!

exit /b 0
