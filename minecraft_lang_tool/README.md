# Minecraft Language File Tool - Regolith Filter

## What does this filter do?

This filter processes Minecraft Education Edition language files (`.lang`) from `.mcworld`, `.mctemplate`, or direct `.lang` files. It provides multiple operations:

- **Analyze**: Performs comprehensive text complexity analysis using multiple readability metrics (Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog Index, etc.)
- **Strip**: Removes non-player-facing text, keeping only player-visible content
- **Improve**: Uses AI (via Ollama) to improve text readability for specific target age groups
- **Quiz**: Generates educational quizzes from game narratives using AI
- **AI Analyze**: Uses AI to analyze game content themes and educational value

## How to use it

### Installation

Install the filter by running the following command:

```bash
regolith install github.com/jjedwards2081/mcedulangtool5/minecraft_lang_tool
```

This will automatically install the filter and its dependencies (Python 3.8+ is required).

For AI-powered features (optional), install [Ollama](https://ollama.ai) and download a model:

```bash
ollama pull phi4
```

### Configuration

Add the filter to the `filters` list in your `config.json`:

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "analyze",
		"input_file": "BP/texts/en_US.lang",
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

### Settings

All settings are passed as a JSON string to the filter. The filter accepts the following configuration:

#### Required Parameters

- **`operation`** (string): The operation to perform. One of:

  - `"analyze"` - Text complexity analysis
  - `"strip"` - Remove non-player text
  - `"improve"` - AI text improvement
  - `"quiz"` - Generate quiz
  - `"ai_analyze"` - AI content analysis

- **`input_file`** (string): Path to the input file (`.mcworld`, `.mctemplate`, or `.lang`)

#### Optional Parameters

- **`cache_dir`** (string): Directory for caching extracted files. Default: `".mc_lang_cache"`
- **`output_file`** (string): Custom output file path (varies by operation)
- **`output_dir`** (string): Custom output directory (for quiz operation)
- **`model_name`** (string): Ollama model name for AI operations. Default: `"phi4"`
- **`target_age`** (integer): Target age for improve/quiz operations. Default: `10`

### Usage Examples

#### Example 1: Analyze Text Complexity

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "analyze",
		"input_file": "BP/texts/en_US.lang",
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

This analyzes the language file and provides readability metrics including grade level, age range, and various complexity scores.

#### Example 2: Strip Non-Player Text

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "strip",
		"input_file": "BP/texts/en_US.lang",
		"output_file": "BP/texts/en_US_player_only.lang",
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

Removes technical and developer-facing text, keeping only content visible to players.

#### Example 3: AI Text Improvement

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "improve",
		"input_file": "BP/texts/en_US.lang",
		"output_file": "BP/texts/en_US_age10.lang",
		"model_name": "phi4",
		"target_age": 10,
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

Uses AI to improve text readability for 10-year-old players. Requires Ollama to be installed.

#### Example 4: Generate Educational Quiz

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "quiz",
		"input_file": "BP/world.mcworld",
		"output_dir": "BP/quizzes",
		"model_name": "phi4",
		"target_age": 12,
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

Generates a 10-question multiple choice quiz based on the game's narrative content.

#### Example 5: AI Content Analysis

```json
{
	"filter": "minecraft_lang_tool",
	"settings": {
		"operation": "ai_analyze",
		"input_file": "BP/texts/en_US.lang",
		"model_name": "phi4",
		"cache_dir": ".regolith/cache/mc_lang_tool"
	}
}
```

Uses AI to analyze the game's theme, educational focus, target audience, and key features.

## Using from Python

You can also use the filter programmatically in your own Python scripts:

```python
import json
from minecraft_lang_tool.core import MinecraftLangTool

# Initialize the tool
tool = MinecraftLangTool(cache_dir=".regolith/cache")

# Configure operation
config = {
    "operation": "analyze",
    "input_file": "BP/texts/en_US.lang"
}

# Process (pass config as JSON string)
config_json = json.dumps(config)
result = tool.process_from_config(config_json)

# Check results
if result.get('success'):
    print(f"Grade Level: {result['analysis']['grade_level']}")
    print(f"Age Range: {result['analysis']['age_range']}")
else:
    print(f"Error: {result.get('error')}")
```

## Output

The filter returns a JSON object with the results:

```json
{
	"operation": "analyze",
	"success": true,
	"analysis": {
		"grade_level": "6th Grade",
		"age_range": "11-12 years",
		"difficulty": "Moderate - Middle School",
		"flesch_reading_ease": 65.3,
		"flesch_kincaid_grade": 6.2,
		"total_words": 1523,
		"unique_words": 456
	}
}
```
