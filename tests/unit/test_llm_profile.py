"""Tests for LLM Profile and Profile Registry"""

import os
import pytest
from trpg_llm.llm.profile import LLMProfile, LLMProfileRegistry, ProviderType


class TestLLMProfile:
    """Test LLMProfile model"""
    
    def test_create_basic_profile(self):
        """Test creating a basic LLM profile"""
        profile = LLMProfile(
            id="test_profile",
            model="gpt-3.5-turbo",
        )
        
        assert profile.id == "test_profile"
        assert profile.model == "gpt-3.5-turbo"
        assert profile.provider_type == ProviderType.OAI_COMPATIBLE
        assert profile.temperature == 0.7
    
    def test_create_profile_with_all_fields(self):
        """Test creating a profile with all fields"""
        profile = LLMProfile(
            id="full_profile",
            provider_type=ProviderType.ANTHROPIC,
            base_url="https://api.anthropic.com",
            api_key_ref="ANTHROPIC_API_KEY",
            model="claude-2",
            temperature=0.8,
            top_p=0.9,
            max_tokens=2000,
            context_window=100000,
            extra_params={"stop_sequences": ["\n\n"]}
        )
        
        assert profile.id == "full_profile"
        assert profile.provider_type == ProviderType.ANTHROPIC
        assert profile.base_url == "https://api.anthropic.com"
        assert profile.api_key_ref == "ANTHROPIC_API_KEY"
        assert profile.model == "claude-2"
        assert profile.temperature == 0.8
        assert profile.top_p == 0.9
        assert profile.max_tokens == 2000
        assert profile.context_window == 100000
        assert profile.extra_params == {"stop_sequences": ["\n\n"]}


class TestLLMProfileRegistry:
    """Test LLMProfileRegistry functionality"""
    
    def test_empty_registry(self):
        """Test creating an empty registry"""
        registry = LLMProfileRegistry()
        
        assert len(registry.list_profiles()) == 0
        assert not registry.has_profile("any_profile")
        assert registry.get_profile("any_profile") is None
    
    def test_registry_with_profiles(self):
        """Test creating registry with profiles"""
        profiles = [
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
        
        registry = LLMProfileRegistry(profiles)
        
        assert len(registry.list_profiles()) == 2
        assert registry.has_profile("gpt3")
        assert registry.has_profile("gpt4")
        
        gpt3_profile = registry.get_profile("gpt3")
        assert gpt3_profile.model == "gpt-3.5-turbo"
        assert gpt3_profile.temperature == 0.7
    
    def test_resolve_api_key_from_env(self):
        """Test resolving API key from environment"""
        os.environ["TEST_API_KEY"] = "test_key_value"
        
        try:
            profile = LLMProfile(
                id="test",
                model="gpt-3.5-turbo",
                api_key_ref="TEST_API_KEY"
            )
            
            registry = LLMProfileRegistry([profile.dict()])
            resolved_key = registry.resolve_api_key(profile)
            
            assert resolved_key == "test_key_value"
        finally:
            del os.environ["TEST_API_KEY"]
    
    def test_resolve_api_key_not_found(self):
        """Test resolving non-existent API key"""
        profile = LLMProfile(
            id="test",
            model="gpt-3.5-turbo",
            api_key_ref="NONEXISTENT_KEY"
        )
        
        registry = LLMProfileRegistry()
        resolved_key = registry.resolve_api_key(profile)
        
        assert resolved_key is None
    
    def test_resolve_api_key_no_ref(self):
        """Test resolving when no api_key_ref provided"""
        profile = LLMProfile(
            id="test",
            model="gpt-3.5-turbo"
        )
        
        registry = LLMProfileRegistry()
        resolved_key = registry.resolve_api_key(profile)
        
        assert resolved_key is None
    
    def test_build_llm_client_params_basic(self):
        """Test building LLM client params from profile"""
        profile = LLMProfile(
            id="test",
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        registry = LLMProfileRegistry()
        params = registry.build_llm_client_params(profile)
        
        assert params["model"] == "gpt-3.5-turbo"
        assert params["temperature"] == 0.7
        assert "api_key" not in params
    
    def test_build_llm_client_params_with_api_key(self):
        """Test building params with API key"""
        os.environ["TEST_KEY"] = "my_api_key"
        
        try:
            profile = LLMProfile(
                id="test",
                model="gpt-4",
                api_key_ref="TEST_KEY"
            )
            
            registry = LLMProfileRegistry()
            params = registry.build_llm_client_params(profile)
            
            assert params["model"] == "gpt-4"
            assert params["api_key"] == "my_api_key"
        finally:
            del os.environ["TEST_KEY"]
    
    def test_build_llm_client_params_with_all_options(self):
        """Test building params with all options"""
        profile = LLMProfile(
            id="test",
            model="claude-2",
            base_url="https://api.anthropic.com",
            temperature=0.8,
            top_p=0.9,
            max_tokens=2000,
            extra_params={"stop_sequences": ["\n\n"]}
        )
        
        registry = LLMProfileRegistry()
        params = registry.build_llm_client_params(profile)
        
        assert params["model"] == "claude-2"
        assert params["base_url"] == "https://api.anthropic.com"
        assert params["temperature"] == 0.8
        assert params["top_p"] == 0.9
        assert params["max_tokens"] == 2000
        assert params["stop_sequences"] == ["\n\n"]
    
    def test_from_config_with_profiles(self):
        """Test creating registry from config with profiles"""
        llm_config = {
            "default_model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
        
        llm_profiles = [
            {
                "id": "gpt3",
                "model": "gpt-3.5-turbo"
            },
            {
                "id": "gpt4",
                "model": "gpt-4"
            }
        ]
        
        registry = LLMProfileRegistry.from_config(llm_config, llm_profiles)
        
        assert registry.has_profile("gpt3")
        assert registry.has_profile("gpt4")
    
    def test_from_config_backward_compatibility(self):
        """Test creating registry from legacy config without profiles"""
        llm_config = {
            "default_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        registry = LLMProfileRegistry.from_config(llm_config, None)
        
        # Should create a default profile
        assert registry.has_profile("default")
        
        default_profile = registry.get_profile("default")
        assert default_profile.model == "gpt-3.5-turbo"
        assert default_profile.temperature == 0.7
        assert default_profile.max_tokens == 1000
    
    def test_from_config_empty(self):
        """Test creating registry from empty config"""
        registry = LLMProfileRegistry.from_config({}, None)
        
        # Should create a default profile with defaults
        assert registry.has_profile("default")
        
        default_profile = registry.get_profile("default")
        assert default_profile.model == "gpt-3.5-turbo"
        assert default_profile.temperature == 0.7
