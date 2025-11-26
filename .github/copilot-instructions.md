# TRPG-LLM Repository Instructions

This is a Python-based TRPG (Tabletop Role-Playing Game) framework with LLM integration and a React/TypeScript frontend. Please follow these guidelines when contributing.

## Code Standards

### Required Before Each Commit

**Backend (Python):**
- Run `ruff check trpg_llm/ tests/` to check for linting errors
- Run `ruff format trpg_llm/ tests/` to ensure proper code formatting
- Run `pytest tests/ -v` to ensure all tests pass

**Frontend (React/TypeScript):**
- Run `npm run lint` in the `frontend/` directory
- Run `npx tsc -b --noEmit` for TypeScript type checking
- Run `npm run build` to verify the build succeeds

### Development Flow

**Backend:**
- Install dependencies: `pip install -r requirements.txt`
- Install package in dev mode: `pip install -e .`
- Run tests: `pytest tests/ -v --cov=trpg_llm`
- Start server: `python -m trpg_llm.main --host 0.0.0.0 --port 8000`

**Frontend:**
- Install dependencies: `cd frontend && npm install`
- Start dev server: `npm run dev`
- Build for production: `npm run build`

## Architecture Overview

This project follows a **Layered Architecture** with **Event Sourcing** pattern:

### Repository Structure

- `trpg_llm/` - Main Python package
  - `api/` - FastAPI REST API layer (server.py, schemas.py)
  - `config/` - YAML/JSON configuration loader
  - `core/` - Core game logic (game_engine.py, chat_pipeline.py, dice.py, tool_executor.py)
  - `llm/` - LLM integration layer (llm_client.py via LiteLLM, agent.py, agent_manager.py, profile.py)
  - `models/` - Pydantic data models (character.py, event.py, game_state.py, dice.py)
  - `sandbox/` - Safe Python script execution environment
  - `state/` - Event sourcing state machine and atomic operations
  - `utils/` - Utility functions (logger.py)

- `frontend/` - React + TypeScript + Vite frontend
  - `src/components/` - React components
  - `src/services/` - API client
  - `src/types/` - TypeScript type definitions

- `tests/` - Test suite
  - `unit/` - Unit tests for individual modules
  - `integration/` - Integration tests for pipelines

- `configs/` - Example game configuration files (YAML/JSON)

## Key Design Patterns

### Event Sourcing

- **All state changes are recorded as immutable events** with `state_diffs`
- Current state is **computed by replaying event history**: `CurrentState = InitialState + Σ(StateDiffs)`
- The `StateMachine` class in `state/state_machine.py` implements this pattern
- Never store current state directly; always derive it from events

### State Operations

Use atomic operations defined in `state/operations.py`:
- `set` - Set a value
- `add` / `subtract` - Numeric operations
- `multiply` - Numeric multiplication
- `append` / `remove` - List operations
- `delete` - Remove a key

### LLM Integration

- Uses **LiteLLM** for multi-provider support (OpenAI, Anthropic, Azure, etc.)
- `LLMProfileRegistry` manages multiple LLM configurations
- Characters can be `AI` or `Human` controlled via `Character.control`
- Tool/function calling supported via `ToolExecutor`

### Chat Pipeline

The `ChatPipeline` class orchestrates:
1. Input → State Hydration → Prompt Rendering → LLM Inference → Tool Execution → State Update

## Coding Guidelines

### Python (Backend)

1. Use **Pydantic** models for all data structures
2. Follow **type hints** for all function signatures
3. Use **async/await** for LLM calls (also provide sync versions with `_sync` suffix)
4. Write **unit tests** for new functionality using pytest
5. Use **table-driven tests** when testing multiple scenarios
6. Handle exceptions gracefully; log errors but don't crash the game engine
7. Keep the sandbox safe - no file I/O or network access in user scripts

### TypeScript/React (Frontend)

1. Use **TypeScript** with strict type checking
2. Define API types in `src/types/api.ts` matching backend schemas
3. Use **functional components** with React hooks
4. Keep components in `src/components/` directory
5. Use the `api.ts` service for all backend communication

### Configuration Files

1. Support both **YAML** and **JSON** formats
2. Follow the `GameConfig` schema defined in `models/game_state.py`
3. Include `name`, `rule_system`, `characters`, `llm_config`, `initial_state`

## Testing Requirements

- Write unit tests in `tests/unit/` for individual modules
- Write integration tests in `tests/integration/` for pipelines
- Use `pytest` fixtures for common test setup
- Mock LLM calls in tests to avoid API dependencies
- Test both success and error cases

## API Design

- RESTful endpoints under `/sessions/{session_id}/`
- Use Pydantic models for request/response schemas in `api/schemas.py`
- Return structured responses with `content` and `state_diffs` for frontend rendering
- Support rollback, regenerate, and edit operations

## Important Notes

1. **Event Sourcing is Critical**: Never bypass the state machine; all changes must go through events
2. **Backward Compatibility**: Support legacy `llm_config` alongside new `llm_profiles`
3. **Rule System Agnostic**: Core engine should work with any TRPG rule system
4. **Safe Script Execution**: The sandbox restricts dangerous operations for user scripts
5. **Tool Calling**: LLM can call tools like `roll_dice`, `update_state` - these must produce `state_diffs`

