"""Integration tests for GameEngine enhancements"""

import pytest
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.models.game_state import GameConfig
from trpg_llm.models.event import EventType, StateDiff


class TestGameEngineEnhancements:
    """Test GameEngine enhancements"""
    
    def get_test_config(self):
        """Get a test configuration"""
        return GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Hero",
                    "type": "player",
                    "control": "human",
                    "state": {"hp": 20}
                },
                "gm": {
                    "id": "gm",
                    "name": "GM",
                    "type": "gm",
                    "control": "ai"
                }
            },
            scripts={
                "on_turn_end": """
# Calculate bonus at turn end
state_updates = []
if current_turn > 0 and current_turn % 3 == 0:
    state_updates.append({
        "path": "bonus_turns",
        "operation": "set",
        "value": current_turn // 3
    })
"""
            }
        )
    
    def test_script_hook_execution(self):
        """Test script hook execution on turn end"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Start and end turn 1
        engine.start_turn("player1", 1)
        engine.end_turn("player1")
        
        # Start and end turn 2
        engine.start_turn("player1", 2)
        engine.end_turn("player1")
        
        # Start and end turn 3 (should trigger script)
        engine.start_turn("player1", 3)
        engine.end_turn("player1")
        
        # Check if script was executed
        state = engine.get_state()
        # The script should set bonus_turns when turn is divisible by 3
        assert "bonus_turns" in state.state
        assert state.state["bonus_turns"] == 1
    
    def test_execute_script_method(self):
        """Test direct script execution"""
        config = GameConfig(
            name="Test",
            rule_system="generic",
            characters={},
            initial_state={"value": 10}
        )
        engine = GameEngine(config)
        
        script = "result = state.get('value', 0) * 2"
        result = engine.execute_script(script)
        
        assert result["result"] == 20
    
    def test_redraw_last_ai_message(self):
        """Test redrawing last AI message"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Add some messages
        engine.add_message("player1", "Hello")
        engine.add_message("gm", "Welcome, adventurer!")
        engine.add_message("player1", "Thanks")
        
        # Get current event count
        event_count_before = len(engine.get_event_history())
        
        # Redraw last GM message
        state = engine.redraw_last_ai_message("gm")
        
        # Should have rolled back to before the GM message
        event_count_after = len(engine.get_event_history())
        assert event_count_after < event_count_before
        
        # Verify the GM message and subsequent player message are gone
        messages = state.messages
        assert len(messages) == 1
        assert messages[0]["sender_id"] == "player1"
        assert messages[0]["content"] == "Hello"
    
    def test_edit_event(self):
        """Test editing an event"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Add a message
        engine.add_message("player1", "Original message")
        
        # Get the message event
        events = engine.find_events_by_type(EventType.MESSAGE)
        message_event = events[-1]
        
        # Edit the message
        new_state = engine.edit_event(
            event_id=message_event.id,
            new_data={
                "sender_id": "player1",
                "content": "Edited message",
                "type": "text"
            }
        )
        
        # Verify the message was edited
        assert new_state.messages[-1]["content"] == "Edited message"
    
    def test_get_event_by_id(self):
        """Test getting event by ID"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Add a message
        engine.add_message("player1", "Test message")
        
        # Get the event
        events = engine.get_event_history()
        last_event = events[-1]
        
        # Retrieve by ID
        retrieved = engine.get_event_by_id(last_event.id)
        
        assert retrieved is not None
        assert retrieved.id == last_event.id
        assert retrieved.type == EventType.MESSAGE
    
    def test_find_events_by_type(self):
        """Test finding events by type"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Create various events
        engine.add_message("player1", "Message 1")
        engine.start_turn("player1", 1)
        engine.add_message("player1", "Message 2")
        engine.end_turn("player1")
        
        # Find message events
        message_events = engine.find_events_by_type(EventType.MESSAGE)
        assert len(message_events) == 2
        
        # Find turn events
        turn_start_events = engine.find_events_by_type(EventType.TURN_START)
        assert len(turn_start_events) == 1
        
        turn_end_events = engine.find_events_by_type(EventType.TURN_END)
        assert len(turn_end_events) == 1
    
    def test_find_events_by_actor(self):
        """Test finding events by actor"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Create events with different actors
        engine.add_message("player1", "Player message")
        engine.add_message("gm", "GM message")
        engine.add_message("player1", "Another player message")
        
        # Find player1 events
        player_events = engine.find_events_by_actor("player1")
        assert len(player_events) == 2
        
        # Find GM events
        gm_events = engine.find_events_by_actor("gm")
        assert len(gm_events) == 1
    
    def test_edit_event_with_state_diffs(self):
        """Test editing event with new state diffs"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        # Update state
        initial_state = engine.update_state(
            actor_id="player1",
            path="characters.player1.state.hp",
            operation="set",
            value=15
        )
        
        assert initial_state.characters["player1"].state["hp"] == 15
        
        # Get the event
        events = engine.find_events_by_type(EventType.STATE_UPDATE)
        update_event = events[-1]
        
        # Edit with new state diff
        new_state_diffs = [
            StateDiff(
                path="characters.player1.state.hp",
                operation="set",
                value=10
            )
        ]
        
        new_state = engine.edit_event(
            event_id=update_event.id,
            new_state_diffs=new_state_diffs
        )
        
        # Verify the state was updated with new value
        assert new_state.characters["player1"].state["hp"] == 10
    
    def test_redraw_nonexistent_character(self):
        """Test redrawing message from nonexistent character"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        with pytest.raises(ValueError, match="No message found"):
            engine.redraw_last_ai_message("nonexistent")
    
    def test_edit_nonexistent_event(self):
        """Test editing nonexistent event"""
        config = self.get_test_config()
        engine = GameEngine(config)
        
        with pytest.raises(ValueError, match="not found"):
            engine.edit_event(
                event_id="nonexistent",
                new_data={}
            )
