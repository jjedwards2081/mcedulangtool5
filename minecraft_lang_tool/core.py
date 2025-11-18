#!/usr/bin/env python3
"""
Minecraft Language File Tool - Core Processing Module

This module contains the core logic for processing Minecraft .lang files
and is designed to be used by Regolith or other automation tools.

Author: Justin Edwards
Email: jnredwards@gmail.com
License: MIT License

Copyright (c) 2025 Justin Edwards
"""

import re
import json
import time
import zipfile
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from collections import Counter


class MinecraftLangTool:
    """
    Core class for processing Minecraft Education Edition language files.
    
    This tool provides functionality to:
    - Extract .mcworld and .mctemplate archives
    - Locate and parse .lang files
    - Analyze text complexity and readability
    - Improve text for specific target ages using AI
    - Generate educational quizzes from game content
    - Analyze content themes using Ollama AI models
    
    Designed to work with JSON configuration for Regolith integration.
    """
    
    def __init__(self, cache_dir: str = ".mc_lang_cache"):
        """Initialize the Minecraft Language Tool with a cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
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
            return extract_dir
        
        # Both .mcworld and .mctemplate are ZIP files
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
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
    
    def strip_non_player_text(self, lang_path: Path, output_path: Path) -> int:
        """
        Copy lang file, removing only comments and empty lines.
        
        Keeps all key-value entries from the original file.
        """
        kept_lines = []
        removed_count = 0
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                removed_count += 1
                continue
            
            if '=' in stripped:
                kept_lines.append(line)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
        
        return removed_count
    
    def _get_preview_analyzed_text(self, lang_path: Path, lines: int = 20) -> List[str]:
        """Get a preview of text that will be analyzed for complexity."""
        text_values = []
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if len(text_values) >= lines:
                        break
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        cleaned = self._clean_text_for_analysis(value)
                        if cleaned:
                            text_values.append(cleaned)
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f):
                    if len(text_values) >= lines:
                        break
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        cleaned = self._clean_text_for_analysis(value)
                        if cleaned:
                            text_values.append(cleaned)
        
        return text_values
    
    def analyze_text_complexity(self, lang_path: Path) -> Dict:
        """
        Perform comprehensive text complexity analysis on all text in the lang file.
        
        Uses multiple established readability formulas to assess the reading level
        of game text. Particularly useful for educators to determine if content
        is appropriate for their students' reading abilities.
        
        Returns:
            dict: Comprehensive analysis including all readability scores
        """
        # Extract all text values
        text_values = []
        skipped_technical = 0
        
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
                        
                        # Clean the text value
                        cleaned = self._clean_text_for_analysis(value)
                        if cleaned and len(cleaned.split()) >= 2:
                            text_values.append(cleaned)
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
                        
                        cleaned = self._clean_text_for_analysis(value)
                        if cleaned and len(cleaned.split()) >= 2:
                            text_values.append(cleaned)
                        else:
                            skipped_technical += 1
        
        if not text_values:
            return {"error": "No analyzable text found"}
        
        # Initialize analysis dictionary
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
        
        # Treat each text entry as a sentence
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
        text = re.sub(r'§[0-9a-fk-or]', '', text)
        text = re.sub(r'%[0-9]+\$?[sdifgx]', '', text)
        text = re.sub(r'%\([^)]+\)[sd]', '', text)
        text = re.sub(r'\{[0-9]+\}', '', text)
        text = re.sub(r'\{\w+\}', '', text)
        text = re.sub(r'\\n', ' ', text)
        text = re.sub(r'\\t', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[_{}()\[\]<>|\\/@#$%^&*+=~`]', ' ', text)
        text = re.sub(r'\b\d+(\.\d+)*\b', '', text)
        text = re.sub(r'\b[a-z]+[A-Z][a-zA-Z]*\b', '', text)
        text = re.sub(r'\b\w+_\w+\b', '', text)
        text = re.sub(r'\b[a-zA-Z]\b', '', text)
        text = re.sub(r'\b(fps|fov|gui|api|rgb|xyz|pos|vec|nbt|uuid|id)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        
        words = text.split()
        if len(words) >= 2 and len(text) >= len(original_text) * 0.3:
            return text
        
        return ""
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text (letters only)."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        if word.endswith('e'):
            syllable_count -= 1
        
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            syllable_count += 1
        
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
        
        # Adjust for vocabulary complexity
        vocab = analysis['vocabulary_complexity']
        total_words = analysis['total_words']
        
        if total_words > 0:
            long_word_ratio = vocab['long_words_7_plus'] / total_words
            complex_word_ratio = vocab['complex_words_3plus_syllables'] / total_words
            vocab_adjustment = (long_word_ratio * 1.5 + complex_word_ratio * 1.5) * 2
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
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            lines = result.stdout.strip().split('\n')
            models = []
            
            for line in lines[1:]:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            
            return models
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    
    def improve_text_for_age(self, lang_path: Path, model_name: str, target_age: int, 
                            output_path: Optional[Path] = None, 
                            changelog_path: Optional[Path] = None) -> Dict:
        """
        Use Ollama AI to improve text in lang file for specific target age.
        
        Args:
            lang_path: Path to the lang file to improve
            model_name: Name of the Ollama model to use
            target_age: Target age for text improvements
            output_path: Optional custom output path
            changelog_path: Optional custom changelog path
            
        Returns:
            dict: Results including output files and statistics
        """
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return {'error': f"Failed to read file: {str(e)}"}
        
        # Prepare output files
        lang_path_obj = Path(lang_path)
        sanitized_stem = self.sanitize_filename(lang_path_obj.stem)
        
        if output_path is None:
            output_filename = sanitized_stem + f"_improved_age{target_age}" + lang_path_obj.suffix
            output_path = lang_path_obj.parent / output_filename
        
        if changelog_path is None:
            changelog_dir = lang_path_obj.parent / "improvements"
            changelog_dir.mkdir(exist_ok=True)
            changelog_filename = sanitized_stem + f"_changelog_age_{target_age}.txt"
            changelog_path = changelog_dir / changelog_filename
        
        improved_lines = []
        lines_processed = 0
        lines_improved = 0
        lines_unchanged = 0
        
        # Initialize changelog
        try:
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(f"Text Improvement Changelog - Age {target_age}\n")
                f.write(f"Model: {model_name}\n")
                f.write(f"Source: {lang_path}\n")
                f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
        except Exception as e:
            return {'error': f"Failed to create changelog file: {str(e)}"}
        
        # Process each line through Ollama
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Keep comments and empty lines as-is
            if not stripped or stripped.startswith('#'):
                improved_lines.append(line)
                continue
            
            # Check if line contains key=value pair
            if '=' not in stripped:
                improved_lines.append(line)
                continue
            
            try:
                key, value = stripped.split('=', 1)
                key = key.strip()
                value = value.strip()
            except ValueError:
                improved_lines.append(line)
                continue
            
            # Clean and check if text is worth improving
            cleaned = self._clean_text_for_analysis(value)
            if not cleaned or len(cleaned.split()) < 2:
                improved_lines.append(line)
                continue
            
            lines_processed += 1
            
            # Create prompt for Ollama to improve this specific text
            prompt = f"""You are helping to rewrite game text to be more appropriate and engaging for a {target_age}-year-old audience.

