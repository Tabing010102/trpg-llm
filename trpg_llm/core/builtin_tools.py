"""Built-in tool functions for game actions"""

from typing import Dict, Any
from ..models.dice import DiceRoll
from ..models.event import StateDiff


def create_builtin_tools_registry():
    """Create and populate a tool registry with built-in tools"""
    from .tool_executor import ToolRegistry
    
    registry = ToolRegistry()
    
    # Register roll_dice
    registry.register_function(
        "roll_dice",
        roll_dice_tool,
        schema={
            "type": "function",
            "function": {
                "name": "roll_dice",
                "description": "Roll dice using standard notation (e.g., 1d20, 3d6+5)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "notation": {
                            "type": "string",
                            "description": "Dice notation (e.g., '1d20', '3d6+5', '1d100')"
                        },
                        "character_id": {
                            "type": "string",
                            "description": "ID of the character rolling the dice"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the roll (e.g., 'attack roll', 'perception check')"
                        },
                        "target": {
                            "type": "integer",
                            "description": "Target number for success (optional)"
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["regular", "hard", "extreme"],
                            "description": "Difficulty level for CoC checks (optional)"
                        }
                    },
                    "required": ["notation", "character_id"]
                }
            }
        }
    )
    
    # Register update_state
    registry.register_function(
        "update_state",
        update_state_tool,
        schema={
            "type": "function",
            "function": {
                "name": "update_state",
                "description": "Update game state (character attributes, global state, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Dot-notation path to update (e.g., 'characters.player1.state.hp')"
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["set", "add", "subtract", "multiply", "append", "remove", "delete"],
                            "description": "Operation to perform"
                        },
                        "value": {
                            "description": "Value for the operation"
                        },
                        "actor_id": {
                            "type": "string",
                            "description": "ID of the character performing the action (optional)"
                        }
                    },
                    "required": ["path", "operation", "value"]
                }
            }
        }
    )
    
    # Register roll_skill (CoC specific)
    registry.register_function(
        "roll_skill",
        roll_skill_tool,
        schema={
            "type": "function",
            "function": {
                "name": "roll_skill",
                "description": "Roll a skill check (Call of Cthulhu style)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_id": {
                            "type": "string",
                            "description": "ID of the character making the check"
                        },
                        "skill_name": {
                            "type": "string",
                            "description": "Name of the skill (e.g., 'Spot Hidden', 'Psychology')"
                        },
                        "skill_value": {
                            "type": "integer",
                            "description": "Character's skill value"
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["regular", "hard", "extreme"],
                            "description": "Difficulty level"
                        }
                    },
                    "required": ["character_id", "skill_name", "skill_value"]
                }
            }
        }
    )
    
    return registry


def roll_dice_tool(arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function for rolling dice.
    
    Args:
        arguments: Tool arguments (notation, character_id, reason, target, difficulty)
        context: Execution context (game_engine, game_state)
    
    Returns:
        Result with dice roll outcome
    """
    game_engine = context.get("game_engine")
    if not game_engine:
        raise ValueError("game_engine not provided in context")
    
    # Create dice roll
    dice_roll = DiceRoll(
        notation=arguments["notation"],
        character_id=arguments["character_id"],
        reason=arguments.get("reason"),
        target=arguments.get("target"),
        difficulty=arguments.get("difficulty", "regular")
    )
    
    # Execute roll through game engine
    new_state = game_engine.roll_dice(dice_roll)
    
    # Get result from last event
    last_event = game_engine.get_event_history()[-1]
    result = last_event.data.get("result", {})
    
    return {
        "result": result,
        "state_diffs": [diff.dict() for diff in last_event.state_diffs]
    }


def update_state_tool(arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function for updating game state.
    
    Args:
        arguments: Tool arguments (path, operation, value, actor_id)
        context: Execution context (game_engine, game_state, role_id)
    
    Returns:
        Result with updated state
    """
    game_engine = context.get("game_engine")
    if not game_engine:
        raise ValueError("game_engine not provided in context")
    
    # Get actor_id from arguments or context
    actor_id = arguments.get("actor_id") or context.get("role_id")
    
    # Update state through game engine
    new_state = game_engine.update_state(
        actor_id=actor_id,
        path=arguments["path"],
        operation=arguments["operation"],
        value=arguments["value"]
    )
    
    # Get state diffs from last event
    last_event = game_engine.get_event_history()[-1]
    
    return {
        "result": {"success": True, "path": arguments["path"]},
        "state_diffs": [diff.dict() for diff in last_event.state_diffs]
    }


def roll_skill_tool(arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool function for rolling skill checks.
    
    Args:
        arguments: Tool arguments (character_id, skill_name, skill_value, difficulty)
        context: Execution context (game_engine, game_state)
    
    Returns:
        Result with skill check outcome
    """
    game_engine = context.get("game_engine")
    if not game_engine:
        raise ValueError("game_engine not provided in context")
    
    # Create dice roll for skill check (1d100 for CoC)
    difficulty = arguments.get("difficulty", "regular")
    skill_value = arguments["skill_value"]
    
    dice_roll = DiceRoll(
        notation="1d100",
        character_id=arguments["character_id"],
        reason=f"Skill check: {arguments['skill_name']}",
        target=skill_value,
        difficulty=difficulty
    )
    
    # Execute roll through game engine
    new_state = game_engine.roll_dice(dice_roll)
    
    # Get result from last event
    last_event = game_engine.get_event_history()[-1]
    result = last_event.data.get("result", {})
    
    return {
        "result": result,
        "state_diffs": [diff.dict() for diff in last_event.state_diffs]
    }
