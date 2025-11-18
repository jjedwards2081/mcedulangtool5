# Test Suite Documentation

This directory contains the comprehensive test suite for the Minecraft Language File Tool.

## Structure

```
tests/
├── __init__.py                     # Package initialization
├── README.md                       # This file
├── run_tests.py                    # Test runner script
├── test_api_integration.py         # API integration tests
├── test_cli_options.py             # CLI option tests
└── test_core_functionality.py      # Core functionality tests
```

## Test Categories

### 1. API Integration Tests (`test_api_integration.py`)

Tests the OpenAI library integration with multiple providers:

- **TestAPIInitialization**: Client initialization with different configurations
- **TestModelListing**: Model discovery with mocked responses
- **TestTextImprovement**: Text improvement with mocked API calls
- **TestQuizGeneration**: Quiz generation with mocked responses
- **TestAIAnalysis**: AI content analysis
- **TestJSONConfiguration**: JSON config processing

### 2. CLI Option Tests (`test_cli_options.py`)

Tests command-line interface functionality:

- **TestCLIHelp**: Help text and documentation
- **TestCLIOptionParsing**: Option parsing validation
- **TestCLICommands**: Command execution
- **TestCLIIntegration**: End-to-end CLI tests

### 3. Core Functionality Tests (`test_core_functionality.py`)

Tests non-AI core features:

- **TestArchiveExtraction**: .mcworld/.mctemplate extraction
- **TestLangFileDiscovery**: Lang file finding and prioritization
- **TestTextComplexityAnalysis**: Readability analysis
- **TestTextStripping**: Comment/empty line removal
- **TestFilenameSanitization**: Filename cleaning

## Running Tests

### Easiest Way (Recommended)

```bash
# Windows
tests\run_tests.bat          # Run all tests
tests\run_tests.bat api      # Run API tests only
tests\run_tests.bat cli      # Run CLI tests only
tests\run_tests.bat core     # Run core tests only

# Linux/Mac
chmod +x tests/run_tests.sh
./tests/run_tests.sh         # Run all tests
./tests/run_tests.sh api     # Run API tests only
./tests/run_tests.sh cli     # Run CLI tests only
./tests/run_tests.sh core    # Run core tests only
```

### Manual Method

```bash
# PowerShell (Windows)
$env:PYTHONPATH = "c:\path\to\mcedulangtool5"
python -m unittest discover -s tests -p "test_*.py" -v

# Bash/Linux/Mac
PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py" -v

# Using pytest (if installed)
pytest
```

### Run Specific Test Suite

```bash
# PowerShell
$env:PYTHONPATH = "c:\path\to\mcedulangtool5"

# API integration tests only
python -m unittest tests.test_api_integration -v

# CLI tests only
python -m unittest tests.test_cli_options -v

# Core functionality tests only
python -m unittest tests.test_core_functionality -v
```

### Run Specific Test Class

```bash
# PowerShell
$env:PYTHONPATH = "c:\path\to\mcedulangtool5"
python -m unittest tests.test_api_integration.TestAPIInitialization -v

# Using pytest
pytest tests/test_api_integration.py::TestAPIInitialization
```

### Run Specific Test Method

```bash
# Using unittest
python -m unittest tests.test_api_integration.TestAPIInitialization.test_default_initialization

# Using pytest
pytest tests/test_api_integration.py::TestAPIInitialization::test_default_initialization
```

### Verbose Output

```bash
# Using unittest
python -m unittest discover tests -v

# Using test runner
python tests/run_tests.py -v

# Using pytest
pytest -v
```

## Writing New Tests

### Test Structure

Each test file should follow this structure:

```python
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from minecraft_lang_tool.core import MinecraftLangTool


class TestFeatureName(unittest.TestCase):
    """Test description."""

    def setUp(self):
        """Set up test fixtures before each test."""
        pass

    def tearDown(self):
        """Clean up after each test."""
        pass

    def test_something(self):
        """Test description."""
        # Arrange
        tool = MinecraftLangTool()

        # Act
        result = tool.some_method()

        # Assert
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use `setUp()` and `tearDown()` to clean up resources
3. **Mocking**: Use `unittest.mock` to mock external dependencies (API calls)
4. **Descriptive Names**: Test names should describe what they test
5. **Documentation**: Use docstrings to explain test purpose
6. **Fixtures**: Create test fixtures in `setUp()`, clean in `tearDown()`

### Mocking API Calls

Example of mocking OpenAI API calls:

```python
from unittest.mock import MagicMock, patch

@patch('minecraft_lang_tool.core.OpenAI')
def test_api_call(self, mock_openai):
    """Test API call with mocked response."""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # Test
    tool = MinecraftLangTool()
    result = tool.some_ai_method()

    # Assert
    self.assertNotIn('error', result)
```

## Test Coverage

To check test coverage:

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
# Then open htmlcov/index.html
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: python tests/run_tests.py
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running tests from the project root:

```bash
cd /path/to/mcedulangtool5
python -m unittest discover tests
```

### Fixture Cleanup Issues

If tests leave behind test fixtures:

```bash
# Clean up manually
rm -rf test_fixtures
rm -rf test_cache
rm -rf .mc_lang_cache
```

### Mocking Issues

If mocks aren't working, ensure:

1. You're patching the right module path
2. The patch decorator is applied to the test method
3. The mock object is passed as a parameter to the test

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass before committing
3. Add docstrings to test methods
4. Update this README if adding new test categories

## Test Metrics

Current test coverage:

- **API Integration**: 8 test classes, 20+ test methods
- **CLI Options**: 4 test classes, 12+ test methods
- **Core Functionality**: 5 test classes, 15+ test methods
- **Total**: 17+ test classes, 47+ test methods

Target coverage: >80% of core functionality
