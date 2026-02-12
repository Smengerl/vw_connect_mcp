@echo off
REM Stop background server started with start_server_bg.bat
REM Note: Windows batch scripts have limited process management capabilities
REM Usage: scripts\stop_server_bg.bat

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

if "%LOG_DIR%"=="" set "LOG_DIR=%ROOT_DIR%\logs"
if "%PID_FILE%"=="" set "PID_FILE=%LOG_DIR%\server.pid"

echo Stopping server...
echo.

REM Note: Windows doesn't have the same PID file functionality as Unix
REM The start_server_bg.bat script cannot reliably capture and save PIDs

echo To stop the background server on Windows, use one of these methods:
echo.
echo 1. Find the process in Task Manager:
echo    - Press Ctrl+Shift+Esc to open Task Manager
echo    - Look for "python.exe" running "mcp_server_cli.py"
echo    - Right-click and select "End Task"
echo.
echo 2. Use tasklist and taskkill commands:
echo    - Find the process:
echo      tasklist /FI "IMAGENAME eq python.exe" /V
echo    - Look for the process running mcp_server_cli.py
echo    - Kill by PID: taskkill /F /PID [PID]
echo.
echo 3. Kill all python.exe processes (WARNING: kills ALL Python processes):
echo    taskkill /F /IM python.exe
echo.
echo 4. Use PowerShell (more precise):
echo    Get-Process python ^| Where-Object {$_.CommandLine -like "*mcp_server_cli*"} ^| Stop-Process -Force
echo.

REM Try to find and display running Python processes for convenience
echo Current Python processes:
tasklist /FI "IMAGENAME eq python.exe" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo No Python processes found.
)

echo.
echo Tip: For better process management on Windows, consider running the server
echo in foreground mode with scripts\start_server_fg.bat instead.

exit /b 0
