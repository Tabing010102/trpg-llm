"""
Example demonstrating the chat pipeline and tool calling features.

This example shows:
1. Creating a game with AI and human characters
2. Using the chat pipeline for message processing
3. Tool calling (roll_dice, update_state)
4. Script hooks for game logic
5. Rollback and event editing
"""

import asyncio
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.core.chat_pipeline import ChatPipeline
from trpg_llm.core.builtin_tools import create_builtin_tools_registry
from trpg_llm.llm.agent_manager import AIAgentManager
from trpg_llm.models.game_state import GameConfig
from trpg_llm.models.event import EventType


def create_example_config():
    """Create an example game configuration"""
    return GameConfig(
        name="Adventure Quest",
        rule_system="generic",
        description="A simple adventure with AI GM and tools",
        
        # Characters
        characters={
            "player1": {
                "id": "player1",
                "name": "Brave Knight",
                "type": "player",
                "control": "human",
                "description": "A courageous warrior",
                "attributes": {
                    "strength": 16,
                    "dexterity": 12,
                    "intelligence": 10
                },
                "state": {
                    "hp": 30,
                    "max_hp": 30,
                    "level": 3
                }
            },
            "gm": {
                "id": "gm",
                "name": "Game Master",
                "type": "gm",
                "control": "ai",
                "description": "Narrates the adventure",
                "ai_config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.8,
                    "system_prompt": "You are a creative Game Master for an adventure game. Narrate exciting scenarios and respond to player actions. Use tools to roll dice and update game state when appropriate."
                }
            }
        },
        
        # LLM Configuration
        llm_config={
            "default_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "prompts": {
                "gm_system": "You are an engaging Game Master. Create immersive narratives."
            }
        },
        
        # Available Tools
        tools=[
            {
                "name": "roll_dice",
                "description": "Roll dice using standard notation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "notation": {
                            "type": "string",
                            "description": "Dice notation (e.g., '1d20', '2d6+3')"
                        },
                        "character_id": {
                            "type": "string",
                            "description": "Character rolling the dice"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the roll"
                        }
                    },
                    "required": ["notation", "character_id"]
                }
            },
            {
                "name": "update_state",
                "description": "Update game state",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Dot-notation path (e.g., 'characters.player1.state.hp')"
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["set", "add", "subtract"],
                            "description": "Operation to perform"
                        },
                        "value": {
                            "description": "Value for the operation"
                        }
                    },
                    "required": ["path", "operation", "value"]
                }
            }
        ],
        
        # Script Hooks
        scripts={
            "on_turn_end": """
# Regenerate HP at end of turn if resting
if state.get('resting', False):
    state_updates = [{
        "path": "characters.player1.state.hp",
        "operation": "add",
        "value": 5
    }]
else:
    state_updates = []
"""
        },
        
        # Initial State
        initial_state={
            "location": "Dark Forest Entrance",
            "time": "Evening",
            "resting": False
        }
    )


async def example_human_chat():
    """Example: Human player sends a message"""
    print("\n=== Example 1: Human Chat ===")
    
    # Setup
    config = create_example_config()
    engine = GameEngine(config)
    tool_registry = create_builtin_tools_registry()
    agent_manager = AIAgentManager(config)
    pipeline = ChatPipeline(engine, tool_registry, agent_manager)
    
    # Human player sends message
    result = await pipeline.process_chat(
        role_id="player1",
        message="I look around the forest entrance."
    )
    
    print(f"Player said: {result['content']}")
    print(f"Is AI: {result['is_ai']}")
    print(f"State diffs: {result['state_diffs']}")


async def example_ai_chat_with_tools():
    """Example: AI GM uses tools during response"""
    print("\n=== Example 2: AI Chat with Tool Calling ===")
    
    # Setup
    config = create_example_config()
    engine = GameEngine(config)
    tool_registry = create_builtin_tools_registry()
    agent_manager = AIAgentManager(config)
    pipeline = ChatPipeline(engine, tool_registry, agent_manager)
    
    # Note: This would actually call OpenAI API
    # For demo purposes, we'll show the structure
    print("AI GM would process player action and use tools:")
    print("1. Roll dice for perception check")
    print("2. Update game state based on results")
    print("3. Generate narrative response")
    
    # In practice:
    # result = await pipeline.process_chat(
    #     role_id="gm",
    #     message="Player wants to search for treasure"
    # )
    # print(f"GM response: {result['content']}")
    # print(f"Tools used: {result['tool_calls']}")


