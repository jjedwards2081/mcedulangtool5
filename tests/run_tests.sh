#!/bin/bash
# Test runner script for Linux/Mac
# Sets PYTHONPATH and runs tests

cd "$(dirname "$0")/.."

echo "Setting PYTHONPATH to: $PWD"
export PYTHONPATH="$PWD"

if [ -z "$1" ]; then
    echo "Running all tests..."
    python -m unittest discover -s tests -p "test_*.py" -v
elif [ "$1" == "api" ]; then
    echo "Running API integration tests..."
    python -m unittest tests.test_api_integration -v
elif [ "$1" == "cli" ]; then
    echo "Running CLI option tests..."
    python -m unittest tests.test_cli_options -v
elif [ "$1" == "core" ]; then
    echo "Running core functionality tests..."
    python -m unittest tests.test_core_functionality -v
else
    echo "Unknown test suite: $1"
    echo "Usage: ./run_tests.sh [api|cli|core]"
    exit 1
fi
