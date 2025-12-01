# Minecraft Language File Tool - AI Agent Instructions

## Project Overview

This is a Python CLI tool for processing Minecraft Education Edition `.lang` files from `.mcworld`/`.mctemplate` archives. It provides text complexity analysis, AI-powered text improvement, and educational quiz generation using the OpenAI-compatible API (supports Ollama, OpenAI, and Azure AI Foundry).

**Dual Interface Architecture:**

- `minecraft_lang_tool/core.py`: Non-interactive core logic with JSON config API (for Regolith filter integration)
- `minecraft_lang_tool.py`: Interactive CLI wrapper using Click (for manual use)

**AI Integration:**

- Uses OpenAI Python library for unified API access
- Supports multiple providers: Ollama (local), OpenAI (cloud), Azure AI Foundry (enterprise)
- Socket-based communication via HTTP API (no subprocess calls)

## Key Architectural Patterns

### 1. Separation of Concerns

- **Core module** (`minecraft_lang_tool/core.py`): Pure logic, no `click` dependencies, accepts JSON strings via `process_from_config()`
- **CLI wrapper** (`minecraft_lang_tool.py`): Interactive menus, user prompts, settings management - all `click`-dependent code lives here
- **Rule**: Never add `click.echo()` or `click.prompt()` to core.py - these belong in minecraft_lang_tool.py

### 2. File Processing Pipeline

```
.mcworld/.mctemplate → extract_archive() → find_lang_files() → [operation methods] → results dict
```

All operations follow this pattern:

1. Accept `Path` objects (not strings) for file paths
2. Return `Dict` with either success data or `{'error': '...'}`
3. Handle both UTF-8 and latin-1 encodings (try/except pattern)

### 3. Text Cleaning Philosophy

The `_clean_text_for_analysis()` method is critical - it removes Minecraft formatting codes (`§[0-9a-fk-or]`), placeholders (`%s`, `{player}`), and technical identifiers while preserving readable text. When updating text processing:

- Filter out values with dots but no spaces (likely technical keys)
- Require at least 2 words after cleaning
- Check cleaned text is ≥30% of original length

## Development Commands

```bash
# Test compilation (no test suite yet)
python -m py_compile minecraft_lang_tool/core.py
python -m py_compile minecraft_lang_tool.py

# Run CLI interactively
python minecraft_lang_tool.py process <file>

# Run with JSON config (Regolith style)
python minecraft_lang_tool.py run --config-json '{"operation":"analyze","input_file":"test.lang"}'

# Test Ollama integration (requires Ollama installed)
ollama pull phi4  # Recommended model for educational content
```

## AI Provider Integration

The tool uses the OpenAI Python library (`openai>=1.0.0`) which provides a unified interface for:

- **Ollama**: Local models via `http://localhost:11434/v1` endpoint
- **OpenAI**: Cloud models via default endpoint or custom base URL
- **Azure AI Foundry**: Enterprise models via Azure endpoint

### Key Implementation Details

1. **Client Initialization**: `MinecraftLangTool.__init__()` creates an `OpenAI` client with configurable `api_key` and `base_url`
2. **API Calls**: Use `client.chat.completions.create()` instead of subprocess calls
3. **Model Discovery**: `get_available_models()` uses `client.models.list()` instead of shell commands
4. **Error Handling**: Unified exception handling for all providers (connection errors, timeouts, rate limits)

### Migration Notes

- **Old**: `subprocess.run(['ollama', 'run', model, prompt])`
- **New**: `client.chat.completions.create(model=model, messages=[...])`
- **Benefits**: Multi-provider support, better error handling, connection pooling, standard API

````

## Critical Conventions

### Encoding Handling Pattern

Always use this try/except pattern for file reading:

```python
try:
    with open(lang_path, 'r', encoding='utf-8') as f:
        # process
except UnicodeDecodeError:
    with open(lang_path, 'r', encoding='latin-1') as f:
        # same processing
````

### Line Parsing Pattern

When parsing `.lang` files (format: `key=value`):

```python
parts = stripped.split('=', 1)  # Limit to 1 split (values may contain =)
if len(parts) != 2:
    continue
key, value = parts
key = key.strip()
value = value.strip()
```

### Filename Sanitization

All output filenames use `sanitize_filename()` - removes spaces and special chars for terminal compatibility:

```python
sanitized_stem = self.sanitize_filename(lang_path_obj.stem)
output_filename = sanitized_stem + f"_improved_age{target_age}" + lang_path_obj.suffix
```

## Integration Points

### Regolith Filter System

The tool is a Regolith filter (Minecraft Bedrock build system). Key files:

- `minecraft_lang_tool/filter.json`: Declares filter metadata
- `minecraft_lang_tool/core.py`: Entry point via `process_from_config(config_json: str)`
- Operations: `strip`, `analyze`, `improve`, `quiz`, `ai_analyze`

### AI Integration

- Uses OpenAI Python library for all AI operations (socket-based, not subprocess)
- Default model: `phi4` (best for educational content when using Ollama)
- Models fetched via `get_available_models()` which uses `client.models.list()`
- All AI features are optional - tool works without AI for basic operations
- Supports Ollama (local), OpenAI (cloud), Azure AI Foundry (enterprise)

## Text Complexity Analysis

Uses 6 readability formulas (Flesch Reading Ease, Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, ARI). Key implementation details:

- Treats each lang entry as a "sentence" (game text is short phrases)
- Prioritizes player-facing prefixes: `death.`, `chat.`, `book.`, `menu.`, etc.
- Syllable counting uses vowel clustering heuristic in `_count_syllables()`
- Grade level is average of all metrics + vocabulary complexity adjustment

## Common Pitfalls

1. **Don't duplicate code cleaning logic** - Use `_clean_text_for_analysis()` consistently
2. **Archive extraction is cached** - Check if `extract_dir.exists()` before extracting
3. **Lang file priority** - `find_lang_files()` returns en_US first, then other English, then others
4. **JSON config in core.py** - Always validate required fields (`operation`, `input_file`) early
5. **Error returns** - Return dict with `'error'` key, not exceptions (except for invalid archives)

## Output Organization

```
improvements/     # Text improvement changelogs
quizzes/         # Generated quiz files + answer keys
.mc_lang_cache/  # Extracted archives (not committed)
```

## When Merging Upstream Changes

This codebase is split from a monolithic `minecraft_lang_tool.py` file. When merging:

1. Interactive/Click methods go to `minecraft_lang_tool.py` (e.g., `select_lang_file`, `create_context_file`)
2. Pure logic goes to `core.py` (e.g., complexity analysis, text cleaning)
3. Update both `analyze_text_complexity()` and its except block when changing parsing logic
4. Test both CLI and JSON config interfaces after changes