Original text: {value}

Please rewrite this text to be:
1. Clear and easy to understand for a {target_age}-year-old
2. Engaging and interesting
3. Slightly shorter if possible
4. Maintaining the original meaning and context

Provide ONLY the improved text, nothing else. No explanations, no quotes, just the improved text."""

            try:
                result = subprocess.run(
                    ['ollama', 'run', model_name, prompt],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60
                )
                
                if result.returncode == 0:
                    improved_value = result.stdout.strip()
                    
                    # Only use improvement if it's reasonable (not empty, not too long)
                    if improved_value and len(improved_value) > 0 and len(improved_value) < len(value) * 2:
                        improved_line = f"{key}={improved_value}\n"
                        improved_lines.append(improved_line)
                        lines_improved += 1
                        
                        # Log to changelog
                        try:
                            with open(changelog_path, 'a', encoding='utf-8') as f:
                                f.write(f"Line {line_num}:\n")
                                f.write(f"  Original:  {value}\n")
                                f.write(f"  Improved:  {improved_value}\n\n")
                        except Exception:
                            pass
                    else:
                        # Keep original if improvement didn't work well
                        improved_lines.append(line)
                        lines_unchanged += 1
                else:
                    # Keep original on error
                    improved_lines.append(line)
                    lines_unchanged += 1
            
            except subprocess.TimeoutExpired:
                # Keep original on timeout
                improved_lines.append(line)
                lines_unchanged += 1
            except Exception:
                # Keep original on any error
                improved_lines.append(line)
                lines_unchanged += 1
        
        # Write improved file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(improved_lines)
        except Exception as e:
            return {'error': f"Failed to write improved file: {str(e)}"}
        
        # Finalize changelog
        try:
            success_rate = (lines_improved/lines_processed*100) if lines_processed > 0 else 0
            with open(changelog_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "="*60 + "\n")
                f.write("SUMMARY\n")
                f.write("="*60 + "\n")
                f.write(f"Total lines processed: {lines_processed}\n")
                f.write(f"Lines improved: {lines_improved}\n")
                f.write(f"Lines unchanged: {lines_unchanged}\n")
                f.write(f"Success rate: {success_rate:.1f}%\n")
        except Exception as e:
            return {'error': f"Failed to finalize changelog: {str(e)}"}
        
        return {
            'output_file': str(output_path),
            'changelog_file': str(changelog_path),
            'lines_processed': lines_processed,
            'lines_improved': lines_improved,
            'lines_unchanged': lines_unchanged
        }
    
    def generate_quiz(self, lang_path: Path, model_name: str, target_age: int,
                     output_dir: Optional[Path] = None) -> Dict:
        """
        Generate a 10-question multiple choice quiz based on game narrative.
        
        Args:
            lang_path: Path to the lang file
            model_name: Name of the Ollama model to use
            target_age: Target age for quiz language
            output_dir: Optional custom output directory
            
        Returns:
            dict: Results including quiz file paths or error
        """
        narrative_texts = []
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        cleaned = self._clean_text_for_analysis(value)
                        if cleaned and len(cleaned) > 20:
                            narrative_texts.append(cleaned)
        except Exception as e:
            return {'error': f"Failed to read file: {str(e)}"}
        
        if not narrative_texts:
            return {'error': "No narrative text found in lang file"}
        
        narrative_sample = '\n'.join(narrative_texts[:100])
        
        prompt = f"""You are creating a 10-question multiple choice quiz for a {target_age}-year-old student based on this educational Minecraft game narrative.

