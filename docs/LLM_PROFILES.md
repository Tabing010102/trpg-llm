# LLM Profiles - Multi-Provider Support

## Overview

LLM Profiles allow you to configure multiple LLM connections with different providers, models, and parameters, then route them to different characters or switch them dynamically at request time.

## Key Features

- **Multiple Provider Support**: Configure OpenAI-compatible, Anthropic, Gemini, or local models
- **Character-Level Routing**: Assign specific profiles to individual characters
- **Request-Level Override**: Switch profiles for individual chat requests
- **Regeneration Switching**: Use different profiles when regenerating AI messages
- **Metadata Tracking**: Track which profile was used for each message
- **Backward Compatibility**: Works with existing configurations without profiles

## Configuration

### Basic Setup

Add `llm_profiles` to your game configuration:

```yaml
llm_config:
  default_profile_id: "gpt3_fast"  # Fallback profile

llm_profiles:
  - id: "gpt3_fast"
    provider_type: "oai_compatible"
    model: "gpt-3.5-turbo"
    temperature: 0.7
    api_key_ref: "OPENAI_API_KEY"
  
  - id: "gpt4_smart"
    provider_type: "oai_compatible"
    model: "gpt-4"
    temperature: 0.5
    max_tokens: 2000
    api_key_ref: "OPENAI_API_KEY"
```

### Profile Fields

- **id** (required): Unique identifier for the profile
- **provider_type** (default: "oai_compatible"): Provider type
  - `oai_compatible`: OpenAI API-compatible services
  - `anthropic`: Anthropic Claude
  - `gemini`: Google Gemini
  - `local_openai`: Local models via OpenAI-compatible API
- **model** (required): Model identifier
- **base_url** (optional): Custom API endpoint
- **api_key_ref** (optional): Environment variable name for API key
- **temperature** (default: 0.7): Sampling temperature
- **top_p** (optional): Nucleus sampling parameter
- **max_tokens** (optional): Maximum tokens to generate
- **context_window** (optional): Context window size
- **extra_params** (optional): Additional provider-specific parameters

### Assigning Profiles to Characters

```yaml
characters:
  gm:
    id: "gm"
    name: "Game Master"
    type: "gm"
    control: "ai"
    ai_config:
      profile_id: "gpt4_creative"  # GM uses creative profile
  
  player_ai:
    id: "player_ai"
    name: "AI Player"
    type: "player"
    control: "ai"
    ai_config:
      profile_id: "gpt3_fast"  # Player uses fast profile
```

If no `profile_id` is specified, the `default_profile_id` from `llm_config` is used.

## API Usage

### Chat with Default Profile

```python
POST /api/v1/sessions/{session_id}/chat
{
  "role_id": "gm",
  "message": "What do you see?"
}
```

The character's configured profile is used automatically.

### Chat with Override Profile

```python
POST /api/v1/sessions/{session_id}/chat
{
  "role_id": "gm",
  "message": "What do you see?",
  "llm_profile_id": "gpt4_creative"  # Override to use creative profile
}
```

### Regenerate with Different Profile

```python
POST /sessions/{session_id}/redraw
{
  "character_id": "gm",
  "llm_profile_id": "gpt4_precise"  # Use precise model for regeneration
}
```

If `llm_profile_id` is not specified, the previous profile is used.

## Response Metadata

AI responses include profile information:

```json
{
  "content": "You enter a dimly lit room...",
  "role_id": "gm",
  "is_ai": true,
  "used_profile_id": "gpt4_creative"
}
```

Message events also store profile metadata:

```json
{
  "metadata": {
    "used_profile_id": "gpt4_creative",
    "provider_type": "oai_compatible",
    "model": "gpt-4",
    "tool_calls": [],
    "iterations": 1
  }
}
```

## Provider Examples

### OpenAI

```yaml
- id: "openai_gpt4"
  provider_type: "oai_compatible"
  model: "gpt-4-turbo-preview"
  api_key_ref: "OPENAI_API_KEY"
  temperature: 0.7
```

### Anthropic Claude

```yaml
- id: "claude"
  provider_type: "anthropic"
  model: "claude-3-opus-20240229"
  base_url: "https://api.anthropic.com"
  api_key_ref: "ANTHROPIC_API_KEY"
  temperature: 0.8
```

### Local Model (via LM Studio, Ollama, etc.)

```yaml
- id: "local_llama"
  provider_type: "local_openai"
  model: "llama2"
  base_url: "http://localhost:1234/v1"
  temperature: 0.7
  # No api_key_ref needed
```

### Azure OpenAI

```yaml
- id: "azure_gpt4"
  provider_type: "oai_compatible"
  model: "azure/gpt-4-deployment-name"
  base_url: "https://your-resource.openai.azure.com"
  api_key_ref: "AZURE_OPENAI_API_KEY"
```

## Backward Compatibility

Existing configurations without `llm_profiles` continue to work. The system automatically creates a default profile from the legacy `llm_config`:

```yaml
# Legacy config (still works)
llm_config:
  default_model: "gpt-3.5-turbo"
  temperature: 0.7
```

This is equivalent to:

```yaml
llm_profiles:
  - id: "default"
    model: "gpt-3.5-turbo"
    temperature: 0.7
```

## Use Cases

### Cost Optimization

Use cheaper models for routine interactions and expensive models for important decisions:

```yaml
llm_profiles:
  - id: "routine"
    model: "gpt-3.5-turbo"  # Fast and cheap
  - id: "important"
    model: "gpt-4"  # Slow but powerful
```

### Specialization

Different characters use different models based on their role:

```yaml
characters:
  gm:
    ai_config:
      profile_id: "creative"  # High temperature for narrative
  analyst:
    ai_config:
      profile_id: "precise"  # Low temperature for logic
```

### A/B Testing

Try different models for regeneration to compare quality:

```python
# Original response with gpt-3.5
POST /api/v1/sessions/{id}/chat
{"role_id": "gm"}

# Regenerate with gpt-4 to compare
POST /sessions/{id}/redraw
{"character_id": "gm", "llm_profile_id": "gpt4"}
```

### Multi-Provider Fallback

Configure backup providers for reliability:

```yaml
llm_profiles:
  - id: "primary"
    model: "gpt-4"
    api_key_ref: "OPENAI_API_KEY"
  - id: "backup"
    model: "claude-2"
    api_key_ref: "ANTHROPIC_API_KEY"
```

## Security

- API keys are referenced by environment variable names, not stored in config
- Keys are resolved at runtime from the environment
- No sensitive data is logged in metadata

## See Also

- [Example Configuration](../configs/multi_llm_example.yaml) - Complete working example
- [API Documentation](../README.md) - Full API reference
- [LiteLLM Documentation](https://docs.litellm.ai/) - Underlying provider integration
