# API Configuration Guide

This tool now uses the OpenAI Python library for AI operations, which provides a unified interface for multiple AI providers:

- **Ollama** (local models)
- **OpenAI** (cloud service)
- **Azure AI Foundry** (Azure-hosted models)

## Configuration Options

The tool can be configured via:

1. Constructor parameters in Python code
2. JSON configuration for Regolith/CLI usage
3. Environment variables

### Constructor Parameters

```python
from minecraft_lang_tool.core import MinecraftLangTool

# For Ollama (default)
tool = MinecraftLangTool(
    cache_dir=".mc_lang_cache",
    api_key="ollama",  # Any non-empty string works
    base_url="http://localhost:11434/v1"
)

# For OpenAI
tool = MinecraftLangTool(
    api_key="sk-...",  # Your OpenAI API key
    base_url=None  # Uses OpenAI default
)

# For Azure AI Foundry
tool = MinecraftLangTool(
    api_key="your-azure-key",
    base_url="https://your-endpoint.openai.azure.com/"
)
```

### JSON Configuration

For command-line or Regolith usage:

```json
{
	"operation": "improve",
	"input_file": "example.lang",
	"model_name": "phi4",
	"target_age": 10,
	"api_key": "ollama",
	"base_url": "http://localhost:11434/v1"
}
```

### Environment Variables

The OpenAI library automatically reads these environment variables if not set explicitly:

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Azure AI Foundry
export OPENAI_API_KEY="your-azure-key"
export OPENAI_BASE_URL="https://your-endpoint.openai.azure.com/"
```

## Provider-Specific Configuration

### Ollama (Local Models)

**Prerequisites:**

- Install Ollama from https://ollama.ai
- Pull a model: `ollama pull phi4`
- Start Ollama service (usually starts automatically)

**Configuration:**

```python
tool = MinecraftLangTool(
    api_key="ollama",  # Any value works for Ollama
    base_url="http://localhost:11434/v1"
)
```

**Recommended Models:**

- `phi4` - Excellent for educational content (default)
- `llama3.2` - Good general-purpose model
- `mistral` - Fast and capable

### OpenAI (Cloud Service)

**Prerequisites:**

- Sign up at https://platform.openai.com
- Generate an API key
- Add billing information

**Configuration:**

```python
tool = MinecraftLangTool(
    api_key="sk-proj-...",  # Your API key
    base_url=None  # Uses default OpenAI endpoint
)
```

**Recommended Models:**

- `gpt-4o` - Best quality for educational content
- `gpt-4o-mini` - Good balance of quality and cost
- `gpt-3.5-turbo` - Fastest and cheapest

### Azure AI Foundry

**Prerequisites:**

- Azure subscription
- Create an Azure OpenAI resource
- Deploy a model to get an endpoint

**Configuration:**

```python
tool = MinecraftLangTool(
    api_key="your-azure-key",
    base_url="https://your-resource.openai.azure.com/"
)
```

**Model Names:**
Use the deployment name you chose in Azure, not the model family name.

## Example Usage

### Python API

```python
from minecraft_lang_tool.core import MinecraftLangTool
from pathlib import Path

# Using Ollama
tool = MinecraftLangTool(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

# Get available models
models = tool.get_available_models()
print(f"Available models: {models}")

# Improve text for age 10
result = tool.improve_text_for_age(
    lang_path=Path("example.lang"),
    model_name="phi4",
    target_age=10
)

# Generate quiz
quiz_result = tool.generate_quiz(
    lang_path=Path("example.lang"),
    model_name="phi4",
    target_age=10
)

# AI analysis
analysis = tool.analyze_with_ai(
    lang_path=Path("example.lang"),
    model="phi4"
)
```

### JSON Configuration (CLI/Regolith)

```bash
# Using Ollama (default)
python minecraft_lang_tool/core.py '{
  "operation": "improve",
  "input_file": "example.lang",
  "model_name": "phi4",
  "target_age": 10
}'

# Using OpenAI
python minecraft_lang_tool/core.py '{
  "operation": "improve",
  "input_file": "example.lang",
  "model_name": "gpt-4o-mini",
  "target_age": 10,
  "api_key": "sk-proj-...",
  "base_url": ""
}'

# Using Azure AI Foundry
python minecraft_lang_tool/core.py '{
  "operation": "improve",
  "input_file": "example.lang",
  "model_name": "my-deployment-name",
  "target_age": 10,
  "api_key": "azure-key",
  "base_url": "https://my-resource.openai.azure.com/"
}'
```