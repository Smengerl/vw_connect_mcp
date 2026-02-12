@echo off
REM Run unit tests for weconnect_mvp
setlocal enabledelayedexpansion

REM Get the script directory and set ROOT_DIR (one level up)
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

REM Print usage information
if "%~1"=="-h" goto :usage
if "%~1"=="--help" goto :usage
goto :main

:usage
echo Usage: %~nx0 [OPTIONS]
echo.
echo Run pytest on all tests in tests\ directory and subdirectories.
echo.
echo Options:
echo   --skip-slow       Skip tests marked as 'slow' or 'real_api'
echo   -v, --verbose     Run pytest in verbose mode
echo   -h, --help        Show this help message
echo.
echo Examples:
echo   %~nx0                    # Run all tests (including slow real API tests)
echo   %~nx0 --skip-slow        # Run only fast mock tests
echo   %~nx0 --skip-slow -v     # Run fast tests with verbose output
exit /b 0

:main
REM Parse arguments
set "PYTEST_VERBOSE="
set "PYTEST_LOG="
set "PYTEST_MARKERS="
set "SKIP_SLOW=false"
set "EXTRA_ARGS="

:parse_loop
if "%~1"=="" goto :done_parsing
if /i "%~1"=="--skip-slow" (
    set "SKIP_SLOW=true"
    shift
    goto :parse_loop
)
if /i "%~1"=="-v" (
    set "PYTEST_VERBOSE=--verbose"
    set "PYTEST_LOG=-o log_cli_level=INFO --log-cli-level=INFO"
    shift
    goto :parse_loop
)
if /i "%~1"=="--verbose" (
    set "PYTEST_VERBOSE=--verbose"
    set "PYTEST_LOG=-o log_cli_level=INFO --log-cli-level=INFO"
    shift
    goto :parse_loop
)
REM Collect any remaining arguments
set "EXTRA_ARGS=!EXTRA_ARGS! %~1"
shift
goto :parse_loop

:done_parsing

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

REM Set marker expression to skip slow tests if requested
if "%SKIP_SLOW%"=="true" (
    set "PYTEST_MARKERS=-m "not real_api and not slow""
    echo Running fast tests only (skipping slow/real_api tests)
) else (
    echo Running ALL tests (including slow real API tests)
)

echo Running tests from: %ROOT_DIR%\tests\

REM Run pytest on entire tests directory
pytest "%ROOT_DIR%\tests\" %PYTEST_VERBOSE% %PYTEST_LOG% %PYTEST_MARKERS% %EXTRA_ARGS%

if %ERRORLEVEL% EQU 0 (
    echo Tests completed successfully
) else (
    echo Tests failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

exit /b 0
