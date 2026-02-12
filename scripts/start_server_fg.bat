@echo off
REM Start the weconnect_mvp MCP server in foreground with logs.
REM Usage: scripts\start_server_fg.bat [config.json] [additional args...]
REM Defaults: config.json -> src\config.json

setlocal enabledelayedexpansion

REM Get the script directory and set ROOT_DIR (one level up)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

REM Set default config or use first argument
if "%~1"=="" (
    set "CONFIG=%ROOT_DIR%\src\config.json"
    set "EXTRA_ARGS="
) else (
    set "CONFIG=%~1"
    set "EXTRA_ARGS="
    shift
    :parse_args
    if not "%~1"=="" (
        set "EXTRA_ARGS=!EXTRA_ARGS! %~1"
        shift
        goto :parse_args
    )
)

REM Set log directory
if "%LOG_DIR%"=="" set "LOG_DIR=%ROOT_DIR%\logs"

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Check if venv exists
if not exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    echo Error: Virtual environment not found. Please run scripts\setup.bat first. >&2
    exit /b 1
)

echo Activating virtualenv...
call "%SCRIPT_DIR%activate_venv.bat"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment >&2
    exit /b 1
)

REM Check if config file exists
if not exist "%CONFIG%" (
    echo Error: Config file not found at %CONFIG% >&2
    echo Please create src\config.json with your VW credentials. >&2
    exit /b 1
)

echo Starting server (foreground) with config=%CONFIG%
python "%ROOT_DIR%\src\weconnect_mcp\cli\mcp_server_cli.py" "%CONFIG%" --tokenstorefile "%TEMP%\tokenstore" --log-level DEBUG %EXTRA_ARGS%

exit /b %ERRORLEVEL%