GAME NARRATIVE:
{narrative_sample}

TASK: Create a quiz with exactly 10 questions that test comprehension and understanding of the game content.

REQUIREMENTS:
1. Each question must have 4 answer choices (A, B, C, D)
2. Only ONE correct answer per question
3. Language must be appropriate for age {target_age}
4. Questions should test understanding of game objectives, characters, locations, and concepts
5. Total: 10 marks (1 mark per question)

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

QUIZ: [Game Name] Comprehension Quiz
Target Age: {target_age}
Total Marks: 10

Question 1: [Your question]
A) [Answer A]
B) [Answer B]
C) [Answer C]
D) [Answer D]

[Continue for all 10 questions]

ANSWER KEY:
1. [Letter]
2. [Letter]
...
10. [Letter]"""

        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            
            if result.returncode != 0:
                return {'error': f"Ollama failed: {result.stderr}"}
            
            quiz_content = result.stdout.strip()
            
            if not quiz_content or len(quiz_content) < 100:
                return {'error': "Quiz generation produced invalid output"}
        
        except subprocess.TimeoutExpired:
            return {'error': "Quiz generation timed out"}
        except FileNotFoundError:
            return {'error': "Ollama not found"}
        except Exception as e:
            return {'error': f"Failed to generate quiz: {str(e)}"}
        
        # Split quiz and answer key
        quiz_text = quiz_content
        answer_key_text = ""
        
        if "ANSWER KEY:" in quiz_content:
            parts = quiz_content.split("ANSWER KEY:")
            quiz_text = parts[0].strip()
            answer_key_text = "ANSWER KEY:\n" + parts[1].strip()
        
        # Save files
        lang_path_obj = Path(lang_path)
        sanitized_stem = self.sanitize_filename(lang_path_obj.stem)
        
        if output_dir is None:
            output_dir = lang_path_obj.parent / "quizzes"
        
        output_dir.mkdir(exist_ok=True)
        
        quiz_filename = sanitized_stem + f"_quiz_age{target_age}.txt"
        answer_key_filename = sanitized_stem + f"_quiz_age{target_age}_answers.txt"
        
        quiz_path = output_dir / quiz_filename
        answer_key_path = output_dir / answer_key_filename
        
        try:
            with open(quiz_path, 'w', encoding='utf-8') as f:
                f.write(quiz_text)
            
            with open(answer_key_path, 'w', encoding='utf-8') as f:
                f.write(answer_key_text)
        except Exception as e:
            return {'error': f"Failed to save quiz files: {str(e)}"}
        
        return {
            'quiz_file': str(quiz_path),
            'answer_key_file': str(answer_key_path)
        }
    
    def analyze_with_ollama(self, lang_path: Path, model: str) -> Dict:
        """Use Ollama to analyze game content from player-facing text."""
        text_samples = []
        skip_prefixes = ['debug.', 'key.keyboard.', 'translation.test.', 'generator.']
        
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if not any(key.strip().startswith(prefix) for prefix in skip_prefixes):
                            cleaned = self._clean_text_for_analysis(value)
                            if cleaned:
                                text_samples.append(cleaned)
        except UnicodeDecodeError:
            with open(lang_path, 'r', encoding='latin-1') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if not any(key.strip().startswith(prefix) for prefix in skip_prefixes):
                            cleaned = self._clean_text_for_analysis(value)
                            if cleaned:
                                text_samples.append(cleaned)
        
        if not text_samples:
            return {"error": "No player-facing text found"}
        
        sample_text = '\n'.join(text_samples[:100])
        
        prompt = f"""You are analyzing a Minecraft world/game based on its language file text entries. 
