"""Integration tests for game engine"""

import pytest
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.models.game_state import GameConfig
from trpg_llm.models.dice import DiceRoll


class TestGameEngineIntegration:
    """Test game engine integration"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return GameConfig(
            name="Test Game",
            rule_system="test",
            initial_state={"location": "start"},
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Hero",
                    "type": "player",
                    "control": "human",
                    "state": {"hp": 20},
                },
                "gm": {
                    "id": "gm",
                    "name": "GM",
                    "type": "gm",
                    "control": "human",
                },
            },
        )
    
    def test_create_game_engine(self, config):
        """Test creating game engine"""
        engine = GameEngine(config)
        
        assert engine.session_id is not None
        assert engine.config == config
        
        # Should have game_start event
        assert len(engine.get_event_history()) == 1
        assert engine.get_event_history()[0].type == "game_start"
    
    def test_dice_rolling_flow(self, config):
        """Test complete dice rolling flow"""
        engine = GameEngine(config)
        
        # Roll dice
        dice_roll = DiceRoll(
            notation="1d20+5",
            reason="Attack roll",
            character_id="player1",
        )
        state = engine.roll_dice(dice_roll)
        
        # Verify result
        events = engine.get_event_history()
        dice_event = [e for e in events if e.type == "dice_roll"][0]
        result = dice_event.data["result"]
        
        assert "rolls" in result
        assert "final_result" in result
        assert result["modifier"] == 5
    
    def test_state_update_flow(self, config):
        """Test state update flow"""
        engine = GameEngine(config)
        
        # Update character HP
        state = engine.update_state(
            actor_id="gm",
            path="characters.player1.state.hp",
            operation="subtract",
            value=5,
        )
        
        # Verify state
        assert state.characters["player1"].state["hp"] == 15
    
    def test_message_flow(self, config):
        """Test message flow"""
        engine = GameEngine(config)
        
        # Add messages
        engine.add_message("gm", "Welcome to the game!")
        engine.add_message("player1", "Hello!")
        
        state = engine.get_state()
        
        assert len(state.messages) == 2
        assert state.messages[0]["content"] == "Welcome to the game!"
        assert state.messages[1]["content"] == "Hello!"
    
    def test_turn_management(self, config):
        """Test turn management"""
        engine = GameEngine(config)
        
        # Start turn
        state = engine.start_turn("player1")
        assert state.current_turn == 1
        assert state.current_actor == "player1"
        
        # End turn
        state = engine.end_turn("player1")
        
        # Start next turn
        state = engine.start_turn("gm")
        assert state.current_turn == 2
    
    def test_complete_game_flow(self, config):
        """Test a complete game flow"""
        engine = GameEngine(config)
        
        # GM starts the game
        engine.add_message("gm", "You enter a dark room.")
        
        # Player performs action
        engine.perform_action(
            actor_id="player1",
            action_type="investigate",
            data={"target": "room"},
        )
        
        # Player rolls perception
        dice_roll = DiceRoll(notation="1d20", character_id="player1")
        engine.roll_dice(dice_roll)
        
        # GM narrates result
        engine.add_message("gm", "You find a hidden door!")
        
        # Update game state
        engine.update_state(
            actor_id="gm",
            path="location",
            operation="set",
            value="secret_passage",
        )
        
        # Verify final state
        state = engine.get_state()
        assert len(state.messages) == 2
        assert state.state["location"] == "secret_passage"
        
        # Verify event history
        events = engine.get_event_history()
        assert len(events) >= 5  # game_start + actions
    
    def test_rollback_scenario(self, config):
        """Test rollback in a game scenario"""
        engine = GameEngine(config)
        
        # Initial actions
        engine.add_message("gm", "Turn 1")
        state1 = engine.get_state()
        
        engine.add_message("player1", "Action 1")
        engine.add_message("gm", "Turn 2")
        state2 = engine.get_state()
        
        # More actions
        engine.add_message("player1", "Action 2")
        
        # Rollback to turn 2
        event_id = [e for e in engine.get_event_history() 
                   if e.type == "message" and e.data.get("content") == "Turn 2"][0].id
        
        state = engine.rollback_to_event(event_id)
        
        # Should have messages up to Turn 2
        assert len(state.messages) == 3
        assert state.messages[-1]["content"] == "Turn 2"
