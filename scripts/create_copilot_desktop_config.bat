@echo off
REM Script to generate a valid mcp.json for Microsoft Copilot Desktop (Windows)
REM for the WeConnect MCP Server

setlocal enabledelayedexpansion

echo Generating Copilot Desktop MCP configuration...
echo.

REM Detect project directory (script is inside scripts\)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

echo Project directory: %PROJECT_DIR%
echo.

REM Detect Python
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_PATH=%PROJECT_DIR%\.venv\Scripts\python.exe"
    echo Using virtualenv Python: !PYTHON_PATH!
) else (
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
echo Using Python: %PYTHON_PATH%
echo.

REM Create tmp directory if it doesn't exist
if not exist "%PROJECT_DIR%\tmp\copilot_desktop" mkdir "%PROJECT_DIR%\tmp\copilot_desktop"

REM Save configuration to tmp file
set "CONFIG_FILE=%PROJECT_DIR%\tmp\copilot_desktop\mcp.json"

REM Write the JSON configuration
(
echo {
echo   "servers": {
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
echo Copy the configuration to Microsoft Copilot Desktop:
echo    %%APPDATA%%\Microsoft\Copilot\mcp.json
echo.
echo You can either:
echo 1. Copy from the file above:
echo    if not exist "%%APPDATA%%\Microsoft\Copilot" mkdir "%%APPDATA%%\Microsoft\Copilot"
echo    copy "%CONFIG_FILE%" "%%APPDATA%%\Microsoft\Copilot\mcp.json"
echo.
echo 2. Or manually copy the JSON content from the file
echo.
echo To edit the Copilot Desktop config file directly:
echo    notepad "%%APPDATA%%\Microsoft\Copilot\mcp.json"
echo.
echo After editing, restart Microsoft Copilot Desktop completely!
echo.

exit /b 0