def example_direct_tools():
    """Example: Direct tool usage"""
    print("\n=== Example 3: Direct Tool Usage ===")
    
    # Setup
    config = create_example_config()
    engine = GameEngine(config)
    tool_registry = create_builtin_tools_registry()
    
    # Get roll_dice tool
    roll_dice = tool_registry.get_tool("roll_dice")
    
    # Execute a dice roll
    result = roll_dice(
        {
            "notation": "1d20+5",
            "character_id": "player1",
            "reason": "Attack roll"
        },
        {"game_engine": engine}
    )
    
    print(f"Dice roll result: {result['result']}")
    
    # Get update_state tool
    update_state = tool_registry.get_tool("update_state")
    
    # Update player HP
    result = update_state(
        {
            "path": "characters.player1.state.hp",
            "operation": "subtract",
            "value": 5,
            "actor_id": "gm"
        },
        {"game_engine": engine}
    )
    
    print(f"State update result: {result['result']}")
    
    # Check updated state
    state = engine.get_state()
    print(f"Player HP: {state.characters['player1'].state['hp']}")


def example_script_hooks():
    """Example: Script hook execution"""
    print("\n=== Example 4: Script Hooks ===")
    
    # Setup
    config = create_example_config()
    engine = GameEngine(config)
    
    # Set resting to true
    engine.update_state(
        actor_id="gm",
        path="resting",
        operation="set",
        value=True
    )
    
    # Damage player
    engine.update_state(
        actor_id="gm",
        path="characters.player1.state.hp",
        operation="subtract",
        value=10
    )
    
    hp_before = engine.get_state().characters['player1'].state['hp']
    print(f"HP before turn end: {hp_before}")
    
    # End turn (triggers script hook)
    engine.start_turn("player1", 1)
    engine.end_turn("player1")
    
    hp_after = engine.get_state().characters['player1'].state['hp']
    print(f"HP after turn end (regenerated): {hp_after}")


def example_rollback():
    """Example: Rollback and event editing"""
    print("\n=== Example 5: Rollback and Event Editing ===")
    
    # Setup
    config = create_example_config()
    engine = GameEngine(config)
    
    # Add some events
    engine.add_message("player1", "I attack the goblin!")
    engine.add_message("gm", "Roll for attack!")
    event_after_attack = engine.get_event_history()[-1]
    engine.add_message("player1", "I rolled a 15!")
    
    print(f"Events: {len(engine.get_event_history())}")
    
    # Rollback to after attack message
    state = engine.rollback_to_event(event_after_attack.id)
    print(f"Events after rollback: {len(engine.get_event_history())}")
    print(f"Messages after rollback: {len(state.messages)}")
    
    # Edit an event
    message_event = engine.find_events_by_type(EventType.MESSAGE)[0]
    engine.edit_event(
        event_id=message_event.id,
        new_data={
            "sender_id": "player1",
            "content": "I attack the dragon!",  # Changed from goblin
            "type": "text"
        }
    )
    
    state = engine.get_state()
    print(f"Edited message: {state.messages[0]['content']}")


def example_custom_tool():
    """Example: Register a custom tool"""
    print("\n=== Example 6: Custom Tool Registration ===")
    
    from trpg_llm.core.tool_executor import ToolRegistry
    
    # Create registry
    registry = ToolRegistry()
    
    # Define custom tool
    def heal_character(args, context):
        """Custom tool to heal a character"""
        engine = context["game_engine"]
        char_id = args["character_id"]
        amount = args.get("amount", 10)
        
        # Update HP
        engine.update_state(
            actor_id=args.get("healer_id", "gm"),
            path=f"characters.{char_id}.state.hp",
            operation="add",
            value=amount
        )
        
        return {
            "result": f"Healed {char_id} for {amount} HP",
            "state_diffs": []
        }
    
    # Register tool
    registry.register_function(
        "heal",
        heal_character,
        schema={
            "type": "function",
            "function": {
                "name": "heal",
                "description": "Heal a character",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_id": {
                            "type": "string",
                            "description": "Character to heal"
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Amount to heal",
                            "default": 10
                        }
                    },
                    "required": ["character_id"]
                }
            }
        }
    )
    
    print(f"Registered tools: {registry.list_tools()}")
    
    # Use the tool
    config = create_example_config()
    engine = GameEngine(config)
    
    heal_tool = registry.get_tool("heal")
    result = heal_tool(
        {"character_id": "player1", "amount": 15},
        {"game_engine": engine}
    )
    
    print(f"Heal result: {result['result']}")


def main():
    """Run all examples"""
    print("TRPG-LLM: Chat Pipeline and Tools Examples")
    print("=" * 50)
    
    # Sync examples
    example_direct_tools()
    example_script_hooks()
    example_rollback()
    example_custom_tool()
    
    # Async examples
    asyncio.run(example_human_chat())
    asyncio.run(example_ai_chat_with_tools())
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
