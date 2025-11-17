#!/usr/bin/env python3
"""
Minecraft Language File Tool - CLI Wrapper

This is the command-line interface wrapper that converts CLI arguments
to JSON configuration and passes them to the core processing module.

Author: Justin Edwards
Email: jnredwards@gmail.com
License: MIT License

Copyright (c) 2025 Justin Edwards
"""

import sys
import json
import click
from pathlib import Path

# Add parent directory to path for package imports
sys.path.insert(0, str(Path(__file__).parent))

from minecraft_lang_tool.core import MinecraftLangTool


def browse_downloads_folder() -> str:
    """Browse and select a file from the Downloads folder."""
    downloads_path = Path.home() / "Downloads"
    
    if not downloads_path.exists():
        click.echo("Downloads folder not found!")
        return None
    
    # Find relevant files
    supported_extensions = ['.mcworld', '.mctemplate', '.lang']
    files = []
    
    for ext in supported_extensions:
        files.extend(downloads_path.glob(f"*{ext}"))
    
    if not files:
        click.echo(f"No Minecraft files found in Downloads folder.")
        click.echo(f"Looking for: {', '.join(supported_extensions)}")
        return None
    
    # Sort by modification time (newest first)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    click.echo(f"\nFound {len(files)} file(s) in Downloads folder:")
    click.echo("="*60)
    
    for idx, file in enumerate(files, 1):
        size = file.stat().st_size
        size_mb = size / (1024 * 1024)
        mod_time = file.stat().st_mtime
        from datetime import datetime
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
        
        click.echo(f"{idx}. {file.name}")
        click.echo(f"   Size: {size_mb:.2f} MB | Modified: {mod_date}")
    
    click.echo("="*60)
    choice = click.prompt("\nSelect a file number (0 to cancel)", type=int, default=1)
    
    if 0 < choice <= len(files):
        return str(files[choice - 1])
    
    return None


def display_menu() -> int:
    """Display interactive menu and return user choice."""
    click.echo("\n" + "="*50)
    click.echo("OPERATIONS MENU")
    click.echo("="*50)
    click.echo("1. Strip non-player-facing text")
    click.echo("2. Text complexity analysis")
    click.echo("3. AI content analysis (using Ollama)")
    click.echo("4. AI text improvement for target age (using Ollama)")
    click.echo("5. Generate quiz from game narrative (using Ollama)")
    click.echo("6. View full file contents")
    click.echo("7. Get file statistics")
    click.echo("0. Exit")
    
    return click.prompt("\nSelect an operation", type=int, default=1)


def select_ollama_model(tool: MinecraftLangTool) -> str:
    """Let user select an Ollama model."""
    click.echo("Checking for available Ollama models...")
    models = tool.get_ollama_models()
    
    if not models:
        click.echo("\n⚠️  No Ollama models found!")
        click.echo("Please install Ollama and at least one model first.")
        click.echo("\nVisit: https://ollama.ai")
        return None
    
    click.echo(f"\nFound {len(models)} model(s):")
    for idx, model in enumerate(models, 1):
        click.echo(f"  {idx}. {model}")
    
    model_choice = click.prompt("\nSelect a model number", type=int, default=1)
    
    if model_choice < 1 or model_choice > len(models):
        click.echo("Invalid selection")
        return None
    
    return models[model_choice - 1]


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
def cli():
    """Minecraft Language File Tool - Extract and process .lang files from Minecraft archives."""
    pass


@cli.command()
@click.argument('config_file', type=click.Path(exists=True), required=False)
@click.option('--operation', type=click.Choice(['strip', 'analyze', 'improve', 'quiz', 'ai_analyze']), 
              help='Operation to perform')
