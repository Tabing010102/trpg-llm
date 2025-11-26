---
applyTo: "**/configs/**/*.{yaml,yml,json}"
---

# Game Configuration Guidelines

When creating or modifying game configuration files, follow these guidelines:

## Configuration Schema

Game configurations must follow the `GameConfig` schema:

```yaml
# Required fields
name: string              # Game/campaign name
rule_system: string       # Rule system (e.g., "coc7e", "dnd5e", "generic")

# Optional fields
description: string       # Game description

characters:               # Character definitions (required)
  <character_id>:
    id: string           # Must match the key
    name: string         # Display name
    type: player|npc|gm  # Character type
    control: human|ai    # Control type
    attributes: dict     # Rule-system specific stats
    state: dict          # Current state (hp, sanity, etc.)
    ai_config:           # Required if control: ai
      model: string      # LLM model
      temperature: float # Sampling temperature
      profile_id: string # Optional: reference to llm_profiles

llm_config:              # LLM configuration
  default_model: string  # Default model for AI characters
  temperature: float     # Default temperature
  default_profile_id: string  # Default profile reference
  prompts:               # System prompts
    gm_system: string    # GM system prompt
    player_system: string
    npc_system: string

llm_profiles:            # Multi-provider LLM profiles (optional)
  - id: string           # Profile identifier
    provider_type: oai_compatible|anthropic|gemini|local_openai
    base_url: string     # API endpoint
    api_key_ref: string  # Environment variable name for API key
    model: string        # Model identifier
    temperature: float
    max_tokens: int

workflow:                # Game workflow (optional)
  turn_order: list       # Character turn order
  phases: list           # Game phases

tools:                   # Available tools/actions (optional)
  - name: string         # Tool name
    description: string  # Tool description
    parameters: dict     # OpenAI function calling format

scripts:                 # Custom script hooks (optional)
  on_turn_end: string    # Python script for turn end

initial_state: dict      # Initial game state variables
```

## Character Definition Examples

### AI-Controlled GM (Call of Cthulhu)

```yaml
keeper:
  id: "keeper"
  name: "Keeper"
  type: "gm"
  control: "ai"
  description: "The Game Master controlling the narrative"
  ai_config:
    model: "gpt-4"
    temperature: 0.8
```

### Human Player Character

```yaml
player1:
  id: "player1"
  name: "Detective Chen"
  type: "player"
  control: "human"
  attributes:
    str: 60
    dex: 65
    int: 80
    pow: 70
  state:
    hp: 10
    mp: 14
    sanity: 70
```

### AI-Controlled NPC

```yaml
librarian:
  id: "librarian"
  name: "Old Librarian"
  type: "npc"
  control: "ai"
  description: "A mysterious elderly librarian who knows too much"
  ai_config:
    model: "gpt-3.5-turbo"
    temperature: 0.6
```

## Multi-LLM Profile Example

```yaml
llm_profiles:
  - id: "gpt4-creative"
    provider_type: "oai_compatible"
    api_key_ref: "OPENAI_API_KEY"
    model: "gpt-4"
    temperature: 0.9
    
  - id: "claude-logic"
    provider_type: "anthropic"
    api_key_ref: "ANTHROPIC_API_KEY"
    model: "claude-3-sonnet-20240229"
    temperature: 0.3
    
  - id: "local-llama"
    provider_type: "local_openai"
    base_url: "http://localhost:11434/v1"
    model: "llama2"
    temperature: 0.7

llm_config:
  default_profile_id: "gpt4-creative"
```

## Tool Definition Example

```yaml
tools:
  - name: "roll_skill"
    description: "Roll a skill check"
    parameters:
      type: "object"
      properties:
        skill_name:
          type: "string"
          description: "Name of the skill"
        difficulty:
          type: "string"
          enum: ["regular", "hard", "extreme"]
      required: ["skill_name"]
```

## Initial State Example

```yaml
initial_state:
  location: "Arkham Library"
  time: "Evening"
  atmosphere: "tense"
  clues_found: []
  doors_opened:
    front: true
    back: false
```

## Validation Checklist

- [ ] `name` and `rule_system` are defined
- [ ] Each character has `id`, `name`, `type`, and `control`
- [ ] AI characters have `ai_config` with at least `model`
- [ ] Character `id` matches its dictionary key
- [ ] `llm_config` has `default_model` or `default_profile_id`
- [ ] Tool parameters follow OpenAI function calling format
- [ ] YAML/JSON syntax is valid

