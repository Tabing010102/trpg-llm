"""Integration tests for ChatPipeline with LLM profile support"""

import pytest
from trpg_llm.core.game_engine import GameEngine
from trpg_llm.core.chat_pipeline import ChatPipeline
from trpg_llm.core.builtin_tools import create_builtin_tools_registry
from trpg_llm.llm.agent_manager import AIAgentManager
from trpg_llm.models.game_state import GameConfig


class TestChatPipelineProfiles:
    """Test ChatPipeline with LLM profile support"""
    
    @pytest.fixture
    def game_config_with_profiles(self):
        """Config with multiple LLM profiles"""
        return GameConfig(
            name="Profile Test Game",
            rule_system="generic",
            description="Testing profile switching",
            characters={
                "gm": {
                    "id": "gm",
                    "name": "Game Master",
                    "type": "gm",
                    "control": "ai",
                    "ai_config": {
                        "profile_id": "gm_profile"
                    }
                },
                "player": {
                    "id": "player",
                    "name": "Player",
                    "type": "player",
                    "control": "human"
                }
            },
            llm_config={
                "default_profile_id": "gm_profile"
            },
            llm_profiles=[
                {
                    "id": "gm_profile",
                    "provider_type": "oai_compatible",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                {
                    "id": "creative_profile",
                    "provider_type": "oai_compatible",
                    "model": "gpt-4",
                    "temperature": 1.0
                },
                {
                    "id": "precise_profile",
                    "provider_type": "oai_compatible",
                    "model": "gpt-4",
                    "temperature": 0.3
                }
            ]
        )
    
    def test_chat_with_default_profile(self, game_config_with_profiles):
        """Test chat using character's default profile"""
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        # Human message should work
        result = pipeline.process_chat_sync(
            role_id="player",
            message="Hello!"
        )
        
        assert result["content"] == "Hello!"
        assert result["role_id"] == "player"
        assert not result["is_ai"]
        assert result.get("used_profile_id") is None  # Human characters don't use profiles
    
    def test_ai_chat_records_used_profile(self, game_config_with_profiles):
        """Test that AI chat records which profile was used"""
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        # Mock AI response
        agent = agent_manager.get_agent("gm")
        original_get_response = agent.get_response_sync
        
        def mock_response(game_state, prompt):
            return {
                "content": "Welcome to the game!",
                "tool_calls": [],
                "finish_reason": "stop"
            }
        
        agent.get_response_sync = mock_response
        
        try:
            result = pipeline.process_chat_sync(
                role_id="gm",
                message=None
            )
            
            assert result["is_ai"]
            assert result["used_profile_id"] == "gm_profile"
            assert result["content"] == "Welcome to the game!"
            
            # Check message metadata (in data.metadata, not event.metadata)
            events = engine.get_event_history()
            last_event = events[-1]
            msg_metadata = last_event.data.get("metadata", {})
            assert msg_metadata.get("used_profile_id") == "gm_profile"
            assert msg_metadata.get("provider_type") == "oai_compatible"
            assert msg_metadata.get("model") == "gpt-3.5-turbo"
        finally:
            agent.get_response_sync = original_get_response
    
    def test_chat_with_explicit_profile(self, game_config_with_profiles):
        """Test chat with explicitly specified profile"""
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        agent = agent_manager.get_agent("gm")
        original_get_response = agent.get_response_sync
        
        def mock_response(game_state, prompt):
            return {
                "content": "Creative response!",
                "tool_calls": [],
                "finish_reason": "stop"
            }
        
        agent.get_response_sync = mock_response
        
        try:
            # Use creative_profile instead of default
            result = pipeline.process_chat_sync(
                role_id="gm",
                message=None,
                llm_profile_id="creative_profile"
            )
            
            assert result["is_ai"]
            assert result["used_profile_id"] == "creative_profile"
            
            # Check that the agent's LLM client was temporarily switched
            # (and then restored)
            assert agent.llm_client.model == "gpt-3.5-turbo"  # Back to default
            
            # Check metadata
            events = engine.get_event_history()
            last_event = events[-1]
            msg_metadata = last_event.data.get("metadata", {})
            assert msg_metadata.get("used_profile_id") == "creative_profile"
            assert msg_metadata.get("model") == "gpt-4"
        finally:
            agent.get_response_sync = original_get_response
    
    def test_chat_with_nonexistent_profile_fallback(self, game_config_with_profiles):
        """Test that nonexistent profile falls back to default"""
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        agent = agent_manager.get_agent("gm")
        original_get_response = agent.get_response_sync
        
        def mock_response(game_state, prompt):
            return {
                "content": "Response with fallback",
                "tool_calls": [],
                "finish_reason": "stop"
            }
        
        agent.get_response_sync = mock_response
        
        try:
            # Request nonexistent profile
            result = pipeline.process_chat_sync(
                role_id="gm",
                message=None,
                llm_profile_id="nonexistent_profile"
            )
            
            assert result["is_ai"]
            # Should fall back to character's default profile
            assert result["used_profile_id"] == "gm_profile"
        finally:
            agent.get_response_sync = original_get_response
    
    def test_profile_preserved_across_tool_iterations(self, game_config_with_profiles):
        """Test that profile is maintained across tool calling iterations"""
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        agent = agent_manager.get_agent("gm")
        original_get_response = agent.get_response_sync
        
        call_count = [0]
        
        def mock_response(game_state, prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: return tool call
                return {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "roll_dice",
                                "arguments": '{"notation": "1d20"}'
                            }
                        }
                    ],
                    "finish_reason": "tool_calls"
                }
            else:
                # Second call: return final content
                return {
                    "content": "After rolling, the result is...",
                    "tool_calls": [],
                    "finish_reason": "stop"
                }
        
        agent.get_response_sync = mock_response
        
        try:
            result = pipeline.process_chat_sync(
                role_id="gm",
                message=None,
                llm_profile_id="precise_profile"
            )
            
            assert result["is_ai"]
            assert result["used_profile_id"] == "precise_profile"
            assert len(result["tool_calls"]) > 0
            
            # Verify profile is in metadata
            events = engine.get_event_history()
            last_event = events[-1]
            msg_metadata = last_event.data.get("metadata", {})
            assert msg_metadata.get("used_profile_id") == "precise_profile"
        finally:
            agent.get_response_sync = original_get_response
    
    def test_async_chat_with_profile(self, game_config_with_profiles):
        """Test async chat with profile switching"""
        import asyncio
        
        engine = GameEngine(game_config_with_profiles, "test_session")
        agent_manager = AIAgentManager(game_config_with_profiles)
        tool_registry = create_builtin_tools_registry()
        pipeline = ChatPipeline(engine, tool_registry, agent_manager)
        
        agent = agent_manager.get_agent("gm")
        original_get_response = agent.get_response
        
        async def mock_response(game_state, prompt):
            return {
                "content": "Async response with profile",
                "tool_calls": [],
                "finish_reason": "stop"
            }
        
        agent.get_response = mock_response
        
        async def run_test():
            result = await pipeline.process_chat(
                role_id="gm",
                message=None,
                llm_profile_id="creative_profile"
            )
            
            assert result["is_ai"]
            assert result["used_profile_id"] == "creative_profile"
            
            # Agent should be back to default
            assert agent.llm_client.model == "gpt-3.5-turbo"
        
        try:
            asyncio.run(run_test())
        finally:
            agent.get_response = original_get_response
