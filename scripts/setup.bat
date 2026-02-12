@echo off
REM Create or recreate the .venv virtual environment and install from requirements.txt
setlocal enabledelayedexpansion

REM Get the script directory and set ROOT_DIR (one level up)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%ROOT_DIR%\.venv"
set "REQ_FILE=%ROOT_DIR%\requirements.txt"

echo Repository root: %ROOT_DIR%

REM Check for Python installation
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_BIN=python"
) else (
    where py >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PYTHON_BIN=py"
    ) else (
        echo Error: Python not found on PATH. Please install Python 3.8+ and retry. >&2
        exit /b 1
    )
)

REM Check if requirements.txt exists
if not exist "%REQ_FILE%" (
    echo Error: requirements.txt not found at %REQ_FILE% >&2
    exit /b 1
)

echo Using Python: %PYTHON_BIN%
%PYTHON_BIN% --version

REM Check if venv already exists
if exist "%VENV_DIR%" (
    set /p "yn=.venv exists. Remove and recreate? [y/N]: "
    if /i "!yn!"=="y" (
        echo Removing existing .venv...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo Leaving existing .venv in place. To force recreation, remove %VENV_DIR% and rerun.
        exit /b 0
    )
)

echo Creating virtualenv at %VENV_DIR%
%PYTHON_BIN% -m venv "%VENV_DIR%"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment >&2
    exit /b 1
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

echo Upgrading pip inside venv...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to upgrade pip >&2
    exit /b 1
)

echo Installing requirements from %REQ_FILE%
"%VENV_PIP%" install -r "%REQ_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install requirements >&2
    exit /b 1
)

REM Setup configuration file
set "CONFIG_EXAMPLE=%ROOT_DIR%\src\config.example.json"
set "CONFIG_FILE=%ROOT_DIR%\src\config.json"

if not exist "%CONFIG_FILE%" (
    if exist "%CONFIG_EXAMPLE%" (
        echo.
        echo Creating config.json from example...
        copy "%CONFIG_EXAMPLE%" "%CONFIG_FILE%" >nul
        echo.
        echo ========================================================================
        echo   WARNING: Edit src\config.json with your VW WeConnect credentials!
        echo   - username: Your VW account email
        echo   - password: Your VW account password
        echo   - spin: Your VW S-PIN (4 digits)
        echo ========================================================================
    ) else (
        echo Warning: config.example.json not found, skipping config file creation >&2
    )
) else (
    echo Config file already exists at %CONFIG_FILE% (not overwriting)
)

echo.
echo Done! To activate the venv, run:
echo   %VENV_DIR%\Scripts\activate.bat
echo Or run scripts via the venv python directly, e.g.:
echo   %VENV_PYTHON% -m pytest
echo   %VENV_PYTHON% -m weconnect_mcp.cli.mcp_server_cli src\config.json

exit /b 0
