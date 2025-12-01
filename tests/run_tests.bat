@echo off
REM Test runner script for Windows
REM Sets PYTHONPATH and runs tests

cd /d "%~dp0.."

echo Setting PYTHONPATH to: %CD%
set PYTHONPATH=%CD%

if "%1"=="" (
    echo Running all tests...
    python -m unittest discover -s tests -p "test_*.py" -v
) else if "%1"=="api" (
    echo Running API integration tests...
    python -m unittest tests.test_api_integration -v
) else if "%1"=="cli" (
    echo Running CLI option tests...
    python -m unittest tests.test_cli_options -v
) else if "%1"=="core" (
    echo Running core functionality tests...
    python -m unittest tests.test_core_functionality -v
) else (
    echo Unknown test suite: %1
    echo Usage: run_tests.bat [api^|cli^|core]
    exit /b 1
)
