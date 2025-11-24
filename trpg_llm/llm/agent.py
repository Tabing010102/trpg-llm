"""AI Agent for controlling characters"""

from enum import Enum
from typing import Dict, Any, List, Optional

from ..models.character import Character
from ..models.game_state import GameState
from .llm_client import LLMClient


class AgentType(str, Enum):
    """Type of AI agent"""
    GM = "gm"  # Game Master
    PLAYER = "player"  # Player character
    NPC = "npc"  # Non-player character


class AIAgent:
    """
    AI Agent that controls a character using LLM.
    Can be GM, Player, or NPC.
    """
    
    def __init__(
        self,
        character: Character,
        agent_type: AgentType,
        llm_client: LLMClient,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        self.character = character
        self.agent_type = agent_type
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.tools = tools or []
        self.message_history: List[Dict[str, str]] = []
    
    def _default_system_prompt(self) -> str:
        """Generate default system prompt based on agent type"""
        if self.agent_type == AgentType.GM:
            return (
                f"You are the Game Master for a TRPG session. "
                f"Your role is to narrate the story, control NPCs, and facilitate gameplay. "
                f"Be creative, fair, and engaging."
            )
        elif self.agent_type == AgentType.PLAYER:
            return (
                f"You are playing as {self.character.name} in a TRPG session. "
                f"Character description: {self.character.description or 'N/A'}\n"
                f"Character background: {self.character.background or 'N/A'}\n"
                f"Make decisions based on your character's personality and goals."
            )
        else:  # NPC
            return (
                f"You are playing as {self.character.name}, an NPC in a TRPG session. "
                f"Character description: {self.character.description or 'N/A'}\n"
                f"Stay in character and respond naturally to the situation."
            )
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history"""
        self.message_history.append({
            "role": role,
            "content": content,
        })
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.message_history = []
    
    def build_context(self, game_state: GameState) -> str:
        """Build context string from game state"""
        context_parts = [
            f"Current Turn: {game_state.current_turn}",
            f"Current Phase: {game_state.current_phase or 'N/A'}",
        ]
        
        # Add character states
        if game_state.characters:
            context_parts.append("\nCharacters:")
            for char_id, char in game_state.characters.items():
                context_parts.append(
                    f"  - {char.name} ({char.type.value}): {char.state}"
                )
        
        # Add recent messages
        if game_state.messages:
            context_parts.append("\nRecent events:")
            for msg in game_state.messages[-5:]:  # Last 5 messages
                sender = msg.get("sender_id", "Unknown")
                content = msg.get("content", "")
                context_parts.append(f"  - {sender}: {content}")
        
        return "\n".join(context_parts)
    
    async def get_response(
        self,
        game_state: GameState,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get AI response for the current game state.
        """
        # Build context
        context = self.build_context(game_state)
        if additional_context:
            context += f"\n\n{additional_context}"
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]
        
        # Add conversation history
        messages.extend(self.message_history)
        
        # Get completion
        response = await self.llm_client.complete(
            messages=messages,
            tools=self.tools if self.tools else None,
        )
        
        # Add assistant response to history if successful
        if response.get("content"):
            self.add_message("assistant", response["content"])
        
        return response
    
    def get_response_sync(
        self,
        game_state: GameState,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous version of get_response.
        """
        # Build context
        context = self.build_context(game_state)
        if additional_context:
            context += f"\n\n{additional_context}"
        
        # Prepare messages
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]
        
        # Add conversation history
        messages.extend(self.message_history)
        
        # Get completion
        response = self.llm_client.complete_sync(
            messages=messages,
            tools=self.tools if self.tools else None,
        )
        
        # Add assistant response to history if successful
        if response.get("content"):
            self.add_message("assistant", response["content"])
        
        return response
