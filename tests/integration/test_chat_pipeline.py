"""Integration tests for chat pipeline"""

import pytest
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.core.chat_pipeline import ChatPipeline
from trpg_llm.core.builtin_tools import create_builtin_tools_registry
from trpg_llm.llm.agent_manager import AIAgentManager
from trpg_llm.models.game_state import GameConfig


class TestChatPipeline:
    """Integration tests for chat pipeline"""
    
    def get_test_config(self):
        """Get a test configuration"""
        return GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Human Player",
                    "type": "player",
                    "control": "human",
                    "attributes": {"str": 15},
                    "state": {"hp": 20}
                }
            },
            initial_state={
                "location": "Village Square"
            }
        )
    
    def test_human_chat(self):
        """Test processing a human player's message"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry)
        
        result = pipeline.process_chat_sync(
            role_id="player1",
            message="I look around the village."
        )
        
        assert result["content"] == "I look around the village."
        assert result["role_id"] == "player1"
        assert result["is_ai"] is False
        assert "current_state" in result
    
    def test_builtin_tool_roll_dice(self):
        """Test roll_dice tool execution"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        
        # Execute roll_dice tool directly
        roll_dice_tool = tool_registry.get_tool("roll_dice")
        
        result = roll_dice_tool(
            {
                "notation": "1d20",
                "character_id": "player1",
                "reason": "Test roll"
            },
            {"game_engine": engine}
        )
        
        assert "result" in result
        assert "total" in result["result"]
        assert 1 <= result["result"]["total"] <= 20
    
    def test_builtin_tool_update_state(self):
        """Test update_state tool execution"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        
        # Execute update_state tool directly
        update_state_tool = tool_registry.get_tool("update_state")
        
        result = update_state_tool(
            {
                "path": "characters.player1.state.hp",
                "operation": "subtract",
                "value": 5,
                "actor_id": "player1"
            },
            {"game_engine": engine}
        )
        
        assert result["result"]["success"] is True
        
        # Verify state was updated
        state = engine.get_state()
        assert state.characters["player1"].state["hp"] == 15
    
    def test_builtin_tool_roll_skill(self):
        """Test roll_skill tool execution"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        
        # Execute roll_skill tool directly
        roll_skill_tool = tool_registry.get_tool("roll_skill")
        
        result = roll_skill_tool(
            {
                "character_id": "player1",
                "skill_name": "Investigation",
                "skill_value": 65,
                "difficulty": "regular"
            },
            {"game_engine": engine}
        )
        
        assert "result" in result
        assert "total" in result["result"]
        assert 1 <= result["result"]["total"] <= 100
    
    def test_multiple_messages(self):
        """Test processing multiple messages"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry)
        
        # Send first message
        result1 = pipeline.process_chat_sync(
            role_id="player1",
            message="I enter the tavern."
        )
        
        # Send second message
        result2 = pipeline.process_chat_sync(
            role_id="player1",
            message="I order an ale."
        )
        
        # Check that both messages are in the state
        state = engine.get_state()
        assert len(state.messages) == 2
        assert state.messages[0]["content"] == "I enter the tavern."
        assert state.messages[1]["content"] == "I order an ale."
    
    def test_state_persistence(self):
        """Test that state changes persist across messages"""
        config = self.get_test_config()
        engine = GameEngine(config)
        tool_registry = create_builtin_tools_registry()
        
        # Make a state change
        initial_hp = engine.get_state().characters["player1"].state["hp"]
        
        engine.update_state(
            actor_id="player1",
            path="characters.player1.state.hp",
            operation="subtract",
            value=3
        )
        
        # Verify change persisted
        new_hp = engine.get_state().characters["player1"].state["hp"]
        assert new_hp == initial_hp - 3
        
        # Add a message
        pipeline = ChatPipeline(engine, tool_registry)
        pipeline.process_chat_sync(
            role_id="player1",
            message="I continue exploring."
        )
        
        # Verify HP is still changed
        final_hp = engine.get_state().characters["player1"].state["hp"]
        assert final_hp == initial_hp - 3
