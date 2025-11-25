"""AI Agent Manager for managing multiple AI-controlled characters"""

from typing import Dict, Optional, List
from ..models.character import Character, CharacterControlType
from ..models.game_state import GameConfig
from .agent import AIAgent, AgentType
from .llm_client import LLMClient
from .profile import LLMProfileRegistry


class AIAgentManager:
    """
    Manages all AI agents in a game session.
    Auto-creates agents for AI-controlled characters.
    """
    
    def __init__(self, config: GameConfig, global_profile_registry: Optional[LLMProfileRegistry] = None):
        self.config = config
        self.agents: Dict[str, AIAgent] = {}
        
        # Use global profile registry if provided, otherwise create from config
        if global_profile_registry is not None:
            self.profile_registry = global_profile_registry
        else:
            # Fallback to creating registry from config (for backward compatibility)
            self.profile_registry = LLMProfileRegistry.from_config(
                llm_config=config.llm_config,
                llm_profiles=config.llm_profiles
            )
        
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize AI agents for all AI-controlled characters"""
        for char_id, char_data in self.config.characters.items():
            # Convert to Character if dict
            if isinstance(char_data, dict):
                character = Character(**char_data)
            else:
                character = char_data
            
            # Only create agents for AI-controlled characters
            if character.control == CharacterControlType.AI:
                self._create_agent(character)
    
    def _create_agent(self, character: Character) -> AIAgent:
        """Create an AI agent for a character"""
        # Determine agent type
        agent_type_map = {
            "gm": AgentType.GM,
            "player": AgentType.PLAYER,
            "npc": AgentType.NPC,
        }
        char_type = character.type.value if hasattr(character.type, 'value') else character.type
        agent_type = agent_type_map.get(char_type, AgentType.NPC)
        
        # Get AI config
        ai_config = character.ai_config or {}
        
        # Determine which profile to use
        profile_id = ai_config.get("profile_id")
        if not profile_id:
            # Fallback to default_profile_id from llm_config
            profile_id = self.config.llm_config.get("default_profile_id", "default")
        
        # Get profile and create LLM client
        profile = self.profile_registry.get_profile(profile_id)
        if profile:
            # Use profile to configure LLM client
            client_params = self.profile_registry.build_llm_client_params(profile)
            llm_client = LLMClient(**client_params)
        else:
            # Fallback to legacy configuration if profile not found
            model = ai_config.get("model", self.config.llm_config.get("default_model", "gpt-3.5-turbo"))
            temperature = ai_config.get("temperature", self.config.llm_config.get("temperature", 0.7))
            llm_client = LLMClient(
                model=model,
                api_key=ai_config.get("api_key"),
                base_url=ai_config.get("base_url"),
                temperature=temperature
            )
        
        # Get system prompt
        system_prompt = self._get_system_prompt(character, agent_type)
        
        # Get tools
        tools = self._format_tools_for_agent()
        
        # Create agent
        agent = AIAgent(
            character=character,
            agent_type=agent_type,
            llm_client=llm_client,
            system_prompt=system_prompt,
            tools=tools
        )
        
        self.agents[character.id] = agent
        return agent
    
    def _get_system_prompt(self, character: Character, agent_type: AgentType) -> str:
        """Get system prompt for agent from config or defaults"""
        prompts = self.config.llm_config.get("prompts", {})
        
        # Check for character-specific prompt
        if character.ai_config and "system_prompt" in character.ai_config:
            return character.ai_config["system_prompt"]
        
        # Use type-specific prompt
        if agent_type == AgentType.GM:
            return prompts.get("gm_system") or self._default_gm_prompt()
        elif agent_type == AgentType.PLAYER:
            return prompts.get("player_system") or self._default_player_prompt(character)
        else:
            return prompts.get("npc_system") or self._default_npc_prompt(character)
    
    def _default_gm_prompt(self) -> str:
        """Default GM prompt"""
        return (
            f"You are the Game Master for '{self.config.name}' using {self.config.rule_system} rules. "
            f"{self.config.description or ''}\n"
            f"Create an engaging narrative, control NPCs, and facilitate gameplay. "
            f"Be creative, fair, and responsive to player actions."
        )
    
    def _default_player_prompt(self, character: Character) -> str:
        """Default player character prompt"""
        return (
            f"You are playing as {character.name} in '{self.config.name}'. "
            f"Character description: {character.description or 'N/A'}\n"
            f"Make decisions that align with your character's personality and goals. "
            f"Engage with the story and other characters meaningfully."
        )
    
    def _default_npc_prompt(self, character: Character) -> str:
        """Default NPC prompt"""
        return (
            f"You are {character.name}, an NPC in '{self.config.name}'. "
            f"Character description: {character.description or 'N/A'}\n"
            f"Stay in character and respond naturally to interactions."
        )
    
    def _format_tools_for_agent(self) -> List[Dict]:
        """Format tools from config for LLM function calling"""
        if not self.config.tools:
            return []
        
        formatted_tools = []
        for tool in self.config.tools:
            # Convert to OpenAI function calling format if needed
            if "type" not in tool:
                formatted_tools.append({
                    "type": "function",
                    "function": tool
                })
            else:
                formatted_tools.append(tool)
        
        return formatted_tools
    
    def get_agent(self, character_id: str) -> Optional[AIAgent]:
        """Get an AI agent by character ID"""
        return self.agents.get(character_id)
    
    def has_agent(self, character_id: str) -> bool:
        """Check if a character has an AI agent"""
        return character_id in self.agents
    
    def list_agents(self) -> List[str]:
        """List all agent IDs"""
        return list(self.agents.keys())
    
    def add_message_to_agent(self, character_id: str, role: str, content: str) -> None:
        """Add a message to an agent's history"""
        agent = self.get_agent(character_id)
        if agent:
            agent.add_message(role, content)
    
    def clear_agent_history(self, character_id: str) -> None:
        """Clear an agent's conversation history"""
        agent = self.get_agent(character_id)
        if agent:
            agent.clear_history()
    
    def clear_all_histories(self) -> None:
        """Clear all agents' conversation histories"""
        for agent in self.agents.values():
            agent.clear_history()
    
    def create_llm_client_from_profile(self, profile_id: str) -> Optional[LLMClient]:
        """
        Create an LLM client from a profile ID.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            LLMClient instance or None if profile not found
        """
        profile = self.profile_registry.get_profile(profile_id)
        if not profile:
            return None
        
        client_params = self.profile_registry.build_llm_client_params(profile)
        return LLMClient(**client_params)
