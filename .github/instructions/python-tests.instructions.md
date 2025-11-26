---
applyTo: "**/tests/**/*.py"
---

# Python Test Requirements

When writing or modifying Python tests for this project, please follow these guidelines:

## Test Structure

1. **Use pytest** as the testing framework
2. **Organize tests** by module:
   - `tests/unit/` - Unit tests for individual functions/classes
   - `tests/integration/` - Integration tests for pipelines and workflows

## Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test functions: `test_<function_name>_<scenario>`
- Example: `test_roll_dice_with_modifier`, `test_state_machine_rollback`

## Test Patterns

### Use Table-Driven Tests

```python
import pytest

@pytest.mark.parametrize("notation,expected_count,expected_sides", [
    ("1d20", 1, 20),
    ("3d6", 3, 6),
    ("2d10+5", 2, 10),
])
def test_parse_notation(notation, expected_count, expected_sides):
    count, sides, _ = dice_system.parse_notation(notation)
    assert count == expected_count
    assert sides == expected_sides
```

### Use Fixtures for Common Setup

```python
@pytest.fixture
def game_config():
    return GameConfig(
        name="Test Game",
        rule_system="test",
        characters={...},
        llm_config={...}
    )

@pytest.fixture
def game_engine(game_config):
    return GameEngine(game_config)
```

### Mock LLM Calls

Always mock LLM client calls to avoid external API dependencies:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_chat():
    with patch.object(LLMClient, 'complete', new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = {
            "content": "Test response",
            "tool_calls": []
        }
        # Test code here
```

## What to Test

1. **Happy path** - Normal operation
2. **Edge cases** - Empty inputs, boundary values
3. **Error handling** - Invalid inputs, exceptions
4. **State changes** - Verify `state_diffs` are correctly applied
5. **Event history** - Verify events are recorded properly

## Event Sourcing Tests

When testing state changes:

```python
def test_state_update_creates_event(game_engine):
    initial_events = len(game_engine.get_event_history())
    
    game_engine.update_state(
        actor_id="test",
        path="characters.player1.state.hp",
        operation="subtract",
        value=5
    )
    
    events = game_engine.get_event_history()
    assert len(events) == initial_events + 1
    assert events[-1].state_diffs[0].operation == "subtract"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=trpg_llm --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_dice.py -v

# Run tests matching pattern
pytest tests/ -k "test_roll" -v
```

## Test Dependencies

Ensure test dependencies are available:
- `pytest`
- `pytest-asyncio` - For async tests
- `pytest-cov` - For coverage reports

