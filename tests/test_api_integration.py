"""
Test suite for API integration (OpenAI library with multiple providers)

Tests the core functionality of the OpenAI library integration including:
- Client initialization
- Model listing
- API calls (mocked)
- Error handling
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

from minecraft_lang_tool.core import MinecraftLangTool


class TestAPIInitialization(unittest.TestCase):
    """Test MinecraftLangTool initialization with different API configurations."""
    
    def test_default_initialization(self):
        """Test that tool initializes with default Ollama configuration."""
        tool = MinecraftLangTool()
        
        self.assertIsNotNone(tool.client)
        self.assertEqual(tool.cache_dir, Path(".mc_lang_cache"))
    
    def test_explicit_ollama_configuration(self):
        """Test explicit Ollama configuration."""
        tool = MinecraftLangTool(
            api_key="ollama",
            base_url="http://localhost:11434/v1"
        )
        
        self.assertIsNotNone(tool.client)
    
    def test_openai_configuration(self):
        """Test OpenAI configuration."""
        tool = MinecraftLangTool(
            api_key="test-key",
            base_url=None  # Uses OpenAI default
        )
        
        self.assertIsNotNone(tool.client)
    
    def test_azure_configuration(self):
        """Test Azure AI Foundry configuration."""
        tool = MinecraftLangTool(
            api_key="azure-key",
            base_url="https://test-resource.openai.azure.com/"
        )
        
        self.assertIsNotNone(tool.client)
    
    def test_custom_cache_dir(self):
        """Test custom cache directory."""
        custom_cache = "custom_test_cache"
        tool = MinecraftLangTool(cache_dir=custom_cache)
        
        self.assertEqual(tool.cache_dir, Path(custom_cache))
        self.assertTrue(tool.cache_dir.exists())
        
        # Cleanup
        import shutil
        if Path(custom_cache).exists():
            shutil.rmtree(custom_cache)


class TestModelListing(unittest.TestCase):
    """Test model listing functionality with mocked API responses."""
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_get_available_models_success(self, mock_openai):
        """Test successful model listing."""
        # Mock the models.list() response
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_models.data = [
            MagicMock(id="phi4:latest"),
            MagicMock(id="llama3.2:latest"),
            MagicMock(id="mistral:latest")
        ]
        mock_client.models.list.return_value = mock_models
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        models = tool.get_available_models()
        
        self.assertEqual(len(models), 3)
        self.assertIn("phi4:latest", models)
        self.assertIn("llama3.2:latest", models)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_get_available_models_empty(self, mock_openai):
        """Test model listing when no models available."""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_models.data = []
        mock_client.models.list.return_value = mock_models
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        models = tool.get_available_models()
        
        self.assertEqual(len(models), 0)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_get_available_models_error(self, mock_openai):
        """Test model listing error handling."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection error")
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        models = tool.get_available_models()
        
        self.assertEqual(models, [])


class TestTextImprovement(unittest.TestCase):
    """Test text improvement functionality with mocked API calls."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test lang file
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("# Test lang file\n")
            f.write("test.greeting=Hello, welcome to the game!\n")
            f.write("test.instruction=Please follow the instructions carefully.\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_improve_text_for_age_success(self, mock_openai):
        """Test successful text improvement."""
        # Mock the chat completion response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hi, welcome to the game!"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        result = tool.improve_text_for_age(
            self.test_lang,
            "phi4",
            target_age=8
        )
        
        self.assertNotIn('error', result)
        self.assertIn('output_file', result)
        self.assertIn('changelog_file', result)
        self.assertIn('lines_improved', result)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_improve_text_api_error(self, mock_openai):
        """Test text improvement with API error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        result = tool.improve_text_for_age(
            self.test_lang,
            "phi4",
            target_age=8
        )
        
        # Should handle errors gracefully
        self.assertIsInstance(result, dict)


class TestQuizGeneration(unittest.TestCase):
    """Test quiz generation functionality with mocked API calls."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test lang file with narrative content
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("narrative.intro=Welcome to the chemistry lab where you will learn about molecules.\n")
            f.write("narrative.chapter1=In this chapter, you will discover how atoms combine to form molecules.\n")
            f.write("narrative.chapter2=Water is composed of two hydrogen atoms and one oxygen atom.\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_generate_quiz_success(self, mock_openai):
        """Test successful quiz generation."""
        # Mock the chat completion response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = """QUIZ: Chemistry Lab Quiz
Target Age: 10
Total Marks: 10

Question 1: What will you learn in the chemistry lab?
A) About planets
B) About molecules
C) About animals
D) About plants

ANSWER KEY:
1. B"""
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        result = tool.generate_quiz(
            self.test_lang,
            "phi4",
            target_age=10
        )
        
        self.assertNotIn('error', result)
        self.assertIn('quiz_file', result)
        self.assertIn('answer_key_file', result)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_generate_quiz_no_narrative(self, mock_openai):
        """Test quiz generation with no narrative text."""
        # Create file with no narrative content
        test_file = self.test_dir / "no_narrative.lang"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("key.a=A\n")
            f.write("key.b=B\n")
        
        tool = MinecraftLangTool()
        result = tool.generate_quiz(test_file, "phi4", target_age=10)
        
        self.assertIn('error', result)
        self.assertIn('No narrative text found', result['error'])


class TestAIAnalysis(unittest.TestCase):
    """Test AI content analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("game.title=Educational Chemistry Adventure\n")
            f.write("game.description=Learn about chemical reactions through interactive gameplay.\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    @patch('minecraft_lang_tool.core.OpenAI')
    def test_analyze_with_ai_success(self, mock_openai):
        """Test successful AI analysis."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is an educational chemistry game for students."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        tool = MinecraftLangTool()
        result = tool.analyze_with_ai(self.test_lang, "phi4")
        
        self.assertNotIn('error', result)
        self.assertIn('analysis', result)
        self.assertIn('model', result)
        self.assertIn('samples_analyzed', result)


class TestJSONConfiguration(unittest.TestCase):
    """Test JSON configuration processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_fixtures")
        self.test_dir.mkdir(exist_ok=True)
        
        self.test_lang = self.test_dir / "test.lang"
        with open(self.test_lang, 'w', encoding='utf-8') as f:
            f.write("test.key=Test value\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_json_config_analyze(self):
        """Test analyze operation via JSON config."""
        tool = MinecraftLangTool()
        config = {
            "operation": "analyze",
            "input_file": str(self.test_lang)
        }
        
        import json
        result = tool.process_from_config(json.dumps(config))
        
        self.assertIn('operation', result)
        self.assertEqual(result['operation'], 'analyze')
        self.assertIn('success', result)
    
    def test_json_config_with_api_settings(self):
        """Test JSON config with API settings."""
        tool = MinecraftLangTool()
        config = {
            "operation": "analyze",
            "input_file": str(self.test_lang),
            "api_key": "test-key",
            "base_url": "http://test.com"
        }
        
        import json
        result = tool.process_from_config(json.dumps(config))
        
        # Should not error on config parsing
        self.assertIsInstance(result, dict)
    
    def test_json_config_invalid_json(self):
        """Test invalid JSON config."""
        tool = MinecraftLangTool()
        result = tool.process_from_config("invalid json {")
        
        self.assertIn('error', result)
        self.assertIn('Invalid JSON', result['error'])
    
    def test_json_config_missing_required(self):
        """Test JSON config with missing required fields."""
        tool = MinecraftLangTool()
        config = {"operation": "analyze"}  # Missing input_file
        
        import json
        result = tool.process_from_config(json.dumps(config))
        
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
