# Minecraft Language File Tool

A Python CLI application for extracting and processing Minecraft `.lang` files from `.mcworld` and `.mctemplate` archives, with AI-powered educational features.

## Features

- **Extract archives**: Automatically extracts `.mcworld` and `.mctemplate` files (which are ZIP-based)
- **Find lang files**: Locates all `.lang` files and prioritizes en_US English files
- **Interactive selection**: Preview and select the correct lang file with confirmation
- **Smart caching**: Stores extracted files to avoid reprocessing
- **Text complexity analysis**: Comprehensive readability assessment with age/grade recommendations
- **Text stripping**: Remove non-player-facing text to keep only player-visible strings
- **AI content analysis**: Use Ollama to analyze and summarize game content
- **AI text improvement**: Improve text line-by-line for specific target ages with user control
- **Quiz generation**: Create age-appropriate multiple choice quizzes from game narratives
- **Browse Downloads**: Quick access to files in your Downloads folder
- **Organized output**: All improvements, changelogs, and quizzes stored in structured folders
- **Terminal-friendly filenames**: All output files use sanitized names (no spaces/special characters)

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Install Ollama for AI features:
   - Download from https://ollama.ai
   - Pull a model: `ollama pull phi4` or `ollama pull llama3.2`

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

## Operations Menu

Once you've selected a lang file, you can choose from:

### 1. Strip Non-Player-Facing Text
Removes internal/debug strings, keeping only player-visible content
- Output saved as `<filename>_player_only.lang`
- Shows how many lines were removed
- Preview the result before saving

### 2. Text Complexity Analysis
Comprehensive readability assessment with multiple metrics:
- **Flesch Reading Ease**: 0-100 scale (higher = easier)
- **Flesch-Kincaid Grade Level**: U.S. grade level
- **Gunning Fog Index**: Years of education needed
- **SMOG Index**: Simple Measure of Gobbledygook
- **Coleman-Liau Index**: Character-based formula
- **Automated Readability Index**: Alternative grade level

Provides:
- Grade level recommendations
- Age range estimates
- Difficulty assessment
- Vocabulary breakdown
- Lexical diversity metrics

**Note**: Optimized for English (en_US) text. Non-English files will show a warning.

### 3. AI Content Analysis
Analyze game content using local Ollama models:
- Automatically detects available models
- Summarizes game theme and features
- Identifies educational focus
- Determines target audience
- Saves analysis report

**Requires**: Ollama installed with at least one model

### 4. AI Text Improvement for Target Age
Improve text line-by-line to match a specific reading level:
- Choose target age (e.g., 8, 10, 12)
- AI suggests improvements for each line
- **User controls every change**:
  - **Accept**: Use AI suggestion
  - **Edit**: Provide your own version
  - **Reject**: Keep original
- Creates improved lang file
- Generates detailed changelog showing:
  - Line numbers
  - Original and improved text
  - Full line comparisons
  - Status (AI/User Edited/Rejected)

**Features**:
- Context-aware: Skips labels (1-2 words), adjusts for text length
- No technical references in improvements
- Real-time progress with elapsed time
- Organized output in `improvements/` folder

### 5. Generate Quiz from Game Narrative
Create educational quizzes from game content:
- 10 multiple choice questions
- Age-appropriate language
- Based on game story and educational elements
- Includes answer key (saved separately)
- Filters out technical game code
- Focuses on gameplay narrative

**Output**:
- Quiz file: `<filename>_quiz_age<X>.txt`
- Answer key: `<filename>_quiz_age<X>_answers.txt`
- Saved in `quizzes/` folder

### 6. View Full File Contents
Display the entire lang file with pagination

### 7. Get File Statistics
Line counts, file size, and content type breakdown

## File Structure

```
mcedulangtool5/
├── minecraft_lang_tool.py      # Main CLI application
├── requirements.txt             # Python dependencies
├── README.md                   # This file
└── .mc_lang_cache/             # Cache directory (auto-created)
    └── <World_Name>/
        └── resource_packs/
            └── <Pack_Name>/
                └── texts/
                    ├── en_US.lang
                    ├── en_US_improved_age10.lang
                    ├── improvements/
                    │   └── en_US_changelog_age10.txt
                    └── quizzes/
                        ├── en_US_quiz_age10.txt
                        └── en_US_quiz_age10_answers.txt
```