@click.option('--input-file', type=click.Path(exists=True), help='Input file path')
@click.option('--output-file', type=click.Path(), help='Output file path')
@click.option('--cache-dir', default='.mc_lang_cache', help='Cache directory')
@click.option('--model-name', help='Ollama model name')
@click.option('--target-age', type=int, help='Target age for improvement/quiz')
def run(config_file, operation, input_file, output_file, cache_dir, model_name, target_age):
    """
    Run processing with JSON config file or CLI arguments.
    
    Examples:
        # Using config file
        python cli.py run config.json
        
        # Using CLI arguments
        python cli.py run --operation analyze --input-file world.mcworld
    """
    tool = MinecraftLangTool(cache_dir=cache_dir)
    
    if config_file:
        # Load configuration from JSON file
        click.echo(f"Loading configuration from: {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Build configuration from CLI arguments
        if not operation or not input_file:
            click.echo("Error: When not using config file, --operation and --input-file are required")
            return
        
        config = {
            'operation': operation,
            'input_file': input_file,
            'cache_dir': cache_dir
        }
        
        if output_file:
            config['output_file'] = output_file
        if model_name:
            config['model_name'] = model_name
        if target_age:
            config['target_age'] = target_age
    
    # Process with core module
    click.echo(f"\nProcessing operation: {config['operation']}")
    result = tool.process_from_config(config)
    
    # Display results
    click.echo("\n" + "="*60)
    click.echo("RESULTS")
    click.echo("="*60)
    
    if result.get('success'):
        click.echo("✓ Operation completed successfully")
        
        # Display operation-specific results
        if result['operation'] == 'strip':
            click.echo(f"  Output file: {result['output_file']}")
            click.echo(f"  Removed lines: {result['removed_lines']}")
        
        elif result['operation'] == 'analyze':
            analysis = result['analysis']
            click.echo(f"\n📊 Text Complexity Analysis:")
            click.echo(f"  Grade Level: {analysis['grade_level']}")
            click.echo(f"  Age Range: {analysis['age_range']}")
            click.echo(f"  Difficulty: {analysis['difficulty']}")
            click.echo(f"\n  Flesch Reading Ease: {analysis['flesch_reading_ease']}")
            click.echo(f"  Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']}")
            click.echo(f"  Total Words: {analysis['total_words']}")
            click.echo(f"  Unique Words: {analysis['unique_words']}")
        
        elif result['operation'] == 'improve':
            click.echo(f"  Output file: {result['output_file']}")
            click.echo(f"  Changelog: {result['changelog_file']}")
            click.echo(f"  Lines processed: {result['lines_processed']}")
            click.echo(f"  Lines improved: {result['lines_improved']}")
        
        elif result['operation'] == 'quiz':
            click.echo(f"  Quiz file: {result['quiz_file']}")
            click.echo(f"  Answer key: {result['answer_key_file']}")
        
        elif result['operation'] == 'ai_analyze':
            click.echo(f"\n🤖 AI Analysis ({result['model']}):")
            click.echo(f"  Samples analyzed: {result['samples_analyzed']}")
            click.echo(f"\n{result['analysis']}")
    
    else:
        click.echo(f"✗ Error: {result.get('error', 'Unknown error')}")
    
    # Save results to JSON
    output_json = Path(cache_dir) / "last_result.json"
    with open(output_json, 'w') as f:
        json.dump(result, f, indent=2)
    click.echo(f"\nFull results saved to: {output_json}")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('--cache-dir', default='.mc_lang_cache', help='Directory for caching extracted files')
@click.option('--downloads', is_flag=True, help='Browse files in Downloads folder')
def process(input_file, cache_dir, downloads):
    """
    Interactive mode - Process a Minecraft file with menu-driven interface.
    
    This is the original interactive CLI that guides you through operations.
    """
    tool = MinecraftLangTool(cache_dir=cache_dir)
    
    # If downloads flag is set or no input file provided, browse Downloads
    if downloads or not input_file:
        input_file = browse_downloads_folder()
        if not input_file:
            click.echo("No file selected. Exiting.")
            return
    
    input_path = Path(input_file)
    
    # Handle different input types
    if input_path.suffix.lower() == '.lang':
        click.echo(f"Processing lang file directly: {input_path}")
        lang_file = input_path
    elif input_path.suffix.lower() in ['.mcworld', '.mctemplate']:
        # Extract archive
        extract_dir = tool.extract_archive(input_file)
        
        # Find lang files
        click.echo("\nSearching for .lang files...")
        lang_files = tool.find_lang_files(extract_dir)
        
        if not lang_files:
            click.echo("No .lang files found!")
            return
        
        click.echo(f"Found {len(lang_files)} .lang file(s)")
        
        # Show the recommended file
        largest_file, largest_size = lang_files[0]
        
        click.echo(f"\nRecommended .lang file (largest):")
        click.echo(f"  Path: {largest_file}")
        click.echo(f"  Size: {largest_size / 1024:.2f} KB")
        click.echo("\nPreview:")
        
        preview = tool.preview_lang_file(largest_file)
        for line in preview:
            click.echo(f"  {line}")
        
        if click.confirm("\nIs this the correct lang file?", default=True):
            lang_file = largest_file
        else:
            click.echo("Operation cancelled.")
            return
    else:
        click.echo(f"Unsupported file type: {input_path.suffix}")
        click.echo("Supported types: .mcworld, .mctemplate, .lang")
        return
    
    # Show menu and process choice
    choice = display_menu()
    
    if choice == 1:
        # Strip non-player text
        output_path = Path(cache_dir) / f"{tool.sanitize_filename(lang_file.stem)}_player_only.lang"
        click.echo(f"\nStripping non-player-facing text...")
        removed = tool.strip_non_player_text(lang_file, output_path)
        click.echo(f"✓ Removed {removed} lines")
        click.echo(f"✓ Output saved to: {output_path}")
    
    elif choice == 2:
        # Text complexity analysis
        click.echo(f"\nAnalyzing text complexity...")
        analysis = tool.analyze_text_complexity(lang_file)
        
        if 'error' in analysis:
            click.echo(f"✗ Error: {analysis['error']}")
        else:
            click.echo("\n" + "="*60)
            click.echo("TEXT COMPLEXITY ANALYSIS")
            click.echo("="*60)
            click.echo(f"\n📊 Overall Assessment:")
            click.echo(f"  Grade Level: {analysis['grade_level']}")
            click.echo(f"  Age Range: {analysis['age_range']}")
            click.echo(f"  Difficulty: {analysis['difficulty']}")
            click.echo(f"\n📖 Readability Scores:")
            click.echo(f"  Flesch Reading Ease: {analysis['flesch_reading_ease']}/100")
            click.echo(f"  Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']}")
            click.echo(f"  Gunning Fog Index: {analysis['gunning_fog_index']}")
            if analysis['smog_index']:
                click.echo(f"  SMOG Index: {analysis['smog_index']}")
            click.echo(f"  Coleman-Liau Index: {analysis['coleman_liau_index']}")
            click.echo(f"  Automated Readability Index: {analysis['automated_readability_index']}")
            click.echo(f"\n📝 Text Statistics:")
            click.echo(f"  Total Entries: {analysis['total_entries']}")
            click.echo(f"  Total Words: {analysis['total_words']}")
            click.echo(f"  Unique Words: {analysis['unique_words']}")
            click.echo(f"  Average Word Length: {analysis['avg_word_length']} characters")
            click.echo(f"  Average Sentence Length: {analysis['avg_sentence_length']} words")
    
    elif choice == 3:
        # AI content analysis
        model_name = select_ollama_model(tool)
        if not model_name:
            return
        
        click.echo(f"\nAnalyzing with {model_name}...")
        result = tool.analyze_with_ollama(lang_file, model_name)
        
        if 'error' in result:
            click.echo(f"✗ Error: {result['error']}")
        else:
            click.echo("\n" + "="*60)
            click.echo(f"AI ANALYSIS - {result['model']}")
            click.echo("="*60)
            click.echo(result['analysis'])
    
    elif choice == 4:
        # AI text improvement
        model_name = select_ollama_model(tool)
        if not model_name:
            return
        
        target_age = click.prompt("Enter target age", type=int, default=10)
        
        click.echo(f"\nImproving text for age {target_age} using {model_name}...")
        result = tool.improve_text_for_age(lang_file, model_name, target_age)
        
        if 'error' in result:
            click.echo(f"✗ Error: {result['error']}")
        else:
            click.echo("\n✓ Text improvement completed!")
            click.echo(f"  Output file: {result['output_file']}")
            click.echo(f"  Changelog: {result['changelog_file']}")
            click.echo(f"  Lines processed: {result['lines_processed']}")
    
    elif choice == 5:
        # Generate quiz
        model_name = select_ollama_model(tool)
        if not model_name:
            return
        
        target_age = click.prompt("Enter target age", type=int, default=10)
        
        click.echo(f"\nGenerating quiz for age {target_age}...")
        result = tool.generate_quiz(lang_file, model_name, target_age)
        
        if 'error' in result:
            click.echo(f"✗ Error: {result['error']}")
        else:
            click.echo("\n✓ Quiz generated successfully!")
            click.echo(f"  Quiz file: {result['quiz_file']}")
            click.echo(f"  Answer key: {result['answer_key_file']}")
    
    elif choice == 6:
        # View full contents
        with open(lang_file, 'r', encoding='utf-8') as f:
            click.echo(f.read())
    
    elif choice == 7:
        # File statistics
        with open(lang_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
            non_empty = sum(1 for line in lines if line.strip())
            comments = sum(1 for line in lines if line.strip().startswith('#'))
        
        click.echo(f"\nFile Statistics for {lang_file.name}:")
        click.echo(f"  Total lines: {total_lines}")
        click.echo(f"  Non-empty lines: {non_empty}")
        click.echo(f"  Comment lines: {comments}")
        click.echo(f"  File size: {lang_file.stat().st_size / 1024:.2f} KB")
    
    click.echo("\nDone!")


@cli.command()
@click.option('--cache-dir', default='.mc_lang_cache', help='Directory for caching extracted files')
def clear_cache(cache_dir):
    """Clear the extraction cache."""
    import shutil
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        click.echo(f"Cache directory '{cache_dir}' does not exist.")
        return
    
    if click.confirm(f"Delete cache directory '{cache_dir}' and all its contents?"):
        shutil.rmtree(cache_path)
        click.echo(f"✓ Cache cleared: {cache_dir}")
    else:
        click.echo("Cancelled.")


if __name__ == '__main__':
    cli()
