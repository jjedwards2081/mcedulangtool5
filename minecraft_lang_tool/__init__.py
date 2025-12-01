"""
Minecraft Language File Tool - Core Module

This package provides core functionality for processing Minecraft Education Edition
language files. It is designed to be used both as a standalone tool and as part of
Regolith filter pipelines.

Main class:
    MinecraftLangTool: Core processing class with JSON configuration support

Example usage:
    from minecraft_lang_tool.core import MinecraftLangTool
    
    tool = MinecraftLangTool(cache_dir=".cache")
    result = tool.process_from_config({
        "operation": "analyze",
        "input_file": "en_US.lang"
    })
"""

from .core import MinecraftLangTool

__version__ = "1.0.0"
__author__ = "Justin Edwards"
__email__ = "jnredwards@gmail.com"

__all__ = ["MinecraftLangTool"]
