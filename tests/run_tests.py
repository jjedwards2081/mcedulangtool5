#!/usr/bin/env python3
"""
Test runner for Minecraft Language File Tool

Run all tests or specific test suites.

Usage:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py api                # Run API tests only
    python tests/run_tests.py cli                # Run CLI tests only
    python tests/run_tests.py core               # Run core tests only
    python tests/run_tests.py -v                 # Verbose output
"""

import sys
import unittest
from pathlib import Path


def run_all_tests(verbosity=2):
    """Run all test suites."""
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    try:
        loader = unittest.TestLoader()
        suite = loader.discover('tests', pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    finally:
        os.chdir(original_dir)


def run_specific_suite(suite_name, verbosity=2):
    """Run a specific test suite."""
    suite_map = {
        'api': 'test_api_integration',
        'cli': 'test_cli_options',
        'core': 'test_core_functionality'
    }
    
    if suite_name not in suite_map:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_map.keys())}")
        return False
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os
    original_dir = os.getcwd()
    os.chdir(project_root)
    
    try:
        module_name = suite_map[suite_name]
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.{module_name}')
        
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    finally:
        os.chdir(original_dir)


def main():
    """Main entry point."""
    args = sys.argv[1:]
    verbosity = 2
    
    # Check for verbose flag
    if '-v' in args or '--verbose' in args:
        verbosity = 2
        args = [a for a in args if a not in ['-v', '--verbose']]
    elif '-q' in args or '--quiet' in args:
        verbosity = 0
        args = [a for a in args if a not in ['-q', '--quiet']]
    
    if not args:
        # Run all tests
        print("Running all tests...\n")
        success = run_all_tests(verbosity)
    else:
        # Run specific suite
        suite_name = args[0]
        print(f"Running {suite_name} tests...\n")
        success = run_specific_suite(suite_name, verbosity)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
