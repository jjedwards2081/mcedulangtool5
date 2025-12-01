"""
Test suite for core functionality

Tests non-AI features:
- Archive extraction
- Lang file discovery
- Text complexity analysis
- File stripping
"""

import unittest
import zipfile
from pathlib import Path

from minecraft_lang_tool.core import MinecraftLangTool


class TestArchiveExtraction(unittest.TestCase):
    """Test archive extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test .mcworld file (ZIP archive)
        self.test_mcworld = self.test_dir / "test_world.mcworld"
        with zipfile.ZipFile(self.test_mcworld, 'w') as zf:
            zf.writestr("texts/en_US.lang", "test.key=Test value\n")
            zf.writestr("level.dat", "mock level data")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Clean up cache
        cache_dir = Path(".mc_lang_cache")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
    
    def test_extract_mcworld(self):
        """Test extracting .mcworld archive."""
        tool = MinecraftLangTool()
        extract_dir = tool.extract_archive(str(self.test_mcworld))
        
        self.assertTrue(extract_dir.exists())
        self.assertTrue((extract_dir / "texts" / "en_US.lang").exists())
    
    def test_extract_nonexistent_file(self):
        """Test extracting non-existent file raises error."""
        tool = MinecraftLangTool()
        
        with self.assertRaises(FileNotFoundError):
            tool.extract_archive("nonexistent.mcworld")
    
    def test_extract_invalid_archive(self):
        """Test extracting invalid archive raises error."""
        invalid_file = self.test_dir / "invalid.mcworld"
        with open(invalid_file, 'w') as f:
            f.write("This is not a ZIP file")
        
        tool = MinecraftLangTool()
        
        with self.assertRaises(ValueError):
            tool.extract_archive(str(invalid_file))


class TestLangFileDiscovery(unittest.TestCase):
    """Test lang file discovery functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create multiple lang files
        (self.test_dir / "texts").mkdir(exist_ok=True)
        
        # Create en_US (highest priority)
        with open(self.test_dir / "texts" / "en_US.lang", 'w') as f:
            f.write("test.key=Value\n" * 100)
        
        # Create other English variant
        with open(self.test_dir / "texts" / "en_GB.lang", 'w') as f:
            f.write("test.key=Value\n" * 50)
        
        # Create non-English
        with open(self.test_dir / "texts" / "es_ES.lang", 'w') as f:
            f.write("test.key=Value\n" * 75)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_find_lang_files(self):
        """Test finding all lang files."""
        tool = MinecraftLangTool()
        lang_files = tool.find_lang_files(self.test_dir)
        
        self.assertEqual(len(lang_files), 3)
    
    def test_lang_file_priority(self):
        """Test that en_US is prioritized first."""
        tool = MinecraftLangTool()
        lang_files = tool.find_lang_files(self.test_dir)
        
        # First file should be en_US
        first_file, _ = lang_files[0]
        self.assertIn("en_US", str(first_file))
    
    def test_find_no_lang_files(self):
        """Test finding lang files in empty directory."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir(exist_ok=True)
        
        tool = MinecraftLangTool()
        lang_files = tool.find_lang_files(empty_dir)
        
        self.assertEqual(len(lang_files), 0)


class TestTextComplexityAnalysis(unittest.TestCase):
    """Test text complexity analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test lang file with readable content
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("# Test lang file\n")
            f.write("game.welcome=Welcome to our educational game about science!\n")
            f.write("game.instructions=Follow the instructions carefully to complete each level.\n")
            f.write("game.challenge=This challenging puzzle requires critical thinking skills.\n")
            f.write("game.reward=Congratulations! You have successfully completed the task.\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_analyze_text_complexity(self):
        """Test text complexity analysis."""
        tool = MinecraftLangTool()
        analysis = tool.analyze_text_complexity(self.test_lang)
        
        self.assertNotIn('error', analysis)
        self.assertIn('total_entries', analysis)
        self.assertIn('flesch_reading_ease', analysis)
        self.assertIn('grade_level', analysis)
        self.assertIn('age_range', analysis)
        self.assertIn('difficulty', analysis)
    
    def test_analyze_empty_file(self):
        """Test analyzing empty lang file."""
        empty_file = self.test_dir / "empty.lang"
        with open(empty_file, 'w') as f:
            f.write("")
        
        tool = MinecraftLangTool()
        analysis = tool.analyze_text_complexity(empty_file)
        
        self.assertIn('error', analysis)
    
    def test_complexity_metrics_present(self):
        """Test that all complexity metrics are calculated."""
        tool = MinecraftLangTool()
        analysis = tool.analyze_text_complexity(self.test_lang)
        
        metrics = [
            'flesch_reading_ease',
            'flesch_kincaid_grade',
            'gunning_fog_index',
            'coleman_liau_index',
            'automated_readability_index',
            'vocabulary_complexity'
        ]
        
        for metric in metrics:
            self.assertIn(metric, analysis)


class TestTextStripping(unittest.TestCase):
    """Test text stripping functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("player.greeting=Hello player!\n")
            f.write("# Another comment\n")
            f.write("debug.info=Debug information\n")
            f.write("\n")
            f.write("player.goodbye=Goodbye!\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_strip_non_player_text(self):
        """Test stripping comments and empty lines."""
        tool = MinecraftLangTool()
        output_file = self.test_dir / "output.lang"
        
        removed = tool.strip_non_player_text(self.test_lang, output_file)
        
        self.assertGreater(removed, 0)
        self.assertTrue(output_file.exists())
        
        # Check output file doesn't have comments
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertNotIn('#', content)
            self.assertIn('player.greeting', content)


class TestFilenameSanitization(unittest.TestCase):
    """Test filename sanitization functionality."""
    
    def test_sanitize_filename_spaces(self):
        """Test sanitizing filename with spaces."""
        tool = MinecraftLangTool()
        sanitized = tool.sanitize_filename("Test World v1")
        
        self.assertNotIn(' ', sanitized)
        self.assertEqual(sanitized, "Test_World_v1")
    
    def test_sanitize_filename_special_chars(self):
        """Test sanitizing filename with special characters."""
        tool = MinecraftLangTool()
        sanitized = tool.sanitize_filename("World (v2) [final]!")
        
        self.assertNotIn('(', sanitized)
        self.assertNotIn(')', sanitized)
        self.assertNotIn('[', sanitized)
        self.assertNotIn(']', sanitized)
        self.assertNotIn('!', sanitized)
    
    def test_sanitize_filename_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed."""
        tool = MinecraftLangTool()
        sanitized = tool.sanitize_filename("Test___World")
        
        self.assertNotIn('___', sanitized)
        self.assertEqual(sanitized, "Test_World")


if __name__ == '__main__':
    unittest.main()