Based on these strings, provide:

1. A brief description of what this Minecraft world/game is about (2-3 sentences)
2. The main theme or educational focus (if any)
3. Key features or gameplay elements mentioned
4. Target audience or age group based on text complexity
5. Any unique or notable aspects

Language file entries:
{sample_text}

Provide a clear, concise analysis:"""

        try:
            result = subprocess.run(
                ['ollama', 'run', model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            
            if result.returncode != 0:
                return {
                    "error": f"Ollama failed: {result.stderr}",
                    "samples_analyzed": len(text_samples)
                }
            
            return {
                "model": model,
                "samples_analyzed": len(text_samples),
                "analysis": result.stdout.strip()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "error": "Ollama request timed out (5 minute limit)",
                "samples_analyzed": len(text_samples)
            }
        except FileNotFoundError:
            return {
                "error": "Ollama not found",
                "samples_analyzed": len(text_samples)
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "samples_analyzed": len(text_samples)
            }
    
    def process_from_config(self, config_json: str) -> Dict:
        """
        Main entry point for processing with JSON configuration.
        
        This method is designed for Regolith integration and accepts
        parameters as a JSON string.
        
        Args:
            config_json: JSON string containing:
                - operation: str (required) - One of: 'strip', 'analyze', 'improve', 'quiz', 'ai_analyze'
                - input_file: str (required) - Path to input file (.mcworld/.mctemplate/.lang)
                - cache_dir: str (optional) - Cache directory path
                - output_file: str (optional) - Output file path (usage varies by operation)
                - model_name: str (optional) - Ollama model for AI operations
                - target_age: int (optional) - Target age for improvement/quiz
                
        Returns:
            dict: Results of the operation including output paths and statistics
        """
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON configuration: {str(e)}', 'success': False}
        
        operation = config.get('operation')
        input_file = config.get('input_file')
        
        if not operation or not input_file:
            return {'error': 'Missing required parameters: operation and input_file'}
        
        # Set cache directory
        if 'cache_dir' in config:
            self.cache_dir = Path(config['cache_dir'])
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = Path(input_file)
        
        # Handle different input types
        if input_path.suffix.lower() == '.lang':
            lang_file = input_path
        elif input_path.suffix.lower() in ['.mcworld', '.mctemplate']:
            try:
                extract_dir = self.extract_archive(str(input_path))
                lang_files = self.find_lang_files(extract_dir)
                
                if not lang_files:
                    return {'error': 'No .lang files found in archive'}
                
                # Use the first (most appropriate) lang file
                lang_file = lang_files[0][0]
            except Exception as e:
                return {'error': f'Failed to extract archive: {str(e)}'}
        else:
            return {'error': f'Unsupported file type: {input_path.suffix}'}
        
        # Execute requested operation
        result = None
        
        if operation == 'strip':
            output_path = Path(config.get('output_file', str(lang_file.parent / 'output_player_only.lang')))
            removed = self.strip_non_player_text(lang_file, output_path)
            abs_path = output_path.resolve()
            print(f"Stripped .lang file saved to: {abs_path}")
            result = {
                'operation': 'strip',
                'output_file': str(abs_path),
                'removed_lines': removed,
                'success': True
            }
        
        elif operation == 'analyze':
            analysis = self.analyze_text_complexity(lang_file)
            result = {
                'operation': 'analyze',
                'analysis': analysis,
                'success': 'error' not in analysis
            }
            # Write JSON result to file if specified
            if 'output_file' in config:
                output_path = Path(config['output_file'])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                abs_path = output_path.resolve()
                print(f"Analysis results saved to: {abs_path}")
        
        elif operation == 'improve':
            model_name = config.get('model_name', 'phi4')
            target_age = config.get('target_age', 10)
            output_path = Path(config['output_file']) if 'output_file' in config else None
            
            result = self.improve_text_for_age(lang_file, model_name, target_age, output_path, 
                                              changelog_path=None)
            result['operation'] = 'improve'
            result['success'] = 'error' not in result
            if 'error' not in result:
                abs_path = Path(result['output_file']).resolve()
                abs_changelog = Path(result['changelog_file']).resolve()
                print(f"Improved .lang file saved to: {abs_path}")
                print(f"Changelog saved to: {abs_changelog}")
        
        elif operation == 'quiz':
            model_name = config.get('model_name', 'phi4')
            target_age = config.get('target_age', 10)
            output_dir = Path(config['output_file']).parent if 'output_file' in config else None
            
            result = self.generate_quiz(lang_file, model_name, target_age, output_dir)
            result['operation'] = 'quiz'
            result['success'] = 'error' not in result
            if 'error' not in result and 'quiz_file' in result:
                abs_quiz = Path(result['quiz_file']).resolve()
                abs_answers = Path(result['answer_key_file']).resolve()
                print(f"Quiz saved to: {abs_quiz}")
                print(f"Answer key saved to: {abs_answers}")
        
        elif operation == 'ai_analyze':
            model_name = config.get('model_name', 'phi4')
            result = self.analyze_with_ollama(lang_file, model_name)
            result['operation'] = 'ai_analyze'
            result['success'] = 'error' not in result
            # Write JSON result to file if specified
            if 'output_file' in config:
                output_path = Path(config['output_file'])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                abs_path = output_path.resolve()
                print(f"AI analysis results saved to: {abs_path}")
        
        else:
            result = {'error': f'Unknown operation: {operation}'}
        
        return result
    



if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python core.py '<json_config>'", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print('  python core.py \'{"operation":"analyze","input_file":"test.lang"}\'', file=sys.stderr)
        print("\nAvailable operations: analyze, strip, improve, quiz, ai_analyze", file=sys.stderr)
        print("\nRequired JSON parameters:", file=sys.stderr)
        print("  - operation: Operation to perform", file=sys.stderr)
        print("  - input_file: Path to .lang, .mcworld, or .mctemplate file", file=sys.stderr)
        print("\nOptional JSON parameters:", file=sys.stderr)
        print("  - cache_dir: Cache directory (default: .mc_lang_cache)", file=sys.stderr)
        print("  - output_file: Output file path (usage varies by operation):", file=sys.stderr)
        print("      * analyze/ai_analyze: JSON results file", file=sys.stderr)
        print("      * strip/improve: Output .lang file", file=sys.stderr)
        print("      * quiz: Directory for quiz files", file=sys.stderr)
        print("  - model_name: Ollama model name (default: phi4)", file=sys.stderr)
        print("  - target_age: Target age for improve/quiz (default: 10)", file=sys.stderr)
        sys.exit(1)
    
    # Get JSON config from first and only argument
    config_json = sys.argv[1]
    
    # Parse config to check if output_file is specified
    try:
        config = json.loads(config_json)
        has_output_file = 'output_file' in config
    except json.JSONDecodeError:
        has_output_file = False
    
    # Initialize tool and process
    tool = MinecraftLangTool()
    result = tool.process_from_config(config_json)
    
    # Print results to stdout only if output_file was not specified
    if not has_output_file:
        print(json.dumps(result, indent=2))
