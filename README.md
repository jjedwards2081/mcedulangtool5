# Minecraft Language File Tool

A Python CLI application for extracting and processing Minecraft `.lang` files from `.mcworld` and `.mctemplate` archives.

## Features

- **Extract archives**: Automatically extracts `.mcworld` and `.mctemplate` files (which are ZIP-based)
- **Find lang files**: Locates all `.lang` files and prioritizes en_US English files
- **Interactive selection**: Preview and select the correct lang file with confirmation
- **Smart caching**: Stores extracted files to avoid reprocessing
- **Text complexity analysis**: Comprehensive readability assessment with age/grade recommendations
- **Text stripping**: Remove non-player-facing text to keep only player-visible strings
- **Browse Downloads**: Quick access to files in your Downloads folder
- **Multiple operations**: View contents, get statistics, and more

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Process a Minecraft archive or lang file:

```bash
python minecraft_lang_tool.py process <file>
```

Examples:
```bash
# Process a .mcworld file
python minecraft_lang_tool.py process myworld.mcworld

# Process a .mctemplate file
python minecraft_lang_tool.py process mytemplate.mctemplate

# Process a .lang file directly
python minecraft_lang_tool.py process en_US.lang
```

### Clear the extraction cache:

```bash
python minecraft_lang_tool.py clear-cache
```

### Custom cache directory:

```bash
python minecraft_lang_tool.py process myworld.mcworld --cache-dir custom_cache
```

## Operations

Once you've selected a lang file, you can:

1. **Strip non-player-facing text**: Removes internal/debug strings, keeping only player-visible content
   - Output is saved as `<filename>_player_only.lang`
   - Shows how many lines were removed
   - Preview the result

2. **Text complexity analysis**: Comprehensive readability assessment
   - Multiple readability metrics (Flesch-Kincaid, Gunning Fog, SMOG, etc.)
   - Age and grade level recommendations
   - Vocabulary complexity breakdown
   - Designed for English (en_US) text
   - Automatically filters technical content
   - Optional detailed report export

3. **AI content analysis** (using Ollama): AI-powered game content summary
   - Automatically detects available Ollama models on your system
   - Analyzes player-facing text to understand game content
   - Provides summary of game theme, features, and target audience
   - Identifies educational focus or unique aspects
   - Saves analysis reports
   - Requires Ollama to be installed locally

4. **View full file contents**: Display the entire lang file with pagination

5. **Get file statistics**: See line counts, file size, and breakdown of content types

## How It Works

1. **Archive Extraction**: `.mcworld` and `.mctemplate` files are ZIP archives. The tool extracts them to a cache directory.

2. **Lang File Discovery**: Searches recursively for all `.lang` files and prioritizes en_US English files first.

3. **Interactive Selection**: Shows preview of the recommended file (en_US when available) and allows selection of alternatives.

4. **Caching**: Extracted files are kept in `.mc_lang_cache/` (or custom directory) to speed up repeated operations.

5. **Text Filtering**: When stripping text or analyzing complexity, keeps entries with common player-facing prefixes like:
   - `death.*`, `chat.*`, `book.*` - High-priority player messages
   - `menu.*`, `gui.*` - UI elements
   - `tile.*`, `item.*`, `block.*` - Game objects
   - `entity.*` - Mob/entity names
   - `advancements.*` - Achievement text
   - And many more...

6. **Text Cleaning**: For complexity analysis, automatically removes:
   - Minecraft formatting codes (§, color codes)
   - Format placeholders (%s, {0}, etc.)
   - Technical identifiers (camelCase, snake_case)
   - URLs and special characters
   - Standalone numbers and version codes

## File Structure

```
mcedulangtool5/
├── minecraft_lang_tool.py  # Main CLI application
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── .mc_lang_cache/         # Cache directory (created automatically)
```

## Requirements

- Python 3.7+
- click library (for CLI interface)
- Ollama (optional, for AI content analysis)
  - Install from: https://ollama.ai
  - Download a model: `ollama pull llama3.2` or `ollama pull llama3.1`

## Text Complexity Analysis

The tool provides comprehensive readability analysis designed for English (en_US) text:

### Readability Metrics
- **Flesch Reading Ease**: 0-100 scale (higher = easier to read)
- **Flesch-Kincaid Grade Level**: U.S. grade level
- **Gunning Fog Index**: Years of education needed
- **SMOG Index**: Simple Measure of Gobbledygook
- **Coleman-Liau Index**: Based on character count
- **Automated Readability Index**: Character-based formula

### Analysis Output
- **Grade Level**: Estimated reading grade (1st Grade to Advanced)
- **Age Range**: Target age group (e.g., "10-11 years")
- **Difficulty Level**: Easy, Moderate, Challenging, etc.
- **Vocabulary Breakdown**: Word length and complexity statistics
- **Lexical Diversity**: Unique word usage ratio

### Important Notes
- Analysis is optimized for **English (en_US)** text
- The tool automatically prioritizes en_US files
- Non-English files will show a warning
- Game text uses short phrases, so results are adjusted for vocabulary complexity
- Technical strings and formatting codes are automatically filtered out

## AI Content Analysis (Ollama)

Analyze game content using local AI models through Ollama.

### Prerequisites
1. Install Ollama from https://ollama.ai
2. Download a model (recommended):
   ```bash
   ollama pull llama3.2
   # or
   ollama pull mistral
   ```

### How It Works
1. The tool detects all available Ollama models on your system
2. You select which model to use
3. It extracts up to 200 player-facing text samples
4. Sends them to Ollama for analysis
5. Returns a comprehensive summary including:
   - Game description and theme
   - Educational focus (if applicable)
   - Key gameplay features
   - Target audience
   - Unique aspects

### Usage
Select option 3 from the operations menu after loading a language file. The tool will:
- List all available Ollama models
- Let you choose which model to use
- Analyze the game content (may take 30-60 seconds)
- Display the results
- Optionally save to a text file

### Notes
- Works best with English (en_US) language files
- Analysis time depends on your computer's performance
- Larger models (70B+) give better results but are slower
- Smaller models (7B-13B) are faster and still quite good

## Future Extensions

The operations menu is designed to be extensible. Potential additions:
- Translation comparison between language files
- Missing key detection
- Format validation
- Bulk processing of multiple files
- Export to different formats (JSON, CSV)
- Key search and filtering
- Multi-language complexity comparison
