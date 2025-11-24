"""Tests for AIAgentManager with LLM profiles"""

import pytest
from trpg_llm.llm.agent_manager import AIAgentManager
from trpg_llm.models.game_state import GameConfig


class TestAIAgentManagerProfiles:
    """Test AIAgentManager with LLM profile support"""
    
    def test_initialization_with_profiles(self):
        """Test manager initialization with llm_profiles"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI Character",
                    "type": "player",
                    "control": "ai",
                    "ai_config": {
                        "profile_id": "gpt4"
                    }
                }
            },
            llm_config={
                "default_profile_id": "gpt3"
            },
            llm_profiles=[
                {
                    "id": "gpt3",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                {
                    "id": "gpt4",
                    "model": "gpt-4",
                    "temperature": 0.5
                }
            ]
        )
        
        manager = AIAgentManager(config)
        
        # Should have profile registry
        assert manager.profile_registry is not None
        assert manager.profile_registry.has_profile("gpt3")
        assert manager.profile_registry.has_profile("gpt4")
        
        # Agent should be created
        assert manager.has_agent("ai1")
    
    def test_backward_compatibility_no_profiles(self):
        """Test manager works without llm_profiles (backward compatibility)"""
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
            llm_config={
                "default_model": "gpt-3.5-turbo",
                "temperature": 0.7
            }
        )
        
        manager = AIAgentManager(config)
        
        # Should create default profile automatically
        assert manager.profile_registry is not None
        assert manager.profile_registry.has_profile("default")
        
        # Agent should still be created
        assert manager.has_agent("ai1")
    
    def test_agent_uses_character_profile(self):
        """Test that agent uses profile specified in character config"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI 1",
                    "type": "player",
                    "control": "ai",
                    "ai_config": {
                        "profile_id": "fast_model"
                    }
                },
                "ai2": {
                    "id": "ai2",
                    "name": "AI 2",
                    "type": "player",
                    "control": "ai",
                    "ai_config": {
                        "profile_id": "smart_model"
                    }
                }
            },
            llm_profiles=[
                {
                    "id": "fast_model",
                    "model": "gpt-3.5-turbo",
                    "temperature": 1.0
                },
                {
                    "id": "smart_model",
                    "model": "gpt-4",
                    "temperature": 0.3
                }
            ],
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        # Both agents should exist
        assert manager.has_agent("ai1")
        assert manager.has_agent("ai2")
        
        # Check that they're using correct models (through their LLM clients)
        agent1 = manager.get_agent("ai1")
        agent2 = manager.get_agent("ai2")
        
        assert agent1.llm_client.model == "gpt-3.5-turbo"
        assert agent2.llm_client.model == "gpt-4"
    
    def test_agent_fallback_to_default_profile(self):
        """Test agent falls back to default profile if not specified"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI Character",
                    "type": "player",
                    "control": "ai"
                    # No profile_id specified
                }
            },
            llm_config={
                "default_profile_id": "default_gpt"
            },
            llm_profiles=[
                {
                    "id": "default_gpt",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                }
            ]
        )
        
        manager = AIAgentManager(config)
        
        agent = manager.get_agent("ai1")
        assert agent.llm_client.model == "gpt-3.5-turbo"
    
    def test_create_llm_client_from_profile(self):
        """Test creating LLM client from profile ID"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={},
            llm_profiles=[
                {
                    "id": "test_profile",
                    "model": "gpt-4",
                    "temperature": 0.5
                }
            ],
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        client = manager.create_llm_client_from_profile("test_profile")
        
        assert client is not None
        assert client.model == "gpt-4"
    
    def test_create_llm_client_from_nonexistent_profile(self):
        """Test creating client from non-existent profile returns None"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={},
            llm_profiles=[],
            llm_config={}
        )
        
        manager = AIAgentManager(config)
        
        client = manager.create_llm_client_from_profile("nonexistent")
        
        assert client is None
    
    def test_legacy_ai_config_overrides(self):
        """Test that legacy ai_config fields work when profile not found"""
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "ai1": {
                    "id": "ai1",
                    "name": "AI Character",
                    "type": "player",
                    "control": "ai",
                    "ai_config": {
                        "profile_id": "nonexistent",
                        "model": "custom-model",
                        "temperature": 0.9
                    }
                }
            },
            llm_config={},
            llm_profiles=[]
        )
        
        manager = AIAgentManager(config)
        
        # Agent should still be created with legacy config
        agent = manager.get_agent("ai1")
        assert agent is not None
        # Legacy fallback should use the model from ai_config
        assert agent.llm_client.model == "custom-model"
