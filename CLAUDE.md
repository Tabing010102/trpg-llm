# CLAUDE.md - AI Assistant Instructions for TRPG-LLM

This document provides context for AI assistants (Claude, ChatGPT, etc.) working on this codebase.

## Project Overview

**TRPG-LLM** is a configuration-driven TRPG (Tabletop Role-Playing Game) framework with LLM integration. It enables running games where AI can control GM, NPCs, or Player characters, with full state management and rollback capabilities.

## Tech Stack

- **Backend**: Python 3.9+, FastAPI, Pydantic, LiteLLM
- **Frontend**: React, TypeScript, Vite
- **Testing**: pytest, pytest-asyncio

## Architecture

This project uses **Event Sourcing** pattern:
- All state changes are recorded as immutable `Event` objects with `state_diffs`
- Current state is computed by replaying events: `CurrentState = InitialState + Σ(StateDiffs)`
- Never store mutable state directly

### Key Modules

| Module | Purpose |
|--------|---------|
| `trpg_llm/api/` | FastAPI REST API |
| `trpg_llm/core/game_engine.py` | Main game orchestration |
| `trpg_llm/core/chat_pipeline.py` | LLM chat processing pipeline |
| `trpg_llm/state/state_machine.py` | Event sourcing state machine |
| `trpg_llm/llm/` | LLM integration (LiteLLM wrapper) |
| `trpg_llm/models/` | Pydantic data models |
| `trpg_llm/sandbox/` | Safe Python script execution |
| `frontend/` | React + TypeScript UI |

## Development Commands

```bash
# Backend
pip install -r requirements.txt
pip install -e .
pytest tests/ -v --cov=trpg_llm
ruff check trpg_llm/ tests/
ruff format trpg_llm/ tests/
python -m trpg_llm.main --port 8000

# Frontend
cd frontend
npm install
npm run dev
npm run lint
npm run build
```

## Key Design Decisions

1. **Event Sourcing**: All mutations go through `StateMachine.add_event()` - never modify state directly
2. **State Diffs**: Use atomic operations (`set`, `add`, `subtract`, `append`, etc.)
3. **LLM Abstraction**: `LLMClient` wraps LiteLLM for multi-provider support
4. **Tool Calling**: LLM can call tools that produce `state_diffs`
5. **Re-hydration**: On edit/rollback, state is recalculated from event history

## Common Tasks

### Adding a New Tool

1. Define tool function in `core/builtin_tools.py`
2. Register with schema in `create_builtin_tools_registry()`
3. Tool must return `{"result": ..., "state_diffs": [...]}`

### Adding a New API Endpoint

1. Define request/response schemas in `api/schemas.py`
2. Add route handler in `api/server.py`
3. Use `GameEngine` for state changes

### Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Mock LLM calls to avoid API dependencies
- Use `@pytest.mark.asyncio` for async tests

## File Patterns

- `*.py` - Python source files (use type hints, Pydantic models)
- `tests/test_*.py` - Test files (pytest)
- `configs/*.yaml` - Game configuration files
- `frontend/src/components/*.tsx` - React components
- `frontend/src/types/*.ts` - TypeScript type definitions

## Things to Avoid

- Bypassing `StateMachine` for state changes
- Using `any` type in TypeScript
- Hardcoding LLM provider specifics (use LiteLLM)
- File I/O or network in sandbox scripts
- Breaking backward compatibility with `llm_config`

