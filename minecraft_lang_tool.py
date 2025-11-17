#!/usr/bin/env python3
"""
Minecraft Language File Tool

A CLI tool for extracting and processing Minecraft .lang files from .mcworld/.mctemplate archives
with AI-powered educational features including text complexity analysis, content improvement,
and quiz generation.

Author: Justin Edwards
Email: jnredwards@gmail.com
License: MIT License

Copyright (c) 2025 Justin Edwards

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import click
from glob import glob
import re
from collections import Counter
import json
import subprocess
import time
import threading


class MinecraftLangTool:
    """
    Main class for processing Minecraft Education Edition language files.
    
    This tool provides functionality to:
    - Extract .mcworld and .mctemplate archives
    - Locate and parse .lang files
    - Analyze text complexity and readability
    - Improve text for specific target ages using AI
    - Generate educational quizzes from game content
    - Analyze content themes using Ollama AI models
    """
    
    def __init__(self, cache_dir: str = ".mc_lang_cache"):
        """Initialize the Minecraft Language Tool with a cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Remove spaces and special characters from filename for terminal compatibility.
        
        Converts filenames like "Sustainability City v3" to "Sustainability_City_v3"
        making them easy to click and use in terminal environments.
        
        Args:
            filename: Original filename string
            
        Returns:
            Sanitized filename with only alphanumeric, underscores, hyphens, and dots
        """
        # Keep only alphanumeric, underscores, hyphens, and dots
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        return sanitized
        
    def extract_archive(self, archive_path: str) -> Path:
        """
        Extract .mcworld or .mctemplate file to cache directory.
        
        Both .mcworld and .mctemplate files are ZIP archives containing
        Minecraft Education Edition world data. This method extracts them
        to a cache directory for processing.
        
        Args:
            archive_path: Path to the .mcworld or .mctemplate file
            
        Returns:
            Path to the extracted directory
            
        Raises:
            FileNotFoundError: If the archive doesn't exist
            zipfile.BadZipFile: If the archive is corrupted
        """
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        # Create extraction directory based on archive name
        extract_dir = self.cache_dir / archive_path.stem
        
        # Check if already extracted
        if extract_dir.exists():
            click.echo(f"Using cached extraction: {extract_dir}")
            return extract_dir
        
        click.echo(f"Extracting {archive_path.name}...")
        
        # Both .mcworld and .mctemplate are ZIP files
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            click.echo(f"Extracted to: {extract_dir}")
            return extract_dir
        except zipfile.BadZipFile:
            raise ValueError(f"Invalid archive format: {archive_path}")
    
    def find_lang_files(self, directory: Path) -> List[Tuple[Path, int]]:
        """
        Find all .lang files in directory and return with their sizes (largest first).
        
        Prioritizes English language files, particularly en_US, as these are most
        commonly used in Minecraft Education Edition. Files are sorted by size
        to help identify the primary language file.
        
        Args:
            directory: Root directory to search recursively
            
        Returns:
            List of tuples containing (file_path, file_size_bytes) sorted by:
            1. en_US files (largest first)
            2. Other English variants (en_GB, en_CA, etc.)
            3. All other language files (largest first)
        """
        lang_files = []
        en_us_files = []
        other_english_files = []
        
        # Prioritize en_US specifically, then other English variants
        primary_english = 'en_us'
        other_english_patterns = ['en_gb', 'en_ca', 'en_au', 'en.lang', 'english']
        
        for lang_file in directory.rglob("*.lang"):
            size = lang_file.stat().st_size
            filename_lower = lang_file.name.lower()
            
            # Check if it's en_US (highest priority)
            if primary_english in filename_lower:
                en_us_files.append((lang_file, size))
            # Check if it's another English variant
            elif any(pattern in filename_lower for pattern in other_english_patterns):
                other_english_files.append((lang_file, size))
            else:
                lang_files.append((lang_file, size))
        
        # Sort all groups by size (largest first)
        en_us_files.sort(key=lambda x: x[1], reverse=True)
        other_english_files.sort(key=lambda x: x[1], reverse=True)
        lang_files.sort(key=lambda x: x[1], reverse=True)
        
        # Return en_US first (largest), then other English (largest), then others (largest)
        return en_us_files + other_english_files + lang_files
    
    def preview_lang_file(self, lang_path: Path, lines: int = 5) -> List[str]:
        """Read and return first N lines of a lang file."""
        preview_lines = []
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    preview_lines.append(line.rstrip())
        except UnicodeDecodeError:
            # Try with latin-1 encoding as fallback
            with open(lang_path, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    preview_lines.append(line.rstrip())
        
        return preview_lines
    
    def select_lang_file(self, lang_files: List[Tuple[Path, int]]) -> Optional[Path]:
        """Present lang files to user and let them select one."""
        if not lang_files:
            click.echo("No .lang files found!")
            return None
        
        # Show the first file (should be en_US if available)
        largest_file, largest_size = lang_files[0]
        
        # Check if it looks like English
        filename_lower = largest_file.name.lower()
        is_en_us = 'en_us' in filename_lower
        is_english = is_en_us or any(pattern in filename_lower for pattern in ['en_gb', 'en_ca', 'en_au', 'en.lang', 'english'])
        
        click.echo(f"\nRecommended .lang file (largest):")
        if is_en_us:
            click.echo(f"  [en_US - English (United States)]")
        elif is_english:
            click.echo(f"  [English variant detected]")
        else:
            click.echo(f"  [Warning: May not be English - complexity analysis works best with en_US]")
        click.echo(f"  Path: {largest_file}")
        size_kb = largest_size / 1024
        click.echo(f"  Size: {size_kb:.2f} KB")
        click.echo("\nPreview:")
        
        preview = self.preview_lang_file(largest_file)
        for line in preview:
            click.echo(f"  {line}")
        
        # Ask for confirmation
        if click.confirm("\nIs this the correct lang file?", default=True):
            return largest_file
        
        # Show other options
        if len(lang_files) > 1:
            click.echo("\nOther .lang files found:")
            for idx, (path, size) in enumerate(lang_files[1:], 1):
                size_kb = size / 1024
                click.echo(f"  {idx}. {path.relative_to(path.parents[len(path.parents)-1])} ({size_kb:.2f} KB)")
            
            choice = click.prompt(
                "\nSelect a file number (0 to cancel)",
                type=int,
                default=0
            )
            
            if 0 < choice <= len(lang_files) - 1:
                selected = lang_files[choice]
                click.echo("\nPreview:")
                preview = self.preview_lang_file(selected[0])
                for line in preview:
                    click.echo(f"  {line}")
                return selected[0]
        
        return None
    
    def strip_non_player_text(self, lang_path: Path, output_path: Path) -> int:
        """
        Strip non-player-facing text from lang file, keeping only player-visible strings.
        
        Common patterns to keep:
        - UI text (tile., item., entity., etc.)
        - Messages and descriptions
        - Menu items
        
        Common patterns to remove:
        - Developer comments
        - Internal keys
        - Debug strings
        """
        kept_lines = []
        removed_count = 0
        
        # Patterns that typically indicate player-facing content
        player_facing_prefixes = [
            'tile.', 'item.', 'entity.', 'effect.', 'enchantment.',
            'menu.', 'gui.', 'options.', 'death.', 'chat.',
            'commands.', 'gameMode.', 'difficulty.', 'multiplayer.',
            'structure_block.', 'jigsaw_block.', 'advancements.',
            'stat.', 'container.', 'key.', 'subtitles.', 'book.',
            'biome.', 'block.', 'potion.', 'attribute.'
        ]
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    
                    # Keep empty lines
                    if not stripped:
                        kept_lines.append(line)
                        continue
                    
                    # Keep comments (optional - can be adjusted)
                    if stripped.startswith('#') or stripped.startswith('//'):
                        kept_lines.append(line)
                        continue
                    
                    # Check if line contains key=value format
                    if '=' in stripped:
                        key = stripped.split('=', 1)[0].strip()
                        
                        # Keep if it starts with player-facing prefix
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            kept_lines.append(line)
                        else:
                            removed_count += 1
                    else:
                        # Keep lines that don't follow key=value format
                        kept_lines.append(line)
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                        kept_lines.append(line)
                        continue
                    if '=' in stripped:
                        key = stripped.split('=', 1)[0].strip()
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            kept_lines.append(line)
                        else:
                            removed_count += 1
                    else:
                        kept_lines.append(line)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
        
        return removed_count
    
    def _get_preview_analyzed_text(self, lang_path: Path, lines: int = 20) -> List[str]:
        """Get a preview of text that will be analyzed for complexity."""
        text_values = []
        
        player_facing_prefixes = [
            'death.', 'chat.', 'book.', 'sign.',
            'menu.', 'gui.', 'options.',
            'gameMode.', 'difficulty.', 'multiplayer.',
            'advancements.', 'subtitle.',
            'entity.', 'effect.', 'enchantment.',
            'tile.', 'item.', 'block.',
            'biome.', 'potion.', 'attribute.',
            'container.', 'structure_block.', 'jigsaw_block.',
            'stat.', 'commands.',
        ]
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(text_values) >= lines:
                        break
                    
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        if not value or len(value) < 3:
                            continue
                        
                        if '.' in value and ' ' not in value:
                            continue
                        
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            clean_value = self._clean_text_for_analysis(value)
                            if clean_value and len(clean_value.split()) >= 2:
                                text_values.append(clean_value)
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for line in f:
                    if len(text_values) >= lines:
                        break
                    
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        if not value or len(value) < 3:
                            continue
                        
                        if '.' in value and ' ' not in value:
                            continue
                        
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            clean_value = self._clean_text_for_analysis(value)
                            if clean_value and len(clean_value.split()) >= 2:
                                text_values.append(clean_value)
        
        return text_values
    
    def analyze_text_complexity(self, lang_path: Path) -> Dict:
        """
        Perform comprehensive text complexity analysis on player-facing text.
        
        Uses multiple established readability formulas to assess the reading level
        of game text. Particularly useful for educators to determine if content
        is appropriate for their students' reading abilities.
        
        Metrics calculated:
        - Flesch Reading Ease (0-100 scale)
        - Flesch-Kincaid Grade Level
        - Gunning Fog Index
        - SMOG Index
        - Coleman-Liau Index
        - Automated Readability Index (ARI)
        
        Also provides vocabulary analysis and age recommendations.
        
        Args:
            lang_path: Path to the lang file to analyze
            
        Returns:
            dict: Comprehensive analysis including:
                - All readability scores
                - Grade level recommendations
                - Age range estimates
                - Vocabulary breakdown
                - Lexical diversity metrics
                - Warning if non-English text detected
        """
        # Extract player-facing text values only
        text_values = []
        skipped_technical = 0
        
        # Prioritize the most user-facing content
        player_facing_prefixes = [
            # High priority - clearly player-facing
            'death.', 'chat.', 'book.', 'sign.',
            'menu.', 'gui.', 'options.',
            'gameMode.', 'difficulty.', 'multiplayer.',
            'advancements.', 'subtitle.',
            # Medium priority - descriptive text
            'entity.', 'effect.', 'enchantment.',
            'tile.', 'item.', 'block.',
            'biome.', 'potion.', 'attribute.',
            # Lower priority - may contain more technical terms
            'container.', 'structure_block.', 'jigsaw_block.',
            'stat.', 'commands.',
        ]
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Skip empty values or values that are just technical strings
                        if not value or len(value) < 3:
                            continue
                        
                        # Skip if value looks like a key itself (no spaces, lots of dots/underscores)
                        if '.' in value and ' ' not in value:
                            skipped_technical += 1
                            continue
                        
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            # Clean the text value
                            clean_value = self._clean_text_for_analysis(value)
                            if clean_value and len(clean_value.split()) >= 2:
                                text_values.append(clean_value)
                            else:
                                skipped_technical += 1
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        if not value or len(value) < 3:
                            continue
                        
                        if '.' in value and ' ' not in value:
                            skipped_technical += 1
                            continue
                        
                        if any(key.startswith(prefix) for prefix in player_facing_prefixes):
                            clean_value = self._clean_text_for_analysis(value)
                            if clean_value and len(clean_value.split()) >= 2:
                                text_values.append(clean_value)
                            else:
                                skipped_technical += 1
        
        if not text_values:
            return {"error": "No player-facing text found"}
        
        # For game text, each entry is typically a complete thought/phrase
        # Treat each text_value as a separate "sentence" for better analysis
        analysis = {
            'total_entries': len(text_values),
            'skipped_technical': skipped_technical,
            'total_words': 0,
            'total_sentences': 0,
            'total_syllables': 0,
            'total_characters': 0,
            'unique_words': 0,
            'avg_word_length': 0,
            'avg_sentence_length': 0,
            'avg_syllables_per_word': 0,
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'gunning_fog_index': 0,
            'smog_index': 0,
            'coleman_liau_index': 0,
            'automated_readability_index': 0,
            'age_range': '',
            'grade_level': '',
            'difficulty': '',
            'vocabulary_complexity': {}
        }
        
        # Treat each text entry as a sentence for better analysis of short phrases
        analysis['total_sentences'] = len(text_values)
        
        # Combine for word-level analysis
        full_text = ' '.join(text_values)
        
        words = self._extract_words(full_text)
        analysis['total_words'] = len(words)
        analysis['unique_words'] = len(set(words))
        
        if not words:
            return analysis
        
        # Character count (letters only)
        analysis['total_characters'] = sum(len(word) for word in words)
        analysis['avg_word_length'] = analysis['total_characters'] / analysis['total_words']
        
        # Syllable count
        syllables = [self._count_syllables(word) for word in words]
        analysis['total_syllables'] = sum(syllables)
        analysis['avg_syllables_per_word'] = analysis['total_syllables'] / analysis['total_words']
        
        # Average sentence length
        if analysis['total_sentences'] > 0:
            analysis['avg_sentence_length'] = analysis['total_words'] / analysis['total_sentences']
        
        # Complex words (3+ syllables)
        complex_words = sum(1 for s in syllables if s >= 3)
        complex_word_ratio = complex_words / analysis['total_words'] if analysis['total_words'] > 0 else 0
        
        # Flesch Reading Ease (0-100, higher = easier)
        if analysis['total_sentences'] > 0:
            analysis['flesch_reading_ease'] = (
                206.835 
                - 1.015 * (analysis['total_words'] / analysis['total_sentences'])
                - 84.6 * (analysis['total_syllables'] / analysis['total_words'])
            )
        
        # Flesch-Kincaid Grade Level
        if analysis['total_sentences'] > 0:
            analysis['flesch_kincaid_grade'] = (
                0.39 * (analysis['total_words'] / analysis['total_sentences'])
                + 11.8 * (analysis['total_syllables'] / analysis['total_words'])
                - 15.59
            )
        
        # Gunning Fog Index
        if analysis['total_sentences'] > 0:
            analysis['gunning_fog_index'] = (
                0.4 * ((analysis['total_words'] / analysis['total_sentences']) + 100 * complex_word_ratio)
            )
        
        # SMOG Index
        if analysis['total_sentences'] >= 30:
            analysis['smog_index'] = (
                1.0430 * ((complex_words * (30 / analysis['total_sentences'])) ** 0.5) + 3.1291
            )
        else:
            analysis['smog_index'] = None
        
        # Coleman-Liau Index
        L = (analysis['total_characters'] / analysis['total_words']) * 100
        S = (analysis['total_sentences'] / analysis['total_words']) * 100
        analysis['coleman_liau_index'] = 0.0588 * L - 0.296 * S - 15.8
        
        # Automated Readability Index
        if analysis['total_sentences'] > 0:
            analysis['automated_readability_index'] = (
                4.71 * (analysis['total_characters'] / analysis['total_words'])
                + 0.5 * (analysis['total_words'] / analysis['total_sentences'])
                - 21.43
            )
        
        # Vocabulary complexity analysis
        word_lengths = Counter(len(word) for word in words)
        analysis['vocabulary_complexity'] = {
            'short_words_1_3': sum(count for length, count in word_lengths.items() if 1 <= length <= 3),
            'medium_words_4_6': sum(count for length, count in word_lengths.items() if 4 <= length <= 6),
            'long_words_7_plus': sum(count for length, count in word_lengths.items() if length >= 7),
            'complex_words_3plus_syllables': complex_words,
            'lexical_diversity': round(analysis['unique_words'] / analysis['total_words'], 3) if analysis['total_words'] > 0 else 0
        }
        
        # Determine age range and grade level
        avg_grade = self._calculate_average_grade(analysis)
        analysis['grade_level'] = self._grade_to_string(avg_grade)
        analysis['age_range'] = self._grade_to_age_range(avg_grade)
        analysis['difficulty'] = self._difficulty_level(avg_grade)
        
        # Round numerical values for readability
        analysis['flesch_reading_ease'] = round(analysis['flesch_reading_ease'], 1)
        analysis['flesch_kincaid_grade'] = round(analysis['flesch_kincaid_grade'], 1)
        analysis['gunning_fog_index'] = round(analysis['gunning_fog_index'], 1)
        if analysis['smog_index']:
            analysis['smog_index'] = round(analysis['smog_index'], 1)
        analysis['coleman_liau_index'] = round(analysis['coleman_liau_index'], 1)
        analysis['automated_readability_index'] = round(analysis['automated_readability_index'], 1)
        analysis['avg_word_length'] = round(analysis['avg_word_length'], 2)
        analysis['avg_sentence_length'] = round(analysis['avg_sentence_length'], 1)
        analysis['avg_syllables_per_word'] = round(analysis['avg_syllables_per_word'], 2)
        
        return analysis
    
    def _clean_text_for_analysis(self, text: str) -> str:
        """Remove technical characters and formatting, keep only readable text."""
        if not text:
            return ""
        
        original_text = text
        
        # Remove common Minecraft formatting codes
        text = re.sub(r'§[0-9a-fk-or]', '', text)  # Color codes
        text = re.sub(r'%[0-9]+\$?[sdifgx]', '', text)  # Format placeholders like %s, %d, %1$s, %i, %f
        text = re.sub(r'%\([^)]+\)[sd]', '', text)  # Python-style placeholders %(name)s
        text = re.sub(r'\{[0-9]+\}', '', text)  # Placeholders like {0}, {1}
        text = re.sub(r'\{\w+\}', '', text)  # Named placeholders like {player}
        text = re.sub(r'\\n', ' ', text)  # Newline escapes
        text = re.sub(r'\\t', ' ', text)  # Tab escapes
        text = re.sub(r'<[^>]+>', '', text)  # HTML/XML tags
        text = re.sub(r'\[.*?\]', '', text)  # Bracketed technical terms
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove special technical punctuation but keep sentence punctuation (.!?,;:')
        text = re.sub(r'[_{}()\[\]<>|\\/@#$%^&*+=~`]', ' ', text)
        
        # Remove numbers that are likely technical (standalone numbers or version numbers)
        text = re.sub(r'\b\d+(\.\d+)*\b', '', text)
        
        # Remove camelCase and snake_case identifiers that look technical
        # Keep normal words but remove things like "minecraftServer" or "player_name"
        text = re.sub(r'\b[a-z]+[A-Z][a-zA-Z]*\b', '', text)  # camelCase
        text = re.sub(r'\b\w+_\w+\b', '', text)  # snake_case
        
        # Remove single letters that are likely variable names
        text = re.sub(r'\b[a-zA-Z]\b', '', text)
        
        # Remove common technical abbreviations
        text = re.sub(r'\b(fps|fov|gui|api|rgb|xyz|pos|vec|nbt|uuid|id)\b', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Only return if it has substantial content (at least 2 words)
        # Also check that it's at least 40% of original length (not too stripped)
        words = text.split()
        if len(words) >= 2 and len(text) >= len(original_text) * 0.3:
            return text
        
        return ""
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # For game text, each string is typically a complete thought/sentence
        # Split on sentence-ending punctuation, but also treat each distinct
        # string as potentially its own sentence
        
        # First, split on clear sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Also split on patterns that indicate separate thoughts:
        # - Multiple spaces (indicating separate entries concatenated)
        # - Capitalized words after lowercase (new sentence)
        all_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            # Further split long segments that are likely multiple sentences
            # Look for capital letter following a lowercase word
            subsents = re.split(r'(?<=[a-z])\s+(?=[A-Z])', sent)
            all_sentences.extend([s.strip() for s in subsents if s.strip()])
        
        return all_sentences
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text (letters only)."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    # ========================================================================
    # Helper Methods for Text Analysis
    # ========================================================================
    
    def _count_syllables(self, word: str) -> int:
        """
        Estimate syllable count for a word.
        
        Uses a simple heuristic based on vowel groups, which is sufficiently
        accurate for readability analysis. Handles common patterns like
        silent 'e' and consonant-le endings.
        
        Args:
            word: Single word to analyze
            
        Returns:
            Estimated syllable count (minimum 1)
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        # Adjust for 'le' ending
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            syllable_count += 1
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)
    
    def _calculate_average_grade(self, analysis: Dict) -> float:
        """Calculate average grade level from multiple readability metrics."""
        grades = []
        
        if analysis['flesch_kincaid_grade'] > 0:
            grades.append(analysis['flesch_kincaid_grade'])
        
        if analysis['gunning_fog_index'] > 0:
            grades.append(analysis['gunning_fog_index'])
        
        if analysis['smog_index'] and analysis['smog_index'] > 0:
            grades.append(analysis['smog_index'])
        
        if analysis['coleman_liau_index'] > 0:
            grades.append(analysis['coleman_liau_index'])
        
        if analysis['automated_readability_index'] > 0:
            grades.append(analysis['automated_readability_index'])
        
        base_grade = sum(grades) / len(grades) if grades else 0
        
        # Adjust for vocabulary complexity in game text (which uses short phrases)
        # Game text complexity comes more from vocabulary than sentence structure
        vocab = analysis['vocabulary_complexity']
        total_words = analysis['total_words']
        
        if total_words > 0:
            # Factor in word length and complexity
            long_word_ratio = vocab['long_words_7_plus'] / total_words
            complex_word_ratio = vocab['complex_words_3plus_syllables'] / total_words
            
            # More balanced vocabulary adjustment (up to +3 grades instead of more)
            vocab_adjustment = (long_word_ratio * 1.5 + complex_word_ratio * 1.5) * 2
            
            # Smaller lexical diversity bonus (0-1 grade)
            diversity_bonus = vocab['lexical_diversity'] * 1
            
            adjusted_grade = base_grade + vocab_adjustment + diversity_bonus
            
            return adjusted_grade
        
        return base_grade
    
    def _grade_to_string(self, grade: float) -> str:
        """Convert numeric grade to string representation."""
        if grade < 1:
            return "Kindergarten or below"
        elif grade < 2:
            return "1st Grade"
        elif grade < 3:
            return "2nd Grade"
        elif grade < 4:
            return "3rd Grade"
        elif grade < 13:
            return f"{int(grade)}th Grade"
        elif grade < 16:
            return "College Level"
        else:
            return "Advanced/Professional"
    
    def _grade_to_age_range(self, grade: float) -> str:
        """Convert grade level to age range."""
        if grade < 1:
            return "5-6 years"
        elif grade < 2:
            return "6-7 years"
        elif grade < 3:
            return "7-8 years"
        elif grade < 4:
            return "8-9 years"
        elif grade < 5:
            return "9-10 years"
        elif grade < 6:
            return "10-11 years"
        elif grade < 7:
            return "11-12 years"
        elif grade < 8:
            return "12-13 years"
        elif grade < 9:
            return "13-14 years"
        elif grade < 10:
            return "14-15 years"
        elif grade < 11:
            return "15-16 years"
        elif grade < 12:
            return "16-17 years"
        elif grade < 13:
            return "17-18 years"
        elif grade < 16:
            return "18-21 years (College)"
        else:
            return "21+ years (Advanced)"
    
    def _difficulty_level(self, grade: float) -> str:
        """Determine difficulty level description."""
        if grade < 3:
            return "Very Easy - Early Elementary"
        elif grade < 6:
            return "Easy - Elementary"
        elif grade < 9:
            return "Moderate - Middle School"
        elif grade < 13:
            return "Challenging - High School"
        elif grade < 16:
            return "Difficult - College Level"
        else:
            return "Very Difficult - Advanced"
    
    def get_ollama_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            # Parse the output - skip header line
            lines = result.stdout.strip().split('\n')
            models = []
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    # First column is the model name
                    model_name = line.split()[0]
                    models.append(model_name)
            
            return models
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    
    def improve_text_for_age(self, lang_path, model_name, target_age):
        """
        Use Ollama AI to improve text in lang file for specific target age.
        
        This method processes each line of the language file and uses AI to suggest
        improvements that make the text more appropriate for the target age group.
        Users have full control to accept, edit, or reject each suggestion.
        
        Features:
        - Context-aware: Skips short labels (1-2 words)
        - Smart processing: Vocabulary-only for short text, full improvements for longer text
        - User control: Accept AI suggestion, provide custom edit, or reject
        - Real-time logging: Creates detailed changelog with line numbers and status
        - Progress tracking: Shows spinner with elapsed time
        
        Args:
            lang_path: Path to the lang file to improve
            model_name: Name of the Ollama model to use (e.g., 'phi4', 'llama3.2')
            target_age: Target age for text improvements (e.g., 8, 10, 12)
            
        Returns:
            dict: Results including:
                - output_file: Path to improved lang file
                - changelog_file: Path to detailed changelog
                - lines_processed: Total lines processed
                - lines_improved: Number of lines changed
                - lines_unchanged: Number of lines kept original
                - error: Error message if processing failed
        """
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return {'error': f"Failed to read file: {str(e)}"}
        
        # Prepare output files
        lang_path_obj = Path(lang_path)
        sanitized_stem = self.sanitize_filename(lang_path_obj.stem)
        output_filename = sanitized_stem + f"_improved_age{target_age}" + lang_path_obj.suffix
        output_path = lang_path_obj.parent / output_filename
        
        # Store changelog in organized folder next to lang file
        changelog_dir = lang_path_obj.parent / "improvements"
        changelog_dir.mkdir(exist_ok=True)
        changelog_filename = sanitized_stem + f"_changelog_age{target_age}.txt"
        changelog_path = changelog_dir / changelog_filename
        
        improved_lines = []
        
        lines_processed = 0
        lines_improved = 0
        lines_unchanged = 0
        
        # Initialize changelog file immediately
        try:
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(f"Text Improvement Changelog for Age {target_age}\n")
                f.write(f"Model: {model_name}\n")
                f.write(f"Source: {lang_path}\n")
                f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                f.write("Processing...\n\n")
                f.flush()  # Force write to disk
        except Exception as e:
            return {'error': f"Failed to create changelog file: {str(e)}"}
        
        # Load context file if available
        context_text = self._load_context_file(Path(lang_path))
        context_summary = ""
        if context_text:
            click.echo("[Using game context file for enhanced improvements]")
            # Extract just the summary section
            if "CONTEXT SUMMARY:" in context_text:
                context_summary = context_text.split("CONTEXT SUMMARY:")[1].split("="*60)[0].strip()
                # Keep it concise for the prompt
                context_summary = context_summary[:300] + "..." if len(context_summary) > 300 else context_summary
        
        # Create a progress indicator
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        spinner_index = [0]
        start_time = time.time()
        stop_spinner = [False]
        
        def spinner_task():
            while not stop_spinner[0]:
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                sys.stdout.write(f'\r{spinner_chars[spinner_index[0] % len(spinner_chars)]} Processing line {lines_processed}/{len(lines)} ({lines_improved} improved) - {mins}m {secs}s')
                sys.stdout.flush()
                spinner_index[0] += 1
                time.sleep(0.1)
        
        spinner_thread = threading.Thread(target=spinner_task, daemon=True)
        spinner_thread.start()
        
        try:
            for line_num, line in enumerate(lines, 1):
                lines_processed += 1
                
                # Check if line is a comment or empty
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                # Check if line contains a key-value pair
                if '=' not in line:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                # Split into key and value
                parts = line.split('=', 1)
                if len(parts) != 2:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                key = parts[0].strip()
                value = parts[1].strip()
                
                # Skip if value is empty or too short
                if not value or len(value) < 3:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                # Check if this looks like player-facing text
                # Skip technical entries (no spaces, all caps, numbers only, etc.)
                if not any(c.isalpha() and c.islower() for c in value):
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                if value.replace('_', '').replace('.', '').replace('-', '').isalnum() and ' ' not in value:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                # Clean value for analysis (remove formatting codes and inline comments)
                clean_value = re.sub(r'§[0-9a-fk-or]', '', value)
                clean_value = re.sub(r'%[0-9]+\$?[sd]|%s|%d', '', clean_value)
                # Remove inline comments that start with # or ##
                if '#' in clean_value:
                    clean_value = clean_value.split('#')[0].strip()
                clean_value = clean_value.strip()
                
                if len(clean_value) < 3:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                # Use AI to evaluate and improve the text
                # Count words to determine if sentence structure analysis is needed
                word_count = len(clean_value.split())
                
                # Skip very short entries (1-2 words) - they're usually labels/titles
                if word_count <= 2:
                    improved_lines.append(line)
                    lines_unchanged += 1
                    continue
                
                if word_count >= 5:
                    context_prefix = f"\nGame context: {context_summary}\n" if context_summary else ""
                    prompt = f"""You are improving text in a Minecraft educational game for a {target_age}-year-old player.{context_prefix}

Original text: "{clean_value}"

Task: Improve this text ONLY if it contains difficult vocabulary or complex sentence structure for a {target_age} year old.

Consider BOTH:
1. Vocabulary: Replace words that are too advanced (e.g., "utilize" → "use", "facilitate" → "help")
2. Sentence structure: Break up long, complex sentences into shorter, clearer ones

CRITICAL RULES:
- If text is already simple and clear for age {target_age}: Respond with exactly "KEEP_ORIGINAL"
- If improvement needed: Provide ONLY the improved text with NO extra commentary
- Do NOT add explanations, hashtags, word counts, or meta-commentary
- Do NOT reference word limits or formatting instructions
- Keep the improved text natural and engaging

Response (either "KEEP_ORIGINAL" or the improved text only):"""
                else:
                    context_prefix = f"\nGame context: {context_summary}\n" if context_summary else ""
                    prompt = f"""You are improving text in a Minecraft educational game for a {target_age}-year-old player.{context_prefix}

Original text: "{clean_value}"

Task: Check if this SHORT PHRASE contains any difficult vocabulary for a {target_age} year old.

FOCUS: Only simplify vocabulary if words are too advanced. Do NOT expand or add words.

Examples of good changes:
- "Utilize" → "Use"
- "Commence" → "Start"  
- "Facilitate" → "Help"

CRITICAL RULES:
- If vocabulary is already simple for age {target_age}: Respond with exactly "KEEP_ORIGINAL"
- If improvement needed: Provide ONLY the improved text with NO additions
- Do NOT add explanations, hashtags, or meta-commentary
- Do NOT expand short phrases into longer sentences
- Keep it concise - same length or shorter than original

Response (either "KEEP_ORIGINAL" or the improved text only):"""

                try:
                    # Call Ollama with timeout
                    result = subprocess.run(
                        ['ollama', 'run', model_name, prompt],
                        capture_output=True,
                        text=True,
                        timeout=60  # Shorter timeout per line
                    )
                    
                    if result.returncode != 0:
                        # On error, keep original
                        improved_lines.append(line)
                        lines_unchanged += 1
                        continue
                    
                    response = result.stdout.strip()
                    
                    # Check if AI says to keep original
                    if 'KEEP_ORIGINAL' in response.upper():
                        improved_lines.append(line)
                        lines_unchanged += 1
                    else:
                        # Clean up the response - remove quotes, extra whitespace, emoji
                        improved_text = response.strip('"\'').strip()
                        # Remove all emoji characters (comprehensive removal)
                        improved_text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+', '', improved_text)
                        improved_text = re.sub(r'[😀-🿿]', '', improved_text)  # Additional emoji range
                        improved_text = re.sub(r'\s+', ' ', improved_text).strip()  # Normalize whitespace
                        # Remove common AI prefixes/suffixes
                        for phrase in ['Here is', 'Here\'s', 'The improved text is', 'Improved:', 'Keep it', 'Response:']:
                            if improved_text.startswith(phrase):
                                improved_text = improved_text[len(phrase):].strip(':').strip()
                        
                        # Only accept if it's reasonable (not empty, not too different in length)
                        if improved_text and len(improved_text) > 0:
                            length_ratio = len(improved_text) / len(clean_value)
                            if 0.3 < length_ratio < 3.0:  # Reasonable length change
                                # Pause spinner for user confirmation
                                stop_spinner[0] = True
                                spinner_thread.join(timeout=1)
                                sys.stdout.write('\r' + ' ' * 100 + '\r')
                                sys.stdout.flush()
                                
                                # Show proposed change and ask for user decision
                                click.echo(f"\nLine {line_num}: {key}")
                                click.echo(f"  ORIGINAL: {clean_value}")
                                click.echo(f"  PROPOSED: {improved_text}")
                                click.echo("\nOptions:")
                                click.echo("  1. Accept AI suggestion")
                                click.echo("  2. Edit the suggestion")
                                click.echo("  3. Keep original (reject)")
                                
                                choice = click.prompt("  Select option", type=int, default=1)
                                
                                if choice == 1:
                                    # Accept AI suggestion
                                    final_text = improved_text
                                    status = "ACCEPTED (AI)"
                                elif choice == 2:
                                    # User wants to edit
                                    click.echo("\nEnter your custom text (press Enter to confirm):")
                                    user_text = click.prompt("  ", default=improved_text, show_default=False)
                                    final_text = user_text.strip()
                                    status = "USER EDITED"
                                    lines_improved += 1
                                else:
                                    # Keep original (reject)
                                    improved_lines.append(line)
                                    lines_unchanged += 1
                                    
                                    # Log rejection with full lines
                                    try:
                                        with open(changelog_path, 'a', encoding='utf-8') as f:
                                            f.write(f"[LINE {line_num}] {key}\n")
                                            f.write(f"  ORIGINAL TEXT: {clean_value}\n")
                                            f.write(f"  PROPOSED TEXT: {improved_text}\n")
                                            f.write(f"  OLD LINE: {line.rstrip()}\n")
                                            f.write(f"  PROPOSED LINE: {key}={improved_text}\n")
                                            f.write(f"  STATUS: REJECTED BY USER\n")
                                            f.write("-" * 60 + "\n\n")
                                            f.flush()
                                    except Exception as e:
                                        pass
                                    
                                    # Resume spinner
                                    stop_spinner[0] = False
                                    spinner_thread = threading.Thread(target=spinner_task, daemon=True)
                                    spinner_thread.start()
                                    continue
                                
                                # Process accepted or edited text
                                if choice in [1, 2]:
                                    # Preserve any formatting codes from original
                                    if '§' in value:
                                        format_match = re.match(r'^((?:§[0-9a-fk-or])+)', value)
                                        if format_match:
                                            final_text = format_match.group(1) + final_text
                                    
                                    # Build improved line
                                    improved_line = f"{key}={final_text}\n"
                                    improved_lines.append(improved_line)
                                    if choice == 1:
                                        lines_improved += 1
                                    
                                    # Write to changelog immediately with full lines
                                    try:
                                        with open(changelog_path, 'a', encoding='utf-8') as f:
                                            f.write(f"[LINE {line_num}] {key}\n")
                                            f.write(f"  ORIGINAL TEXT: {clean_value}\n")
                                            if choice == 2:
                                                f.write(f"  AI PROPOSED: {improved_text}\n")
                                            f.write(f"  IMPROVED TEXT: {final_text}\n")
                                            f.write(f"  OLD LINE: {line.rstrip()}\n")
                                            f.write(f"  NEW LINE: {improved_line.rstrip()}\n")
                                            f.write(f"  STATUS: {status}\n")
                                            f.write("-" * 60 + "\n\n")
                                            f.flush()
                                    except Exception as e:
                                        pass
                                
                                # Resume spinner (for all paths that continue)
                                stop_spinner[0] = False
                                spinner_thread = threading.Thread(target=spinner_task, daemon=True)
                                spinner_thread.start()
                            else:
                                # Length change too dramatic, keep original
                                improved_lines.append(line)
                                lines_unchanged += 1
                        else:
                            # Empty response, keep original
                            improved_lines.append(line)
                            lines_unchanged += 1
                
                except subprocess.TimeoutExpired:
                    # Timeout, keep original
                    improved_lines.append(line)
                    lines_unchanged += 1
                except Exception as e:
                    # Any error, keep original
                    improved_lines.append(line)
                    lines_unchanged += 1
        
        finally:
            stop_spinner[0] = True
            spinner_thread.join(timeout=1)
            sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear spinner line
            sys.stdout.flush()
        
        # Write improved file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(improved_lines)
        except Exception as e:
            return {'error': f"Failed to write improved file: {str(e)}"}
        
        # Finalize changelog
        try:
            with open(changelog_path, 'a', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write(f"Processing complete!\n")
                f.write(f"Total lines: {lines_processed}\n")
                f.write(f"Lines improved: {lines_improved}\n")
                f.write(f"Lines unchanged: {lines_unchanged}\n")
                if lines_improved == 0:
                    f.write("\nNo changes made - all text was already appropriate for target age.\n")
        except Exception as e:
            return {'error': f"Failed to finalize changelog: {str(e)}"}
        
        return {
            'output_file': str(output_path),
            'changelog_file': str(changelog_path),
            'lines_processed': lines_processed,
            'lines_improved': lines_improved,
            'lines_unchanged': lines_unchanged
        }
    
    def generate_quiz(self, lang_path, model_name, target_age):
        """
        Generate a 10-question multiple choice quiz based on game narrative.
        
        Uses AI to analyze the game's language file and create educational quiz
        questions based on the storyline, gameplay mechanics, and educational content.
        Questions are age-appropriate with 4 multiple choice options each.
        
        Features:
        - Filters out technical game code and references
        - Focuses on actual narrative and educational content
        - Age-appropriate language and concepts
        - Separate answer key file for educators
        - Organized output in quizzes/ folder
        
        Args:
            lang_path: Path to the lang file
            model_name: Name of the Ollama model to use (recommended: 'phi4')
            target_age: Target age for quiz language (e.g., 8, 10, 12)
            
        Returns:
            dict: Results including:
                - quiz_file: Path to the quiz file
                - answer_key_file: Path to the answer key
                - error: Error message if generation failed
        """
        # Extract narrative text from the lang file
        narrative_texts = []
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove inline comments
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        
                        if not value or len(value) < 5:
                            continue
                        
                        # Look for narrative/dialogue text (longer entries with context)
                        # Skip technical entries, UI labels, single words
                        if any(c.isalpha() and c.islower() for c in value):
                            # Clean formatting codes and technical references
                            clean_value = re.sub(r'§[0-9a-fk-or]', '', value)
                            clean_value = re.sub(r'%[0-9]+\$?[sd]|%s|%d', '', clean_value)
                            # Remove technical placeholders and input key references
                            clean_value = re.sub(r':_input_key\.[^:]+:', '', clean_value)
                            clean_value = re.sub(r'\[.*?\]', '', clean_value)  # Remove [bracketed] tech notes
                            clean_value = re.sub(r'\s+', ' ', clean_value).strip()
                            
                            # Keep entries with substantial content (sentences, paragraphs)
                            if len(clean_value.split()) >= 5:
                                narrative_texts.append(clean_value)
        
        except Exception as e:
            return {'error': f"Failed to read file: {str(e)}"}
        
        if not narrative_texts:
            return {'error': "No narrative text found in lang file"}
        
        # Load context file if available
        lang_path_obj = Path(lang_path)
        context_text = self._load_context_file(lang_path_obj)
        context_section = ""
        if context_text:
            click.echo("[Using game context file for enhanced quiz generation]")
            # Extract just the summary section
            if "CONTEXT SUMMARY:" in context_text:
                context_summary = context_text.split("CONTEXT SUMMARY:")[1].split("="*60)[0].strip()
                context_section = f"\n\nGAME CONTEXT:\n{context_summary}\n"
        
        # Combine narrative text for context
        narrative_sample = '\n'.join(narrative_texts[:100])  # Use first 100 entries
        
        # Create quiz using AI
        prompt = f"""You are creating a 10-question multiple choice quiz for a {target_age}-year-old student based on this educational Minecraft game narrative.{context_section}

GAME NARRATIVE:
{narrative_sample}

TASK: Create a quiz with exactly 10 questions that test comprehension and understanding of the game content.

IMPORTANT: The game narrative may contain technical code or placeholders - ignore these completely. Focus only on the actual story, gameplay, and educational content that a {target_age}-year-old player would experience.

REQUIREMENTS:
1. Each question must have 4 answer choices (A, B, C, D)
2. Only ONE correct answer per question
3. Language must be appropriate for age {target_age} - use simple, clear vocabulary
4. Questions should test understanding of: game objectives, characters, locations, concepts taught, and story events
5. Each question is worth 1 mark (total: 10 marks)
6. Include a mix of question types: recall, comprehension, and application
7. DO NOT reference technical game code, placeholders like ":_input_key:", or developer notation
8. Questions should be answerable by a {target_age}-year-old who played the game
9. Avoid abstract or overly technical concepts - keep it concrete and relatable

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS (no extra text):

QUIZ: [Game Name] Comprehension Quiz
Target Age: {target_age}
Total Marks: 10 (1 mark per question)

Question 1: [Your question here]
A) [Answer option A]
B) [Answer option B]
C) [Answer option C]
D) [Answer option D]

Question 2: [Your question here]
A) [Answer option A]
B) [Answer option B]
C) [Answer option C]
D) [Answer option D]

[Continue for all 10 questions]

ANSWER KEY:
1. [Letter]
2. [Letter]
3. [Letter]
4. [Letter]
5. [Letter]
6. [Letter]
7. [Letter]
8. [Letter]
9. [Letter]
10. [Letter]

Generate the quiz now:"""

        # Show progress
        click.echo("\nGenerating quiz questions...")
        click.echo("This may take 1-2 minutes...")
        
        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, prompt],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                return {'error': f"Ollama error: {result.stderr}"}
            
            quiz_content = result.stdout.strip()
            
            if not quiz_content or len(quiz_content) < 100:
                return {'error': "Quiz generation failed - no content produced"}
        
        except subprocess.TimeoutExpired:
            return {'error': "Quiz generation timed out (5 minutes)"}
        except FileNotFoundError:
            return {'error': "Ollama not found. Please install Ollama first."}
        except Exception as e:
            return {'error': f"Failed to generate quiz: {str(e)}"}
        
        # Split quiz and answer key
        quiz_text = quiz_content
        answer_key_text = ""
        
        if "ANSWER KEY:" in quiz_content:
            parts = quiz_content.split("ANSWER KEY:")
            quiz_text = parts[0].strip()
            answer_key_text = "ANSWER KEY:\n" + parts[1].strip()
        
        # Save quiz file in organized folder structure
        lang_path_obj = Path(lang_path)
        quiz_filename = lang_path_obj.stem + f"_quiz_age{target_age}.txt"
        sanitized_stem = self.sanitize_filename(lang_path_obj.stem)
        quiz_filename = sanitized_stem + f"_quiz_age{target_age}.txt"
        answer_key_filename = sanitized_stem + f"_quiz_age{target_age}_answers.txt"
        
        # Create output folder next to the lang file
        output_dir = lang_path_obj.parent / "quizzes"
        output_dir.mkdir(exist_ok=True)
        
        quiz_path = output_dir / quiz_filename
        answer_key_path = output_dir / answer_key_filename
        
        try:
            # Save full quiz (without answer key)
            with open(quiz_path, 'w', encoding='utf-8') as f:
                f.write(quiz_text)
                f.write(f"\n\n{'='*60}\n")
                f.write(f"Instructions: Choose the best answer for each question.\n")
                f.write(f"Write your answer (A, B, C, or D) for each question.\n")
                f.write(f"Total Score: ___ / 10\n")
            
            # Save answer key separately
            with open(answer_key_path, 'w', encoding='utf-8') as f:
                f.write(f"ANSWER KEY\n")
                f.write(f"{'='*60}\n")
                f.write(f"Quiz: {lang_path_obj.stem}\n")
                f.write(f"Target Age: {target_age}\n")
                f.write(f"{'='*60}\n\n")
                f.write(answer_key_text)
                f.write(f"\n\n{'='*60}\n")
                f.write(f"Scoring: 1 mark per correct answer\n")
                f.write(f"Total: 10 marks\n")
        
        except Exception as e:
            return {'error': f"Failed to save quiz files: {str(e)}"}
        
        return {
            'quiz_file': str(quiz_path),
            'answer_key_file': str(answer_key_path)
        }
    
    def create_context_file(self, lang_path: Path, model_name: str) -> Dict:
        """
        Create a game context file through AI-generated questions.
        
        Uses AI to generate 5 relevant questions about the game, captures user
        responses, and consolidates them into a context file. This context is
        then used to enhance all AI operations (content analysis, quiz generation,
        text improvement).
        
        Args:
            lang_path: Path to the lang file (used to determine context file location)
            model_name: Name of the Ollama model to use (e.g., 'phi4')
            
        Returns:
            dict: Results including:
                - context_file: Path to the created context file
                - questions: List of questions asked
                - answers: List of user answers
                - error: Error message if creation failed
        """
        lang_path_obj = Path(lang_path)
        
        # Store context file next to lang file
        context_filename = lang_path_obj.stem + "_context.txt"
        context_path = lang_path_obj.parent / context_filename
        
        # Check if context file already exists
        if context_path.exists():
            if not click.confirm(f"\nContext file already exists. Overwrite?", default=False):
                return {
                    'context_file': str(context_path),
                    'status': 'cancelled',
                    'message': 'User chose not to overwrite existing context file'
                }
        
        click.echo("\n" + "="*60)
        click.echo("Creating Game Context File")
        click.echo("="*60)
        click.echo("\nThe AI will generate 5 questions about your game to better")
        click.echo("understand its educational content, theme, and target audience.")
        click.echo("This context will improve all AI-powered features.\n")
        
        # First, sample some text from the lang file to help AI generate relevant questions
        text_samples = []
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            if value and len(value) > 10:
                                # Clean the text
                                clean_value = re.sub(r'§[0-9a-fk-or]', '', value)
                                clean_value = re.sub(r'%[0-9]+\$?[sdifgx]', '', clean_value)
                                clean_value = re.sub(r':_input_key\..*?:', '', clean_value)
                                clean_value = clean_value.strip()
                                if clean_value:
                                    text_samples.append(clean_value)
                        
                        if len(text_samples) >= 50:
                            break
        except Exception as e:
            return {'error': f"Failed to read lang file: {str(e)}"}
        
        if not text_samples:
            return {'error': "No text content found in lang file"}
        
        # Generate questions using AI
        click.echo("Generating questions about your game...")
        
        sample_text = "\n".join(text_samples[:30])
        
        question_prompt = f"""Based on this text from an educational Minecraft game, generate exactly 5 important questions that would help understand the game's educational content, theme, objectives, and target audience.

Game text samples:
{sample_text}

Generate 5 questions that will help understand:
1. The educational topic/subject (e.g., sustainability, history, science)
2. The game's learning objectives
3. Target student age/grade level
4. Key concepts or skills being taught
5. The narrative or gameplay context

Format your response as exactly 5 questions, one per line, numbered 1-5.
Make questions clear and specific. Do not include any other text."""

        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, question_prompt],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return {'error': f"Ollama failed: {result.stderr}"}
            
            questions_text = result.stdout.strip()
            
            # Parse questions
            questions = []
            for line in questions_text.split('\n'):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, 6)):
                    # Remove the number prefix
                    question = re.sub(r'^\d+\.\s*', '', line)
                    if question:
                        questions.append(question)
            
            if len(questions) < 5:
                return {'error': f"AI generated only {len(questions)} questions. Expected 5."}
            
            questions = questions[:5]  # Ensure exactly 5
            
        except subprocess.TimeoutExpired:
            return {'error': "Question generation timed out"}
        except Exception as e:
            return {'error': f"Failed to generate questions: {str(e)}"}
        
        # Ask user the questions and capture answers
        click.echo("\n" + "="*60)
        click.echo("Please answer the following questions about your game:")
        click.echo("="*60 + "\n")
        
        answers = []
        for i, question in enumerate(questions, 1):
            click.echo(f"Question {i}:")
            click.echo(f"  {question}")
            answer = click.prompt("Your answer", type=str)
            answers.append(answer)
            click.echo()
        
        # Consolidate into context using AI
        click.echo("Creating consolidated context file...")
        
        qa_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
        
        consolidation_prompt = f"""You are creating a context file for an educational Minecraft game. Based on the following questions and answers, write a comprehensive but concise context summary (200-300 words) that captures:

1. The educational topic and subject matter
2. Learning objectives and key concepts
3. Target audience (age/grade level)
4. Gameplay narrative and context
5. How the game teaches or reinforces learning

Questions and Answers:
{qa_text}

Write a clear, informative context summary that will help AI understand this game when analyzing content, generating quizzes, or improving text. Use a professional educational tone. Do not include section headers - write as flowing paragraphs."""

        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, consolidation_prompt],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return {'error': f"Context consolidation failed: {result.stderr}"}
            
            context_summary = result.stdout.strip()
            
            # Save context file
            with open(context_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("GAME CONTEXT FILE\n")
                f.write("="*60 + "\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {model_name}\n")
                f.write(f"Source: {lang_path_obj.name}\n")
                f.write("="*60 + "\n\n")
                
                f.write("CONTEXT SUMMARY:\n")
                f.write("-"*60 + "\n")
                f.write(context_summary)
                f.write("\n\n")
                
                f.write("="*60 + "\n")
                f.write("ORIGINAL QUESTIONS & ANSWERS:\n")
                f.write("="*60 + "\n\n")
                
                for i, (q, a) in enumerate(zip(questions, answers), 1):
                    f.write(f"Question {i}: {q}\n")
                    f.write(f"Answer: {a}\n\n")
            
            click.echo("\nContext file created successfully!")
            click.echo(f"Location: {context_path}")
            
            return {
                'context_file': str(context_path),
                'questions': questions,
                'answers': answers,
                'summary': context_summary,
                'status': 'success'
            }
            
        except subprocess.TimeoutExpired:
            return {'error': "Context consolidation timed out"}
        except Exception as e:
            return {'error': f"Failed to create context file: {str(e)}"}
    
    def _load_context_file(self, lang_path: Path) -> Optional[str]:
        """
        Load context file if it exists.
        
        Args:
            lang_path: Path to the lang file
            
        Returns:
            Context text if file exists, None otherwise
        """
        lang_path_obj = Path(lang_path)
        context_filename = lang_path_obj.stem + "_context.txt"
        context_path = lang_path_obj.parent / context_filename
        
        if context_path.exists():
            try:
                with open(context_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
        return None
    
    def analyze_with_ollama(self, lang_path: Path, model: str) -> Dict:
        """Use Ollama to analyze game content from player-facing text."""
        # Extract player-facing text
        text_samples = []
        
        # For AI analysis, be more inclusive - accept any text that looks player-facing
        # Don't filter by prefix as strictly, since custom worlds use custom keys
        skip_prefixes = ['debug.', 'key.keyboard.', 'translation.test.', 'generator.']
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove inline comments (text after # or ##)
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        
                        if not value or len(value) < 2:
                            continue
                        
                        # Skip technical keys
                        if any(key.startswith(prefix) for prefix in skip_prefixes):
                            continue
                        
                        # Skip if value looks like a key itself
                        if '.' in value and ' ' not in value and len(value) > 20:
                            continue
                        
                        # For AI analysis, include the text (less strict cleaning)
                        # Just remove basic formatting codes
                        clean_value = re.sub(r'§[0-9a-fk-or]', '', value)
                        clean_value = re.sub(r'%[0-9]+\$?[sdifgx]', '', clean_value)
                        clean_value = re.sub(r'\{[0-9]+\}', '', clean_value)
                        clean_value = re.sub(r'\\n', ' ', clean_value)
                        clean_value = clean_value.strip()
                        
                        if clean_value:
                            text_samples.append(f"{key}: {clean_value}")
                            
                        # Limit samples to avoid overwhelming the model
                        if len(text_samples) >= 200:
                            break
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for line in f:
                    stripped = line.strip()
                    if '=' in stripped and not stripped.startswith('#'):
                        parts = stripped.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove inline comments
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        
                        if not value or len(value) < 2:
                            continue
                        
                        # Skip technical keys
                        if any(key.startswith(prefix) for prefix in skip_prefixes):
                            continue
                        
                        # Skip if value looks like a key itself
                        if '.' in value and ' ' not in value and len(value) > 20:
                            continue
                        
                        # Basic cleaning for AI analysis
                        clean_value = re.sub(r'§[0-9a-fk-or]', '', value)
                        clean_value = re.sub(r'%[0-9]+\$?[sdifgx]', '', clean_value)
                        clean_value = re.sub(r'\{[0-9]+\}', '', clean_value)
                        clean_value = re.sub(r'\\n', ' ', clean_value)
                        clean_value = clean_value.strip()
                        
                        if clean_value:
                            text_samples.append(f"{key}: {clean_value}")
                            
                        if len(text_samples) >= 200:
                            break
        
        if not text_samples:
            return {"error": "No player-facing text found"}
        
        # Load context file if available
        context_text = self._load_context_file(lang_path)
        context_section = ""
        if context_text:
            click.echo("[Using game context file for enhanced analysis]")
            # Extract just the summary section
            if "CONTEXT SUMMARY:" in context_text:
                context_section = context_text.split("CONTEXT SUMMARY:")[1].split("="*60)[0].strip()
                context_section = f"\n\nGAME CONTEXT:\n{context_section}\n"
        
        # Prepare prompt for Ollama
        sample_text = '\n'.join(text_samples[:100])  # Use first 100 samples
        
        prompt = f"""You are analyzing a Minecraft world/game based on its language file text entries.{context_section}

Below are player-facing text strings from the game. Based on these strings{' and the provided context' if context_text else ''}, provide:

1. A brief description of what this Minecraft world/game is about (2-3 sentences)
2. The main theme or educational focus (if any)
3. Key features or gameplay elements mentioned
4. Target audience or age group - ANALYZE THE TEXT COMPLEXITY:
   - Look at vocabulary difficulty, sentence structure, and reading level
   - Consider word length, sentence length, and concept complexity
   - Base your age assessment ONLY on the actual text the player reads
   - Use standard reading level guidelines (e.g., simple words = younger, complex concepts = older)
5. Any unique or notable aspects

Language file entries:
{sample_text}

Provide a clear, concise analysis. For age group, be specific and base it solely on the text complexity you observe:"""

        try:
            # Progress indicator
            stop_spinner = threading.Event()
            spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            
            def show_spinner():
                """Show a spinner while processing."""
                idx = 0
                start_time = time.time()
                while not stop_spinner.is_set():
                    elapsed = int(time.time() - start_time)
                    click.echo(f'\r   {spinner_chars[idx % len(spinner_chars)]} Processing... ({elapsed}s elapsed)', nl=False)
                    idx += 1
                    time.sleep(0.1)
                click.echo('\r   Complete!                      ')
            
            # Start spinner in background
            spinner_thread = threading.Thread(target=show_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()
            
            # Call Ollama (increased timeout for larger models)
            result = subprocess.run(
                ['ollama', 'run', model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for larger models
            )
            
            # Stop spinner
            stop_spinner.set()
            spinner_thread.join(timeout=1)
            
            if result.returncode != 0:
                return {
                    "error": f"Ollama error: {result.stderr}",
                    "samples_analyzed": len(text_samples)
                }
            
            return {
                "model": model,
                "samples_analyzed": len(text_samples),
                "analysis": result.stdout.strip()
            }
            
        except subprocess.TimeoutExpired:
            stop_spinner.set()
            return {
                "error": "Ollama request timed out (5 minute limit). Try using a smaller/faster model.",
                "samples_analyzed": len(text_samples)
            }
        except FileNotFoundError:
            stop_spinner.set()
            return {
                "error": "Ollama not found. Please install Ollama first.",
                "samples_analyzed": len(text_samples)
            }
        except Exception as e:
            stop_spinner.set()
            return {
                "error": f"Unexpected error: {str(e)}",
                "samples_analyzed": len(text_samples)
            }


def check_ollama_installed() -> bool:
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(
            ['which', 'ollama'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_ollama_installation_instructions() -> str:
    """Get platform-specific Ollama installation instructions."""
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return """
Ollama Installation for macOS:

Option 1: Download from website (Recommended)
   1. Visit https://ollama.ai
   2. Click "Download for Mac"
   3. Open the downloaded .dmg file
   4. Drag Ollama to Applications
   5. Open Ollama from Applications

Option 2: Install via Homebrew
   Run: brew install ollama

After installation:
   1. Verify: ollama --version
   2. Start Ollama: ollama serve
   3. Install a model: ollama pull phi4
   4. Return to this tool and try AI features!
"""
    elif system == "Linux":
        return """
Ollama Installation for Linux:

Run this command in terminal:
   curl -fsSL https://ollama.ai/install.sh | sh

After installation:
   1. Verify: ollama --version
   2. Start Ollama: ollama serve
   3. Install a model: ollama pull phi4
   4. Return to this tool and try AI features!

For more details, visit: https://ollama.ai
"""
    elif system == "Windows":
        return """
Ollama Installation for Windows:

   1. Visit https://ollama.ai
   2. Click "Download for Windows"
   3. Run the installer
   4. Follow installation prompts

After installation:
   1. Open PowerShell or Command Prompt
   2. Verify: ollama --version
   3. Install a model: ollama pull phi4
   4. Return to this tool and try AI features!
"""
    else:
        return """
Ollama Installation:

   1. Visit https://ollama.ai
   2. Download the installer for your platform
   3. Follow the installation instructions

After installation:
   1. Verify: ollama --version
   2. Install a model: ollama pull phi4
   3. Return to this tool and try AI features!
"""


def show_settings_menu(tool: MinecraftLangTool):
    """Display and handle settings menu."""
    while True:
        click.echo("\n" + "="*50)
        click.echo("SETTINGS")
        click.echo("="*50)
        
        # Check Ollama status
        ollama_installed = check_ollama_installed()
        ollama_status = "Installed" if ollama_installed else "Not installed"
        
        click.echo(f"\nOllama Status: {ollama_status}")
        
        if ollama_installed:
            # Get available models
            models = tool.get_ollama_models()
            if models:
                click.echo(f"Available models: {len(models)}")
                click.echo("   " + ", ".join(models[:5]))
                if len(models) > 5:
                    click.echo(f"   ... and {len(models) - 5} more")
            else:
                click.echo("No models installed yet")
        
        click.echo("\n" + "-"*50)
        click.echo("1. Check Ollama installation")
        click.echo("2. Install Ollama (instructions)")
        click.echo("3. Install Ollama model")
        click.echo("4. List installed models")
        click.echo("0. Back to main menu")
        
        choice = click.prompt("\nSelect an option", type=int, default=0)
        
        if choice == 0:
            break
        elif choice == 1:
            # Check Ollama installation
            click.echo("\nChecking Ollama installation...")
            if check_ollama_installed():
                click.echo("[OK] Ollama is installed")
                
                # Try to get version
                try:
                    result = subprocess.run(
                        ['ollama', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        click.echo(f"Version: {result.stdout.strip()}")
                except Exception:
                    pass
                
                # Check for models
                models = tool.get_ollama_models()
                if models:
                    click.echo(f"\n[OK] {len(models)} model(s) installed")
                else:
                    click.echo("\n[WARNING] No models installed")
                    click.echo("Run 'ollama pull phi4' to install recommended model")
            else:
                click.echo("[NOT FOUND] Ollama is not installed")
                click.echo("\nChoose option 2 for installation instructions")
        
        elif choice == 2:
            # Show installation instructions
            instructions = get_ollama_installation_instructions()
            click.echo(instructions)
            
            if click.confirm("\nOpen Ollama website in browser?", default=False):
                import webbrowser
                webbrowser.open("https://ollama.ai")
                click.echo("Opened https://ollama.ai in your browser")
        
        elif choice == 3:
            # Install model
            if not check_ollama_installed():
                click.echo("\n[ERROR] Ollama is not installed")
                click.echo("Please install Ollama first (option 2)")
                continue
            
            click.echo("\nRecommended models:")
            click.echo("   phi4        - Best for educational content (recommended)")
            click.echo("   llama3.2    - Fast and capable")
            click.echo("   gemma2:2b   - Lightweight and fast")
            click.echo("   mistral     - Good general purpose")
            
            model_name = click.prompt("\nEnter model name to install", type=str, default="phi4")
            
            click.echo(f"\nInstalling {model_name}...")
            click.echo("This may take several minutes depending on model size...")
            
            try:
                result = subprocess.run(
                    ['ollama', 'pull', model_name],
                    capture_output=False,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if result.returncode == 0:
                    click.echo(f"\n[OK] Successfully installed {model_name}")
                else:
                    click.echo(f"\n[ERROR] Failed to install {model_name}")
            except subprocess.TimeoutExpired:
                click.echo("\n[ERROR] Installation timed out")
            except Exception as e:
                click.echo(f"\n[ERROR] {str(e)}")
        
        elif choice == 4:
            # List models
            if not check_ollama_installed():
                click.echo("\n[ERROR] Ollama is not installed")
                continue
            
            click.echo("\nFetching installed models...")
            models = tool.get_ollama_models()
            
            if models:
                click.echo(f"\nInstalled models ({len(models)}):")
                click.echo("-"*50)
                for i, model in enumerate(models, 1):
                    click.echo(f"{i}. {model}")
                click.echo("-"*50)
            else:
                click.echo("\n[WARNING] No models installed")
                click.echo("\nTo install a model, choose option 3")
                click.echo("Recommended: phi4")


def browse_downloads_folder() -> Optional[str]:
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


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
def cli():
    """Minecraft Language File Tool - Extract and process .lang files from Minecraft archives."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('--cache-dir', default='.mc_lang_cache', help='Directory for caching extracted files')
@click.option('--downloads', is_flag=True, help='Browse files in Downloads folder')
def process(input_file, cache_dir, downloads):
    """
    Process a Minecraft .mcworld, .mctemplate, or .lang file.
    
    Main command that provides access to all tool features through an
    interactive menu system. Supports direct lang file processing or
    extraction from Minecraft archives.
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
            click.echo("No .lang files found in the archive!")
            return
        
        click.echo(f"Found {len(lang_files)} .lang file(s)")
        
        # Let user select
        lang_file = tool.select_lang_file(lang_files)
        
        if not lang_file:
            click.echo("No file selected. Exiting.")
            return
    else:
        click.echo(f"Unsupported file type: {input_path.suffix}")
        click.echo("Supported types: .mcworld, .mctemplate, .lang")
        return
    
    # Main operations loop
    while True:
        # Show menu of operations
        click.echo("\n" + "="*50)
        click.echo("OPERATIONS MENU")
        click.echo("="*50)
        click.echo("1. Strip non-player-facing text")
        click.echo("2. Text complexity analysis")
        click.echo("3. Create game context file (using Ollama)")
        click.echo("4. AI content analysis (using Ollama)")
        click.echo("5. AI text improvement for target age (using Ollama)")
        click.echo("6. Generate quiz from game narrative (using Ollama)")
        click.echo("7. View full file contents")
        click.echo("8. Get file statistics")
        click.echo("9. Settings")
        click.echo("0. Exit")
        
        choice = click.prompt("\nSelect an operation", type=int, default=1)
        
        if choice == 0:
            break
        
        elif choice == 1:
            # Strip non-player text
            sanitized_stem = tool.sanitize_filename(lang_file.stem)
            output_path = Path(cache_dir) / f"{sanitized_stem}_player_only.lang"
            click.echo(f"\nStripping non-player-facing text...")
            removed = tool.strip_non_player_text(lang_file, output_path)
            click.echo(f"Removed {removed} lines")
            click.echo(f"Output saved to: {output_path}")
            
            # Show preview of output
            if click.confirm("\nPreview output file?", default=True):
                preview = tool.preview_lang_file(output_path, lines=10)
                click.echo("\nFirst 10 lines:")
                for line in preview:
                    click.echo(f"  {line}")
        
        elif choice == 2:
            # Text complexity analysis
            
            # Check if file appears to be en_US or English
            filename_lower = lang_file.name.lower()
            is_en_us = 'en_us' in filename_lower
            is_english = is_en_us or any(pattern in filename_lower for pattern in ['en_gb', 'en_ca', 'en_au', 'en.lang', 'english'])
            
            if not is_english:
                click.echo("\nWARNING: This file does not appear to be English (en_US).")
                click.echo("   Complexity analysis is designed for English text.")
                click.echo("   Results may be inaccurate for other languages.\n")
                if not click.confirm("Continue anyway?", default=False):
                    click.echo("Analysis cancelled.")
                    return
            elif not is_en_us:
                click.echo(f"\nNote: Analyzing {lang_file.name} (not en_US).")
                click.echo("Results are most accurate with en_US files.\n")
            
            click.echo(f"\nAnalyzing text complexity for player-facing content...")
            click.echo("This may take a moment...\n")
            
            # Option to preview what text will be analyzed
            if click.confirm("Preview sample of text that will be analyzed?", default=False):
                preview_texts = tool._get_preview_analyzed_text(lang_file, lines=20)
                if preview_texts:
                    click.echo("\nSample of text being analyzed:")
                    click.echo("-" * 60)
                    for i, text in enumerate(preview_texts, 1):
                        click.echo(f"{i}. {text}")
                    click.echo("-" * 60)
                    if not click.confirm("\nContinue with full analysis?", default=True):
                        click.echo("Analysis cancelled.")
                        return
                click.echo()
            
            analysis = tool.analyze_text_complexity(lang_file)
            
            if 'error' in analysis:
                click.echo(f"Error: {analysis['error']}")
            else:
                # Display results
                click.echo("="*70)
                click.echo("TEXT COMPLEXITY ANALYSIS REPORT")
                click.echo("="*70)
                
                click.echo(f"\nBASIC STATISTICS")
                click.echo(f"   Player-facing text entries analyzed: {analysis['total_entries']:,}")
                click.echo(f"   Technical entries skipped: {analysis['skipped_technical']:,}")
                click.echo(f"   Total words: {analysis['total_words']:,}")
                click.echo(f"   Unique words: {analysis['unique_words']:,}")
                click.echo(f"   Total sentences: {analysis['total_sentences']:,}")
                click.echo(f"   Average word length: {analysis['avg_word_length']} characters")
                click.echo(f"   Average sentence length: {analysis['avg_sentence_length']} words")
                click.echo(f"   Average syllables per word: {analysis['avg_syllables_per_word']}")
                
                click.echo(f"\nREADABILITY METRICS")
                click.echo(f"   Flesch Reading Ease: {analysis['flesch_reading_ease']}")
                click.echo(f"      (0-100 scale, higher = easier)")
                click.echo(f"   Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']}")
                click.echo(f"   Gunning Fog Index: {analysis['gunning_fog_index']}")
                if analysis['smog_index']:
                    click.echo(f"   SMOG Index: {analysis['smog_index']}")
                else:
                    click.echo(f"   SMOG Index: N/A (requires 30+ sentences)")
                click.echo(f"   Coleman-Liau Index: {analysis['coleman_liau_index']}")
                click.echo(f"   Automated Readability Index: {analysis['automated_readability_index']}")
                
                click.echo(f"\nOVERALL ASSESSMENT")
                click.echo(f"   Grade Level: {analysis['grade_level']}")
                click.echo(f"   Target Age Range: {analysis['age_range']}")
                click.echo(f"   Difficulty: {analysis['difficulty']}")
                
                click.echo(f"\nVOCABULARY COMPLEXITY")
                vc = analysis['vocabulary_complexity']
                click.echo(f"   Short words (1-3 chars): {vc['short_words_1_3']:,} ({vc['short_words_1_3']/analysis['total_words']*100:.1f}%)")
                click.echo(f"   Medium words (4-6 chars): {vc['medium_words_4_6']:,} ({vc['medium_words_4_6']/analysis['total_words']*100:.1f}%)")
                click.echo(f"   Long words (7+ chars): {vc['long_words_7_plus']:,} ({vc['long_words_7_plus']/analysis['total_words']*100:.1f}%)")
                click.echo(f"   Complex words (3+ syllables): {vc['complex_words_3plus_syllables']:,} ({vc['complex_words_3plus_syllables']/analysis['total_words']*100:.1f}%)")
                click.echo(f"   Lexical diversity: {vc['lexical_diversity']}")
                click.echo(f"      (unique words / total words)")
                
                click.echo("\n" + "="*70)
                
                # Ask if user wants to save report
                if click.confirm("\nSave detailed report to file?", default=False):
                    report_path = Path(cache_dir) / f"{lang_file.stem}_complexity_report.txt"
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write("TEXT COMPLEXITY ANALYSIS REPORT\n")
                        f.write("="*70 + "\n")
                        f.write(f"File: {lang_file.name}\n")
                        f.write(f"Analysis Date: {Path(report_path).stat().st_mtime}\n\n")
                        
                        f.write("BASIC STATISTICS\n")
                        f.write(f"  Player-facing text entries: {analysis['total_entries']:,}\n")
                        f.write(f"  Total words: {analysis['total_words']:,}\n")
                        f.write(f"  Unique words: {analysis['unique_words']:,}\n")
                        f.write(f"  Total sentences: {analysis['total_sentences']:,}\n")
                        f.write(f"  Average word length: {analysis['avg_word_length']} characters\n")
                        f.write(f"  Average sentence length: {analysis['avg_sentence_length']} words\n")
                        f.write(f"  Average syllables per word: {analysis['avg_syllables_per_word']}\n\n")
                        
                        f.write("READABILITY METRICS\n")
                        f.write(f"  Flesch Reading Ease: {analysis['flesch_reading_ease']}\n")
                        f.write(f"  Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']}\n")
                        f.write(f"  Gunning Fog Index: {analysis['gunning_fog_index']}\n")
                        f.write(f"  SMOG Index: {analysis['smog_index'] if analysis['smog_index'] else 'N/A'}\n")
                        f.write(f"  Coleman-Liau Index: {analysis['coleman_liau_index']}\n")
                        f.write(f"  Automated Readability Index: {analysis['automated_readability_index']}\n\n")
                        
                        f.write("OVERALL ASSESSMENT\n")
                        f.write(f"  Grade Level: {analysis['grade_level']}\n")
                        f.write(f"  Target Age Range: {analysis['age_range']}\n")
                        f.write(f"  Difficulty: {analysis['difficulty']}\n\n")
                        
                        f.write("VOCABULARY COMPLEXITY\n")
                        f.write(f"  Short words (1-3 chars): {vc['short_words_1_3']:,}\n")
                        f.write(f"  Medium words (4-6 chars): {vc['medium_words_4_6']:,}\n")
                        f.write(f"  Long words (7+ chars): {vc['long_words_7_plus']:,}\n")
                        f.write(f"  Complex words (3+ syllables): {vc['complex_words_3plus_syllables']:,}\n")
                        f.write(f"  Lexical diversity: {vc['lexical_diversity']}\n")
                    
                    click.echo(f"Report saved to: {report_path}")
    
        elif choice == 3:
            # Create game context file
            click.echo(f"\nCreate Game Context File using Ollama")
            click.echo("="*60)
            
            # Check for Ollama and get models
            click.echo("Checking for available Ollama models...")
            models = tool.get_ollama_models()
            
            if not models:
                click.echo("\nNo Ollama models found!")
                click.echo("   Please install Ollama and download a model first.")
                click.echo("   Visit: https://ollama.ai")
                click.echo("\n   Quick start:")
                click.echo("      1. Install Ollama")
                click.echo("      2. Run: ollama pull phi4")
                click.echo("      3. Run this tool again")
                return
            
            # Display available models
            click.echo(f"\nFound {len(models)} model(s):")
            for i, model in enumerate(models, 1):
                click.echo(f"   {i}. {model}")
            
            if len(models) == 1:
                model_choice = 1
                click.echo(f"\nUsing model: {models[0]}")
            else:
                model_choice = click.prompt("\nSelect model number", type=int, default=1)
                if model_choice < 1 or model_choice > len(models):
                    click.echo("Invalid choice!")
                    return
            
            selected_model = models[model_choice - 1]
            
            # Create context file
            result = tool.create_context_file(lang_file, selected_model)
            
            if 'error' in result:
                click.echo(f"\nError: {result['error']}")
            elif result.get('status') == 'cancelled':
                click.echo(f"\n{result['message']}")
            else:
                click.echo(f"\n{'='*60}")
                click.echo("CONTEXT FILE SUMMARY")
                click.echo(f"{'='*60}")
                click.echo(f"\nQuestions asked: {len(result['questions'])}")
                click.echo(f"Context file: {result['context_file']}")
                click.echo(f"\nThis context will now be used to enhance:")
                click.echo("   • AI content analysis")
                click.echo("   • Quiz generation")
                click.echo("   • Text improvements")
                click.echo(f"\n{'='*60}")
        
        elif choice == 4:
            # AI content analysis with Ollama
            click.echo(f"\nAI Content Analysis using Ollama")
            click.echo("="*60)
            
            # Check for Ollama and get models
            click.echo("Checking for available Ollama models...")
            models = tool.get_ollama_models()
            
            if not models:
                click.echo("\nNo Ollama models found!")
                click.echo("   Please install Ollama and download a model first.")
                click.echo("   Visit: https://ollama.ai")
                click.echo("\n   Quick start:")
                click.echo("   1. Install Ollama")
                click.echo("   2. Run: ollama pull llama3.2")
                return
            
            click.echo(f"\nFound {len(models)} model(s):")
            for idx, model in enumerate(models, 1):
                # Add speed indicator based on model size
                if any(size in model for size in ['70b', '72b', '90b', '405b']):
                    speed = "slow but thorough"
                elif any(size in model for size in ['13b', '14b', '34b']):
                    speed = "moderate speed"
                elif any(size in model for size in ['7b', '8b', '3b', '1b']):
                    speed = "fast"
                else:
                    speed = ""
                
                if speed:
                    click.echo(f"   {idx}. {model} ({speed})")
                else:
                    click.echo(f"   {idx}. {model}")
            
            # Let user select model
            model_choice = click.prompt(
                "\nSelect a model number",
                type=int,
                default=1
            )
            
            if model_choice < 1 or model_choice > len(models):
                click.echo("Invalid model selection.")
                return
            
            selected_model = models[model_choice - 1]
            
            # Show model size/speed hint
            if any(size in selected_model for size in ['70b', '72b', '90b', '405b']):
                speed_hint = "Large model detected - may take 2-5 minutes"
            elif any(size in selected_model for size in ['13b', '14b', '34b']):
                speed_hint = "Medium model - typically 1-2 minutes"
            else:
                speed_hint = "Small model - typically 30-90 seconds"
            
            click.echo(f"\nUsing model: {selected_model}")
            click.echo(f"{speed_hint}")
            click.echo("\n" + "="*60)
            click.echo("AI ANALYSIS IN PROGRESS")
            click.echo("="*60)
            click.echo("Step 1/2: Extracting player-facing text samples...")
            click.echo("Step 2/2: Analyzing with AI...")
            click.echo("           (Maximum wait time: 5 minutes)")
            
            # Run analysis (will show spinner during processing)
            result = tool.analyze_with_ollama(lang_file, selected_model)
            
            click.echo("\nAnalysis complete!\n")
            
            if 'error' in result:
                click.echo(f"\nError: {result['error']}")
                if 'samples_analyzed' in result:
                    click.echo(f"   Text samples found: {result['samples_analyzed']}")
            else:
                click.echo("="*60)
                click.echo("AI GAME CONTENT ANALYSIS")
                click.echo("="*60)
                click.echo(f"\nModel: {result['model']}")
                click.echo(f"Text samples analyzed: {result['samples_analyzed']}")
                click.echo("\n" + "-"*60)
                click.echo(result['analysis'])
                click.echo("-"*60)
                
                # Ask if user wants to save
                if click.confirm("\nSave analysis to file?", default=False):
                    analysis_path = Path(cache_dir) / f"{lang_file.stem}_ai_analysis.txt"
                    with open(analysis_path, 'w', encoding='utf-8') as f:
                        f.write("AI GAME CONTENT ANALYSIS\n")
                        f.write("="*60 + "\n")
                        f.write(f"File: {lang_file.name}\n")
                        f.write(f"Model: {result['model']}\n")
                        f.write(f"Text samples analyzed: {result['samples_analyzed']}\n")
                        f.write("\n" + "-"*60 + "\n")
                        f.write(result['analysis'])
                        f.write("\n" + "-"*60 + "\n")
                    
                    click.echo(f"Analysis saved to: {analysis_path}")
        
        elif choice == 5:
            # AI text improvement for target age
            click.echo(f"\nAI Text Improvement for Target Age")
            click.echo("="*60)
            
            # Check for Ollama and get models
            click.echo("Checking for available Ollama models...")
            models = tool.get_ollama_models()
            
            if not models:
                click.echo("\nNo Ollama models found!")
                click.echo("   Please install Ollama and download a model first.")
                click.echo("   Visit: https://ollama.ai")
                return
            
            click.echo(f"\nFound {len(models)} model(s):")
            for idx, model in enumerate(models, 1):
                if any(size in model for size in ['70b', '72b', '90b', '405b']):
                    speed = "slow but thorough"
                elif any(size in model for size in ['13b', '14b', '34b']):
                    speed = "moderate speed"
                elif any(size in model for size in ['7b', '8b', '3b', '1b']):
                    speed = "fast"
                else:
                    speed = ""
                
                if speed:
                    click.echo(f"   {idx}. {model} ({speed})")
                else:
                    click.echo(f"   {idx}. {model}")
            
            model_choice = click.prompt("\nSelect a model number", type=int, default=1)
            
            if model_choice < 1 or model_choice > len(models):
                click.echo("Invalid model selection.")
                return
            
            selected_model = models[model_choice - 1]
            
            # Get target age from user
            target_age = click.prompt("\nEnter target age for text improvement (e.g., 8, 10, 12, 14)", type=int, default=10)
            
            click.echo(f"\nUsing model: {selected_model}")
            click.echo(f"Target age: {target_age} years old")
            click.echo("\nThis will:")
            click.echo("  1. Analyze each line to determine if it's player-facing")
            click.echo(f"  2. Improve text readability for age {target_age}")
            click.echo("  3. Preserve all technical formatting and keys")
            click.echo("  4. Generate a new lang file and changelog")
            click.echo("\nNote: This may take several minutes for large files.")
            click.echo("      You can monitor progress by opening the changelog file during processing.")
            
            if not click.confirm("\nProceed with AI text improvement?", default=True):
                click.echo("Cancelled.")
                return
            
            # Show changelog path before starting
            lang_path_obj = Path(lang_file)
            changelog_filename = lang_path_obj.stem + f"_changelog_age{target_age}.txt"
            changelog_dir = lang_path_obj.parent / "improvements"
            changelog_preview_path = changelog_dir / changelog_filename
            
            click.echo("\n" + "="*60)
            click.echo("AI TEXT IMPROVEMENT IN PROGRESS")
            click.echo("="*60)
            click.echo(f"\nChangelog: file://{changelog_preview_path.absolute()}")
            click.echo("(Click the link above to open and monitor progress)\n")
            
            result = tool.improve_text_for_age(lang_file, selected_model, target_age)
            
            if 'error' in result:
                click.echo(f"\nError: {result['error']}")
            else:
                click.echo("\nImprovement complete!")
                click.echo("="*60)
                click.echo(f"Lines processed: {result['lines_processed']}")
                click.echo(f"Lines improved: {result['lines_improved']}")
                click.echo(f"Lines unchanged: {result['lines_unchanged']}")
                click.echo(f"\nNew file: {result['output_file']}")
                click.echo(f"Changelog: {result['changelog_file']}")
                click.echo("="*60)
                
                # Show sample changes
                if result['lines_improved'] > 0 and click.confirm("\nPreview sample changes?", default=True):
                    changelog_path = Path(result['changelog_file'])
                    with open(changelog_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        preview_lines = min(20, len(lines))
                        click.echo(f"\nFirst {preview_lines} lines of changelog:")
                        click.echo("-" * 60)
                        for line in lines[:preview_lines]:
                            click.echo(line.rstrip())
                        if len(lines) > preview_lines:
                            click.echo(f"... ({len(lines) - preview_lines} more changes)")
                        click.echo("-" * 60)
        
        elif choice == 6:
            # Generate quiz from game narrative
            click.echo(f"\nGenerate Quiz from Game Narrative")
            click.echo("="*60)
            
            # Check for Ollama and get models
            click.echo("Checking for available Ollama models...")
            models = tool.get_ollama_models()
            
            if not models:
                click.echo("\nNo Ollama models found!")
                click.echo("   Please install Ollama and download a model first.")
                click.echo("   Visit: https://ollama.ai")
                return
            
            click.echo(f"\nFound {len(models)} model(s):")
            for idx, model in enumerate(models, 1):
                if any(size in model for size in ['70b', '72b', '90b', '405b']):
                    speed = "slow but thorough"
                elif any(size in model for size in ['13b', '14b', '34b']):
                    speed = "moderate speed"
                elif any(size in model for size in ['7b', '8b', '3b', '1b']):
                    speed = "fast"
                else:
                    speed = ""
                
                if speed:
                    click.echo(f"   {idx}. {model} ({speed})")
                else:
                    click.echo(f"   {idx}. {model}")
            
            model_choice = click.prompt("\nSelect a model number", type=int, default=1)
            
            if model_choice < 1 or model_choice > len(models):
                click.echo("Invalid model selection.")
                return
            
            selected_model = models[model_choice - 1]
            
            # Get target age from user
            target_age = click.prompt("\nEnter target age for quiz language (e.g., 8, 10, 12, 14)", type=int, default=10)
            
            click.echo(f"\nUsing model: {selected_model}")
            click.echo(f"Target age: {target_age} years old")
            click.echo("\nThis will generate a 10-question multiple choice quiz based on the game narrative.")
            click.echo("Each question is worth 1 mark.")
            
            if not click.confirm("\nProceed with quiz generation?", default=True):
                click.echo("Cancelled.")
                return
            
            click.echo("\n" + "="*60)
            click.echo("GENERATING QUIZ")
            click.echo("="*60)
            
            result = tool.generate_quiz(lang_file, selected_model, target_age)
            
            if 'error' in result:
                click.echo(f"\nError: {result['error']}")
            else:
                click.echo("\nQuiz generated successfully!")
                click.echo("="*60)
                click.echo(f"Quiz file: {result['quiz_file']}")
                click.echo(f"Answer key: {result['answer_key_file']}")
                click.echo("="*60)
                
                # Show preview of quiz
                if click.confirm("\nPreview quiz?", default=True):
                    with open(result['quiz_file'], 'r', encoding='utf-8') as f:
                        quiz_content = f.read()
                        click.echo("\n" + "="*60)
                        click.echo(quiz_content)
                        click.echo("="*60)
        
        elif choice == 7:
            # View full contents
            with open(lang_file, 'r', encoding='utf-8') as f:
                content = f.read()
                click.echo_via_pager(content)
        
        elif choice == 8:
            # File statistics
            with open(lang_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_lines = len(lines)
                entry_lines = sum(1 for line in lines if '=' in line and not line.strip().startswith('#'))
                comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//'))
                empty_lines = sum(1 for line in lines if not line.strip())
            
            click.echo(f"\nFile Statistics for {lang_file.name}:")
            click.echo(f"  Total lines: {total_lines}")
            click.echo(f"  Entry lines: {entry_lines}")
            click.echo(f"  Comment lines: {comment_lines}")
            click.echo(f"  Empty lines: {empty_lines}")
            click.echo(f"  File size: {lang_file.stat().st_size:,} bytes")
        
        elif choice == 9:
            # Settings menu
            show_settings_menu(tool)
    
    click.echo("\nDone!")


@cli.command()
@click.option('--cache-dir', default='.mc_lang_cache', help='Directory for caching extracted files')
def clear_cache(cache_dir):
    """Clear the extraction cache."""
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        click.echo("Cache directory does not exist.")
        return
    
    if click.confirm(f"Delete cache directory '{cache_dir}' and all its contents?"):
        shutil.rmtree(cache_path)
        click.echo("Cache cleared!")
    else:
        click.echo("Cancelled.")


if __name__ == '__main__':
    cli()

# ============================================================================
# End of Minecraft Language File Tool
# Created by Justin Edwards (jnredwards@gmail.com)
# Released under MIT License
# ============================================================================
