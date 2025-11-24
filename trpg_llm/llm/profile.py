"""LLM Profile management for multi-provider support"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Supported LLM provider types"""
    OAI_COMPATIBLE = "oai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL_OPENAI = "local_openai"


class LLMProfile(BaseModel):
    """Configuration profile for an LLM connection"""
    
    id: str = Field(..., description="Unique profile identifier")
    provider_type: ProviderType = Field(
        ProviderType.OAI_COMPATIBLE,
        description="Provider type"
    )
    base_url: Optional[str] = Field(None, description="API base URL")
    api_key_ref: Optional[str] = Field(
        None,
        description="Reference to API key (env var name or config key)"
    )
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(None, description="Nucleus sampling parameter")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    context_window: Optional[int] = Field(
        None,
        description="Context window size"
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific parameters"
    )


class LLMProfileRegistry:
    """Registry for managing LLM profiles"""
    
    def __init__(self, profiles: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize profile registry.
        
        Args:
            profiles: List of profile configurations
        """
        self.profiles: Dict[str, LLMProfile] = {}
        
        if profiles:
            for profile_data in profiles:
                profile = LLMProfile(**profile_data)
                self.profiles[profile.id] = profile
    
    def get_profile(self, profile_id: str) -> Optional[LLMProfile]:
        """Get a profile by ID"""
        return self.profiles.get(profile_id)
    
    def has_profile(self, profile_id: str) -> bool:
        """Check if a profile exists"""
        return profile_id in self.profiles
    
    def list_profiles(self) -> List[str]:
        """List all profile IDs"""
        return list(self.profiles.keys())
    
    def resolve_api_key(self, profile: LLMProfile) -> Optional[str]:
        """
        Resolve API key from reference.
        
        Tries to resolve from:
        1. Environment variable
        2. Returns None if not found (allows for no-auth scenarios)
        
        Args:
            profile: LLM profile with api_key_ref
            
        Returns:
            Resolved API key or None
        """
        if not profile.api_key_ref:
            return None
        
        # Try environment variable
        api_key = os.environ.get(profile.api_key_ref)
        if api_key:
            return api_key
        
        # No key found - could be valid for local models
        return None
    
    def build_llm_client_params(self, profile: LLMProfile) -> Dict[str, Any]:
        """
        Build parameters for LLMClient initialization from a profile.
        
        Args:
            profile: LLM profile
            
        Returns:
            Dict of parameters for LLMClient constructor
        """
        params = {
            "model": profile.model,
            "temperature": profile.temperature,
        }
        
        # Resolve API key
        api_key = self.resolve_api_key(profile)
        if api_key:
            params["api_key"] = api_key
        
        # Add base URL if provided
        if profile.base_url:
            params["base_url"] = profile.base_url
        
        # Add optional parameters
        if profile.top_p is not None:
            params["top_p"] = profile.top_p
        
        if profile.max_tokens is not None:
            params["max_tokens"] = profile.max_tokens
        
        # Merge extra params
        if profile.extra_params:
            params.update(profile.extra_params)
        
        return params
    
    @classmethod
    def from_config(
        cls,
        llm_config: Dict[str, Any],
        llm_profiles: Optional[List[Dict[str, Any]]] = None
    ) -> "LLMProfileRegistry":
        """
        Create registry from config, with backward compatibility.
        
        If no llm_profiles provided, creates a default profile from llm_config.
        
        Args:
            llm_config: Legacy llm_config dict
            llm_profiles: New-style llm_profiles list
            
        Returns:
            LLMProfileRegistry instance
        """
        if llm_profiles:
            return cls(llm_profiles)
        
        # Backward compatibility: create default profile from llm_config
        default_profile = {
            "id": "default",
            "provider_type": "oai_compatible",
            "model": llm_config.get("default_model", "gpt-3.5-turbo"),
            "temperature": llm_config.get("temperature", 0.7),
            "max_tokens": llm_config.get("max_tokens"),
        }
        
        # Check for API key in common env vars
        if "OPENAI_API_KEY" in os.environ:
            default_profile["api_key_ref"] = "OPENAI_API_KEY"
        
        return cls([default_profile])
