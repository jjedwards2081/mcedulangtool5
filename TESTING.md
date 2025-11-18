# Quick Test Guide

## Run Tests (Easiest)

```bash
# Windows - run from project root
tests\run_tests.bat              # All tests
tests\run_tests.bat api          # API tests only
tests\run_tests.bat cli          # CLI tests only
tests\run_tests.bat core         # Core tests only

# Linux/Mac
chmod +x tests/run_tests.sh
./tests/run_tests.sh             # All tests
./tests/run_tests.sh api         # API tests only
./tests/run_tests.sh cli         # CLI tests only
./tests/run_tests.sh core        # Core tests only
```

## Test Structure

```
tests/
├── test_api_integration.py     # 17 tests - OpenAI library, mocking, JSON config
├── test_cli_options.py         # 6 tests - CLI parsing, help text
├── test_core_functionality.py  # 13 tests - Archive extraction, text analysis
├── run_tests.py               # Python test runner
├── run_tests.bat              # Windows batch script
├── run_tests.sh               # Linux/Mac shell script
├── README.md                  # Detailed documentation
└── __init__.py                # Package marker
```

## Test Coverage

✅ 36 tests total - ALL PASSING

- **API Integration** (17): Ollama/OpenAI/Azure configuration, model listing, text improvement, quiz generation
- **CLI Options** (6): Help text, API key/base URL passing
- **Core Functionality** (13): Archive extraction, lang file discovery, text analysis

## What's Tested

✅ Socket-based OpenAI library (not subprocess)  
✅ Multi-provider support (Ollama, OpenAI, Azure)  
✅ CLI API configuration options (--api-key, --base-url)  
✅ JSON configuration with API settings  
✅ Archive extraction (.mcworld/.mctemplate)  
✅ Text complexity analysis (6 readability metrics)  
✅ All core features remain functional

## Requirements

- Python 3.11+
- Dependencies: `click`, `openai` (both already in requirements.txt)
- No additional test dependencies needed!

## Notes

- Tests use `unittest.mock` - no real API calls made
- PYTHONPATH automatically set by batch/shell scripts
- Tests validate the migration from subprocess to OpenAI library
- All existing functionality preserved

## Documentation

See `tests/README.md` for detailed information about:

- Test architecture
- Mocking strategies
- Adding new tests
- Best practices
- Troubleshooting