## Requirements

- Python 3.7+
- click >= 8.1.0 (CLI framework)
- Ollama (optional, for AI features)
  - Install from: https://ollama.ai
  - Recommended models: `phi4`, `llama3.2`, `gpt-oss:20b`, `gemma3:1b`

## How It Works

### Archive Extraction
`.mcworld` and `.mctemplate` files are ZIP archives. The tool extracts them to a cache directory and searches recursively for `.lang` files.

### Lang File Discovery
- Searches for all `.lang` files in the archive
- Prioritizes en_US English files first
- Shows file sizes to help identify the main file
- Allows selection of alternative files if needed

### Text Filtering
Keeps entries with player-facing prefixes like:
- `death.*`, `chat.*`, `book.*` - Player messages
- `menu.*`, `gui.*` - UI elements
- `tile.*`, `item.*`, `block.*` - Game objects
- `entity.*` - Mob/entity names
- `advancement.*` - Achievement text
- Custom keys from educational worlds

### Text Cleaning
Automatically removes for analysis:
- Minecraft formatting codes (§, color codes)
- Format placeholders (%s, {0}, etc.)
- Technical identifiers (`:_input_key.:`)
- URLs and special characters
- Inline comments (#, ##)

### AI Processing
- **Content Analysis**: Sends text samples to Ollama (300s timeout)
- **Text Improvement**: Processes line-by-line (60s per line timeout)
  - Skips 1-2 word entries (labels/titles)
  - Vocabulary-only changes for 3-4 word entries
  - Full improvements for 5+ word entries
  - No emojis or meta-commentary in output
- **Quiz Generation**: Creates questions from narrative (300s timeout)
  - Removes technical references
  - Age-appropriate language
  - Multiple choice format with 4 options

### Caching System
- Extracted archives stored in `.mc_lang_cache/`
- Organized by world/pack name
- Speeds up repeated operations
- Can be cleared with `clear-cache` command

## Tips for Best Results

### For Text Analysis
- Works best with English (en_US) files
- Automatically detects and warns for other languages
- Supports custom world key formats

### For AI Features
- **Smaller models** (7B-13B): Faster, good for most tasks
  - `phi4` - Excellent for educational content
  - `llama3.2` - Fast and capable
  - `gemma3:1b` - Very fast, lighter analysis
- **Larger models** (20B+): Better analysis but slower
  - `gpt-oss:20b` - High quality improvements
  
### For Text Improvement
- Choose appropriate target age for your audience
- Review AI suggestions - you have full control
- Use **Edit** option to customize suggestions
- Check the changelog for a summary of all changes

### For Quiz Generation
- Best with worlds that have rich narratives
- Educational worlds produce the best questions
- Answer key saved separately for teacher use

## Example Workflow

1. **Extract and select file**:
   ```bash
   python minecraft_lang_tool.py process Sustainability_City.mcworld
   ```

2. **Analyze text complexity** (Option 2):
   - Check reading level
   - Identify if improvements needed

3. **Improve text for target age** (Option 4):
   - Set target age (e.g., 10)
   - Review each suggestion
   - Accept, edit, or reject changes
   - Get improved file + changelog

4. **Generate quiz** (Option 5):
   - Choose target age
   - Get 10 questions based on game content
   - Use for classroom assessment

## Troubleshooting

### No Ollama models found
- Install Ollama from https://ollama.ai
- Pull a model: `ollama pull phi4`
- Verify: `ollama list`

### Timeout errors during AI processing
- Use a smaller/faster model
- Check Ollama is running: `ollama serve`
- Reduce text complexity if possible

### Wrong language detected
- Tool prioritizes en_US files automatically
- Select correct file from the list if needed
- Some custom worlds use non-standard key formats (supported)

### Cache issues
- Clear cache: `python minecraft_lang_tool.py clear-cache`
- Or manually delete `.mc_lang_cache/` folder

## Future Enhancements

Potential additions:
- Translation comparison between language files
- Missing key detection
- Batch processing of multiple files
- Export to different formats (JSON, CSV)
- Multi-language quiz support
- Collaborative editing features

## License

This tool is provided as-is for educational purposes.

## Credits

Created for processing Minecraft Education Edition worlds and enhancing educational content accessibility.
