"""Tests for AI agent manager"""

import pytest
from trpg_llm.llm.agent_manager import AIAgentManager
from trpg_llm.models.game_state import GameConfig
from trpg_llm.models.character import Character, CharacterType, CharacterControlType


class TestAIAgentManager:
    """Test AIAgentManager functionality"""
    
    def test_initialization_with_ai_characters(self):
        """Test manager initialization with AI characters"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Human Player",
                    "type": "player",
                    "control": "human"
                },
                "gm": {
                    "id": "gm",
                    "name": "AI GM",
                    "type": "gm",
                    "control": "ai",
                    "ai_config": {
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.7
                    }
                }
            },
            llm_config={
                "default_model": "gpt-3.5-turbo"
            }
        )
        
        manager = AIAgentManager(config)
        
        # Should only create agent for AI character
        assert manager.has_agent("gm")
        assert not manager.has_agent("player1")
        assert len(manager.list_agents()) == 1
    
    def test_get_agent(self):
        """Test getting an agent"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai_npc": {
                    "id": "ai_npc",
                    "name": "AI NPC",
                    "type": "npc",
                    "control": "ai"
                }
            },
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        agent = manager.get_agent("ai_npc")
        assert agent is not None
        assert agent.character.id == "ai_npc"
    
    def test_get_nonexistent_agent(self):
        """Test getting an agent that doesn't exist"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={},
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        agent = manager.get_agent("nonexistent")
        assert agent is None
    
    def test_add_message_to_agent(self):
        """Test adding message to agent history"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI Character",
                    "type": "player",
                    "control": "ai"
                }
            },
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        manager.add_message_to_agent("ai1", "user", "Test message")
        
        agent = manager.get_agent("ai1")
        assert len(agent.message_history) == 1
        assert agent.message_history[0]["content"] == "Test message"
    
    def test_clear_agent_history(self):
        """Test clearing agent history"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI Character",
                    "type": "player",
                    "control": "ai"
                }
            },
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        manager.add_message_to_agent("ai1", "user", "Test")
        agent = manager.get_agent("ai1")
        assert len(agent.message_history) == 1
        
        manager.clear_agent_history("ai1")
        assert len(agent.message_history) == 0
    
    def test_clear_all_histories(self):
        """Test clearing all agent histories"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI 1",
                    "type": "player",
                    "control": "ai"
                },
                "ai2": {
                    "id": "ai2",
                    "name": "AI 2",
                    "type": "npc",
                    "control": "ai"
                }
            },
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        manager.add_message_to_agent("ai1", "user", "Test 1")
        manager.add_message_to_agent("ai2", "user", "Test 2")
        
        manager.clear_all_histories()
        
        agent1 = manager.get_agent("ai1")
        agent2 = manager.get_agent("ai2")
        assert len(agent1.message_history) == 0
        assert len(agent2.message_history) == 0
    
    def test_custom_system_prompt(self):
        """Test custom system prompt from character config"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "Custom AI",
                    "type": "player",
                    "control": "ai",
                    "ai_config": {
                        "system_prompt": "You are a custom character with a unique prompt."
                    }
                }
            },
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        agent = manager.get_agent("ai1")
        
        assert "custom character" in agent.system_prompt.lower()
    
    def test_tools_formatting(self):
        """Test tools are properly formatted for agents"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI",
                    "type": "player",
                    "control": "ai"
                }
            },
            tools=[
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {}
                }
            ],
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        agent = manager.get_agent("ai1")
        
        assert len(agent.tools) == 1
        assert agent.tools[0]["type"] == "function"
        assert agent.tools[0]["function"]["name"] == "test_tool"
