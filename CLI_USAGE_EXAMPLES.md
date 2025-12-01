# CLI Usage Examples with API Configuration

This document shows how to use the new `--api-key` and `--base-url` options with the CLI.

## Quick Reference

### For Ollama (Default)

```bash
# No options needed - uses Ollama by default
python minecraft_lang_tool.py process myworld.mcworld
```

### For OpenAI

```bash
# Using environment variable
export OPENAI_API_KEY="sk-proj-..."
python minecraft_lang_tool.py process myworld.mcworld

# Or using CLI options
python minecraft_lang_tool.py process myworld.mcworld \
  --api-key "sk-proj-..." \
  --base-url ""
```

### For Azure AI Foundry

```bash
python minecraft_lang_tool.py process myworld.mcworld \
  --api-key "your-azure-key" \
  --base-url "https://your-resource.openai.azure.com/"
```

## Interactive Mode (`process` command)

### Ollama (Local)

```bash
# Default - uses Ollama on localhost:11434
python minecraft_lang_tool.py process myworld.mcworld

# Explicit Ollama configuration
python minecraft_lang_tool.py process myworld.mcworld \
  --api-key "ollama" \
  --base-url "http://localhost:11434/v1"
```

### OpenAI (Cloud)

```bash
# With explicit API key
python minecraft_lang_tool.py process myworld.mcworld \
  --api-key "sk-proj-your-key-here" \
  --base-url "https://api.openai.com/v1"

# Using environment variable (recommended)
export OPENAI_API_KEY="sk-proj-your-key-here"
python minecraft_lang_tool.py process myworld.mcworld
```

### Azure AI Foundry

```bash
python minecraft_lang_tool.py process myworld.mcworld \
  --api-key "your-azure-api-key" \
  --base-url "https://your-resource-name.openai.azure.com/"
```

## Non-Interactive Mode (`run` command)

### Analyze Text Complexity (No AI needed)

```bash
python minecraft_lang_tool.py run \
  --operation analyze \
  --input-file myworld.mcworld
```

### Improve Text with Ollama

```bash
python minecraft_lang_tool.py run \
  --operation improve \
  --input-file myworld.mcworld \
  --model-name phi4 \
  --target-age 10
```

### Improve Text with OpenAI

```bash
python minecraft_lang_tool.py run \
  --operation improve \
  --input-file myworld.mcworld \
  --model-name gpt-4o-mini \
  --target-age 10 \
  --api-key "sk-proj-your-key" \
  --base-url "https://api.openai.com/v1"
```

### Improve Text with Azure AI

```bash
python minecraft_lang_tool.py run \
  --operation improve \
  --input-file myworld.mcworld \
  --model-name "your-deployment-name" \
  --target-age 10 \
  --api-key "your-azure-key" \
  --base-url "https://your-resource.openai.azure.com/"
```

### Generate Quiz with OpenAI

```bash
python minecraft_lang_tool.py run \
  --operation quiz \
  --input-file myworld.mcworld \
  --model-name gpt-4o-mini \
  --target-age 12 \
  --api-key "sk-proj-your-key"
```

### AI Content Analysis with Azure

```bash
python minecraft_lang_tool.py run \
  --operation ai_analyze \
  --input-file myworld.mcworld \
  --model-name "your-gpt4-deployment" \
  --api-key "your-azure-key" \
  --base-url "https://your-resource.openai.azure.com/"
```

## Using JSON Configuration

### With API Configuration in JSON

```bash
# Create config.json
cat > config.json << EOF
{
  "operation": "improve",
  "input_file": "myworld.mcworld",
  "model_name": "gpt-4o-mini",
  "target_age": 10,
  "api_key": "sk-proj-...",
  "base_url": "https://api.openai.com/v1"
}
EOF

# Run with config file
python minecraft_lang_tool.py run config.json
```

### Using JSON String

```bash
python minecraft_lang_tool.py run --config-json '{
  "operation": "improve",
  "input_file": "myworld.mcworld",
  "model_name": "gpt-4o-mini",
  "target_age": 10,
  "api_key": "sk-proj-...",
  "base_url": "https://api.openai.com/v1"
}'
```

## Environment Variables

Set these to avoid passing credentials on command line:

### For OpenAI

```bash
export OPENAI_API_KEY="sk-proj-your-key-here"

# Then just use the tool normally
python minecraft_lang_tool.py process myworld.mcworld
```

### For Azure AI Foundry

```bash
export OPENAI_API_KEY="your-azure-key"
export OPENAI_BASE_URL="https://your-resource.openai.azure.com/"

# Then use the tool
python minecraft_lang_tool.py process myworld.mcworld
```

## Practical Examples

### Example 1: Analyze world without AI

```bash
python minecraft_lang_tool.py run \
  --operation analyze \
  --input-file "Sustainability City.mcworld" \
  --output-file analysis_results.json
```

### Example 2: Improve text for 8-year-olds using Ollama

```bash
python minecraft_lang_tool.py process "Chemistry Lab.mcworld"
# Then select "Improve text for target age" from menu
# Choose age 8 and model phi4
```

### Example 3: Generate quiz using OpenAI

```bash
export OPENAI_API_KEY="sk-proj-..."

python minecraft_lang_tool.py run \
  --operation quiz \
  --input-file "History World.mcworld" \
  --model-name gpt-4o-mini \
  --target-age 12
```

### Example 4: Batch processing with different providers

```bash
# Analyze with local tools (no AI)
python minecraft_lang_tool.py run --operation analyze --input-file world1.mcworld

# Improve with Ollama (free, local)
python minecraft_lang_tool.py run --operation improve --input-file world1.mcworld \
  --model-name phi4 --target-age 10

# Generate quiz with OpenAI (paid, cloud, better quality)
python minecraft_lang_tool.py run --operation quiz --input-file world1.mcworld \
  --model-name gpt-4o-mini --target-age 10 --api-key "sk-proj-..."
```