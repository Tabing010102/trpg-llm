# TRPG-LLM

[![CI](https://github.com/Tabing010102/trpg-llm/actions/workflows/ci.yml/badge.svg)](https://github.com/Tabing010102/trpg-llm/actions/workflows/ci.yml)

A configuration-driven TRPG (Tabletop Role-Playing Game) framework with LLM integration.

## Overview

TRPG-LLM is a Python-based framework for running tabletop role-playing games with AI-powered characters and game masters. It features:

- **Configuration-Driven**: Define games entirely through YAML/JSON configuration files
- **Event Sourcing**: All state changes are recorded as immutable events, enabling perfect rollback and replay
- **LLM Integration**: Support for multiple LLM providers through LiteLLM (OpenAI, Anthropic, Azure, etc.)
- **Flexible Characters**: Any character can be controlled by AI or human players
- **Rule System Support**: Built-in support for Call of Cthulhu (CoC) 7th Edition, extensible to other systems
- **REST API**: FastAPI-based backend for frontend integration
- **Script Sandbox**: Safe execution environment for custom game logic

## Key Features

### Event Sourcing & State Management
- All state changes are atomic operations recorded as `state_diff`
- Complete event history enables time-travel debugging
- Re-hydration: automatically recalculate current state from event history
- Rollback to any point in time or specific event

### Dice System
- Support for standard dice notation (1d20, 3d6+5, etc.)
- Call of Cthulhu skill checks with difficulty levels (regular, hard, extreme)
- Critical success/failure detection
- Extensible for other rule systems

### AI Characters
- GM (Game Master), Players, and NPCs can all be AI-controlled
- Customizable prompts and personas per character
- Tool/function calling support for game actions
- Conversation history management

### API & Integration
- RESTful API built with FastAPI
- Real-time state updates
- WebSocket support (planned)
- Frontend-agnostic design
- **Web Frontend**: React + TypeScript interface for playing and debugging games

## Installation

### Backend

```bash
# Clone the repository
git clone https://github.com/Tabing010102/trpg-llm.git
cd trpg-llm

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173` and connects to the backend at `http://localhost:8000`.

## Quick Start

### Option 1: Using the Web Frontend (Recommended)

1. **Start the backend server**:
```bash
python -m trpg_llm.main --host 0.0.0.0 --port 8000
```

2. **Start the frontend** (in a new terminal):
```bash
cd frontend
npm run dev
```

3. **Open your browser** to `http://localhost:5173`

4. **Click "New Session"** to create a game with default configuration

5. **Start playing!** Select a character, type a message, and send it

See [frontend/README.md](frontend/README.md) for detailed frontend documentation.

### Option 2: Using the API Directly

### 1. Create a Game Configuration

Create a YAML configuration file (e.g., `my_game.yaml`):

```yaml
name: "My Adventure"
rule_system: "generic"
description: "An exciting adventure"

characters:
  player1:
    id: "player1"
    name: "Hero"
    type: "player"
    control: "human"
    attributes:
      strength: 15
      dexterity: 14
    state:
      hp: 20

  gm:
    id: "gm"
    name: "Game Master"
    type: "gm"
    control: "ai"
    ai_config:
      model: "gpt-3.5-turbo"
      temperature: 0.7

llm_config:
  default_model: "gpt-3.5-turbo"

initial_state:
  location: "Village Square"
```

### 2. Run the API Server

```bash
# Start the server
python -m trpg_llm.main

# Or with custom settings
python -m trpg_llm.main --host 0.0.0.0 --port 8000 --reload
```

### 3. Use the Framework Programmatically

```python
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.config.loader import ConfigLoader
from trpg_llm.models.dice import DiceRoll

# Load configuration
config = ConfigLoader.load_from_file("my_game.yaml")

# Create game engine
engine = GameEngine(config)

# Roll dice
dice_roll = DiceRoll(notation="1d20+5", character_id="player1")
state = engine.roll_dice(dice_roll)

# Update state
state = engine.update_state(
    actor_id="gm",
    path="characters.player1.state.hp",
    operation="subtract",
    value=5
)

# Add message
state = engine.add_message("gm", "A goblin attacks!")

# Get event history
events = engine.get_event_history()

# Rollback to previous state
state = engine.rollback_to_event(events[0].id)
```

## API Endpoints

### Session Management

- `POST /sessions` - Create a new game session
- `GET /sessions/{session_id}` - Get session state
- `GET /sessions/{session_id}/history` - Get event history
- `DELETE /sessions/{session_id}` - Delete session

### Game Actions

- `POST /sessions/{session_id}/actions` - Perform a game action
- `POST /sessions/{session_id}/dice` - Roll dice
- `POST /sessions/{session_id}/state` - Update state
- `POST /sessions/{session_id}/messages` - Add message
- `POST /sessions/{session_id}/rollback` - Rollback state

### Example API Usage

```bash
# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d @my_game.json

# Roll dice
curl -X POST http://localhost:8000/sessions/{session_id}/dice \
  -H "Content-Type: application/json" \
  -d '{
    "notation": "1d20+5",
    "character_id": "player1",
    "reason": "Attack roll"
  }'

# Get state
curl http://localhost:8000/sessions/{session_id}
```

## Configuration Reference

### Game Configuration Structure

```yaml
name: string              # Game name
rule_system: string       # Rule system (e.g., "coc7e", "dnd5e", "generic")
description: string       # Game description

characters:              # Character definitions
  <character_id>:
    id: string
    name: string
    type: player|npc|gm
    control: human|ai
    attributes: dict      # Character attributes
    state: dict          # Character state (hp, etc.)
    ai_config:           # AI configuration (if AI-controlled)
      model: string
      temperature: float

llm_config:              # LLM configuration
  default_model: string
  temperature: float
  prompts:
    gm_system: string    # GM system prompt
    player_system: string

workflow:                # Game workflow
  turn_order: list       # Turn order
  phases: list          # Game phases

tools:                   # Available actions/tools
  - name: string
    description: string
    parameters: dict

initial_state: dict      # Initial game state
```

## Architecture

### Core Components

1. **Models** (`trpg_llm/models/`)
   - `character.py` - Character definitions
   - `event.py` - Event and StateDiff models
   - `game_state.py` - Game state and configuration
   - `dice.py` - Dice roll models

2. **State Management** (`trpg_llm/state/`)
   - `state_machine.py` - Event sourcing state machine
   - `operations.py` - Atomic state operations

3. **Core Logic** (`trpg_llm/core/`)
   - `game_engine.py` - Main game orchestration
   - `dice.py` - Dice rolling system

4. **LLM Integration** (`trpg_llm/llm/`)
   - `llm_client.py` - LiteLLM wrapper
   - `agent.py` - AI agent implementation

5. **API** (`trpg_llm/api/`)
   - `server.py` - FastAPI application
   - `schemas.py` - API request/response models

6. **Configuration** (`trpg_llm/config/`)
   - `loader.py` - YAML/JSON configuration loader

7. **Sandbox** (`trpg_llm/sandbox/`)
   - `sandbox.py` - Safe script execution

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trpg_llm --cov-report=html

# Run specific test file
pytest tests/unit/test_dice.py
```

### Project Structure

```
trpg-llm/
├── trpg_llm/           # Main package
│   ├── api/            # FastAPI server
│   ├── config/         # Configuration loading
│   ├── core/           # Core game logic
│   ├── llm/            # LLM integration
│   ├── models/         # Data models
│   ├── sandbox/        # Script sandbox
│   ├── state/          # State management
│   └── utils/          # Utilities
├── tests/              # Tests
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── configs/            # Example configurations
├── examples/           # Example scripts
└── docs/              # Documentation (planned)
```

## Examples

See the `examples/` directory for complete examples:

- `basic_usage.py` - Basic framework usage
- See `configs/` for example game configurations:
  - `simple_game.json` - Simple adventure game
  - `coc_example.yaml` - Call of Cthulhu example

## Call of Cthulhu Support

TRPG-LLM includes built-in support for Call of Cthulhu 7th Edition:

- Skill checks with regular/hard/extreme difficulty
- Critical success/failure detection
- Success level determination
- Sanity system (configurable)
- Character sheets with CoC attributes

See `configs/coc_example.yaml` for a complete example.

## Roadmap

- [x] **Web Frontend**: React-based UI for playing and debugging games
- [ ] WebSocket support for real-time updates
- [ ] Database persistence (PostgreSQL, MongoDB)
- [ ] Additional rule systems (D&D 5e, Pathfinder)
- [ ] Enhanced AI agent behaviors
- [ ] Voice input/output support
- [ ] Campaign management
- [ ] Session replay viewer
- [ ] Character sheet generator
- [ ] Multi-session management in frontend
- [ ] Visual character sheet editor
- [ ] Map/location visualization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[License information to be added]

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LiteLLM](https://github.com/BerriAI/litellm) - LLM integration
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [PyYAML](https://pyyaml.org/) - YAML parsing
- [React](https://react.dev/) - Frontend UI framework
- [Vite](https://vitejs.dev/) - Frontend build tool