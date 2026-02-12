@echo off
REM Activate repository's virtualenv Python
REM This script checks if the venv exists and can be called from other scripts.

setlocal enabledelayedexpansion

REM Get the script directory and set ROOT_DIR (one level up)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "VENV_PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Error: Virtualenv python not found at %VENV_PYTHON% >&2
    echo Please run scripts\setup.bat first to create the virtual environment. >&2
    exit /b 1
)

REM Activate the virtual environment
call "%ROOT_DIR%\.venv\Scripts\activate.bat"

exit /b 0
