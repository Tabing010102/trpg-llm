"""
Basic usage example for TRPG-LLM framework
"""

from trpg_llm.core.game_engine import GameEngine
from trpg_llm.config.loader import ConfigLoader
from trpg_llm.models.dice import DiceRoll
from trpg_llm.models.event import StateDiff


def main():
    """Demonstrate basic framework usage"""
    
    # Load configuration
    print("Loading game configuration...")
    config = ConfigLoader.load_from_file("configs/simple_game.json")
    
    # Create game engine
    print(f"Creating game: {config.name}")
    engine = GameEngine(config)
    
    # Get initial state
    state = engine.get_state()
    print(f"Session ID: {state.session_id}")
    print(f"Initial location: {state.state.get('location')}")
    print(f"Characters: {list(state.characters.keys())}")
    
    # Roll some dice
    print("\nRolling 1d20...")
    dice_roll = DiceRoll(
        notation="1d20",
        reason="Initiative check",
        character_id="player1",
    )
    state = engine.roll_dice(dice_roll)
    
    # Get the result
    last_event = engine.get_event_history()[-1]
    result = last_event.data["result"]
    print(f"Result: {result['final_result']} (rolls: {result['rolls']})")
    
    # Update state
    print("\nUpdating player HP...")
    state = engine.update_state(
        actor_id="gm",
        path="characters.player1.state.hp",
        operation="subtract",
        value=5,
    )
    
    # Check updated HP
    player = state.characters["player1"]
    print(f"Player HP after damage: {player.state.get('hp')}")
    
    # Add a message
    print("\nAdding game message...")
    state = engine.add_message(
        sender_id="gm",
        content="A goblin attacks!",
        message_type="narration",
    )
    
    # Show message history
    print(f"Total messages: {len(state.messages)}")
    for msg in state.messages:
        print(f"  - {msg['sender_id']}: {msg['content']}")
    
    # Demonstrate rollback
    print("\nDemonstrating rollback...")
    print(f"Current turn: {state.current_turn}")
    print(f"Total events: {len(engine.get_event_history())}")
    
    # Get event ID of the dice roll
    dice_event = [e for e in engine.get_event_history() if e.type == "dice_roll"][0]
    print(f"Rolling back to event: {dice_event.id}")
    
    state = engine.rollback_to_event(dice_event.id)
    print(f"Total events after rollback: {len(engine.get_event_history())}")
    
    # Save session
    print("\nGame session summary:")
    session = engine.get_session()
    print(f"Session ID: {session.session_id}")
    print(f"Total events: {len(session.event_history)}")
    print(f"Current turn: {session.current_state.current_turn}")


if __name__ == "__main__":
    main()
