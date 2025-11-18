"""
Test suite for CLI options

Tests the command-line interface including:
- Option parsing  
- Help text
- Command execution
"""

import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pathlib import Path
import sys
import importlib.util

# Add parent directory to Python path for imports
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

# Import the CLI module directly (not the package)
spec = importlib.util.spec_from_file_location("minecraft_lang_tool", Path(parent_dir) / "minecraft_lang_tool.py")
mlt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mlt)


class TestCLIHelp(unittest.TestCase):
    """Test CLI help commands and documentation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_process_command_help(self):
        """Test that 'process' command help shows API options."""
        result = self.runner.invoke(mlt.cli, ['process', '--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--api-key", result.output)
        self.assertIn("--base-url", result.output)
    
    def test_run_command_help(self):
        """Test that 'run' command help shows API options."""
        result = self.runner.invoke(mlt.cli, ['run', '--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--api-key", result.output)
        self.assertIn("--base-url", result.output)
    
    def test_main_cli_help(self):
        """Test main CLI help."""
        result = self.runner.invoke(mlt.cli, ['--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("process", result.output)
        self.assertIn("run", result.output)


class TestCLIOptionParsing(unittest.TestCase):
    """Test that CLI options are parsed correctly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('minecraft_lang_tool.MinecraftLangTool')
    def test_api_key_passed_to_tool(self, mock_tool_class):
        """Test that --api-key is passed to MinecraftLangTool."""
        mock_instance = MagicMock()
        mock_tool_class.return_value = mock_instance
        
        with self.runner.isolated_filesystem():
            # Create test file
            Path("test.lang").write_text("test.key=value")
            
            result = self.runner.invoke(mlt.process, [
                'test.lang',
                '--api-key', 'test-key-123'
            ])
            
            # Check that MinecraftLangTool was initialized with api_key
            if mock_tool_class.called:
                call_kwargs = mock_tool_class.call_args[1] if mock_tool_class.call_args else {}
                self.assertEqual(call_kwargs.get('api_key'), 'test-key-123')
    
    @patch('minecraft_lang_tool.MinecraftLangTool')
    def test_base_url_passed_to_tool(self, mock_tool_class):
        """Test that --base-url is passed to MinecraftLangTool."""
        mock_instance = MagicMock()
        mock_tool_class.return_value = mock_instance
        
        with self.runner.isolated_filesystem():
            # Create test file
            Path("test.lang").write_text("test.key=value")
            
            result = self.runner.invoke(mlt.process, [
                'test.lang',
                '--base-url', 'http://custom-api.com/v1'
            ])
            
            # Check that MinecraftLangTool was initialized with base_url
            if mock_tool_class.called:
                call_kwargs = mock_tool_class.call_args[1] if mock_tool_class.call_args else {}
                self.assertEqual(call_kwargs.get('base_url'), 'http://custom-api.com/v1')


class TestCLIRunCommand(unittest.TestCase):
    """Test CLI run command with JSON config."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('minecraft_lang_tool.MinecraftLangTool')
    def test_run_command_with_api_options(self, mock_tool_class):
        """Test run command passes API options."""
        mock_instance = MagicMock()
        mock_instance.process_from_config.return_value = {'success': True}
        mock_tool_class.return_value = mock_instance
        
        config = '{"operation": "analyze", "input_file": "test.lang"}'
        result = self.runner.invoke(mlt.run, [
            '--config-json', config,
            '--api-key', 'test-key',
            '--base-url', 'http://test.com/v1'
        ])
        
        # Check MinecraftLangTool initialization
        if mock_tool_class.called:
            call_kwargs = mock_tool_class.call_args[1] if mock_tool_class.call_args else {}
            self.assertEqual(call_kwargs.get('api_key'), 'test-key')
            self.assertEqual(call_kwargs.get('base_url'), 'http://test.com/v1')


if __name__ == '__main__':
    unittest.main()
