@echo off
REM Send commands to VW vehicles using CarConnectivityAdapter

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

REM Print usage if no arguments or help requested
if "%~1"=="" goto :usage
if "%~1"=="-h" goto :usage
if "%~1"=="--help" goto :usage
goto :main

:usage
echo Send commands to VW vehicles using CarConnectivityAdapter
echo.
echo Usage: %~nx0 ^<vehicle_id^> ^<command^>
echo.
echo Available Commands:
echo   Lock/Unlock:
echo     lock, unlock
echo.
echo   Climatization:
echo     start_climatization, stop_climatization
echo.
echo   Charging (BEV/PHEV only):
echo     start_charging, stop_charging
echo.
echo   Lights/Horn:
echo     flash_lights, honk_and_flash
echo.
echo   Window Heating:
echo     start_window_heating, stop_window_heating
echo.
echo Examples:
echo   %~nx0 ID7 lock
echo   %~nx0 Golf unlock
echo   %~nx0 ID7 start_climatization
echo   %~nx0 ID7 start_charging
echo.
exit /b 0

:main
REM Check if venv exists
if not exist "%ROOT_DIR%\.venv\Scripts\python.exe" (
    echo Error: Virtual environment not found. Please run scripts\setup.bat first. >&2
    exit /b 1
)

REM Activate virtualenv
echo Activating virtualenv...
call "%SCRIPT_DIR%activate_venv.bat"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment >&2
    exit /b 1
)

REM Run the Python script with all arguments
python "%ROOT_DIR%\scripts\vehicle_command.py" %*

exit /b %ERRORLEVEL%
