"""Chat message pipeline for processing user input through LLM and tools"""

from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime, timezone

from ..models.game_state import GameState
from ..models.event import StateDiff
from .prompt_renderer import PromptRenderer
from .tool_executor import ToolExecutor, ToolRegistry
from .game_engine import GameEngine
from ..llm.llm_client import LLMClient
from ..llm.agent_manager import AIAgentManager


class ChatPipeline:
    """
    Manages the complete chat message pipeline:
    User Input → State Hydrate → Prompt Render → LLM Call → Tool Execution → State Update
    """
    
    def __init__(
        self,
        game_engine: GameEngine,
        tool_registry: ToolRegistry,
        agent_manager: Optional[AIAgentManager] = None
    ):
        self.game_engine = game_engine
        self.tool_registry = tool_registry
        self.tool_executor = ToolExecutor(tool_registry)
        self.prompt_renderer = PromptRenderer()
        self.agent_manager = agent_manager
    
    def _normalize_state_diffs(self, state_diffs: List) -> List[Dict[str, Any]]:
        """Normalize state_diffs to dict format"""
        return [diff.dict() if isinstance(diff, StateDiff) else diff for diff in state_diffs]
    
    def _get_agent_profile_id(self, role_id: str) -> Optional[str]:
        """
        Get the profile ID for an agent.
        
        Args:
            role_id: Character ID
            
        Returns:
            Profile ID or None
        """
        if not self.agent_manager:
            return None
        
        # Try to get from character's ai_config
        game_state = self.game_engine.get_state()
        character = game_state.characters.get(role_id)
        if character and hasattr(character, 'ai_config') and character.ai_config:
            profile_id = character.ai_config.get("profile_id")
            if profile_id:
                return profile_id
        
        # Fallback to default from llm_config
        config = self.agent_manager.config
        return config.llm_config.get("default_profile_id", "default")
    
    async def process_chat(
        self,
        role_id: str,
        message: Optional[str] = None,
        template: Optional[str] = None,
        max_tool_iterations: int = 3,
        llm_profile_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message through the complete pipeline.
        
        Args:
            role_id: Character ID sending/generating the message
            message: User message (for human characters) or context for AI
            template: Optional Jinja2 template for prompt rendering
            max_tool_iterations: Maximum number of tool calling iterations
            llm_profile_id: Optional LLM profile ID to use for this request
        
        Returns:
            Dict with content, state_diffs, current_state, tool_calls, used_profile_id
        """
        # Get current game state
        game_state = self.game_engine.get_state()
        
        # Check if this is an AI character
        is_ai = self.agent_manager and self.agent_manager.has_agent(role_id)
        
        if is_ai:
            return await self._process_ai_chat(
                role_id, message, template, max_tool_iterations, game_state, llm_profile_id
            )
        else:
            return await self._process_human_chat(
                role_id, message, game_state
            )
    
    async def _process_human_chat(
        self,
        role_id: str,
        message: str,
        game_state: GameState
    ) -> Dict[str, Any]:
        """Process message from human character"""
        # Simply add message to game
        new_state = self.game_engine.add_message(
            sender_id=role_id,
            content=message,
            message_type="text"
        )
        
        return {
            "content": message,
            "state_diffs": [],
            "current_state": new_state.dict(),
            "tool_calls": [],
            "role_id": role_id,
            "is_ai": False
        }
    
    async def _process_ai_chat(
        self,
        role_id: str,
        message: Optional[str],
        template: Optional[str],
        max_tool_iterations: int,
        game_state: GameState,
        llm_profile_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process message from AI character"""
        agent = self.agent_manager.get_agent(role_id)
        if not agent:
            raise ValueError(f"No AI agent found for character {role_id}")
        
        # Track which profile is being used
        used_profile_id = None
        original_llm_client = agent.llm_client
        
        # If a specific profile is requested, temporarily switch the agent's LLM client
        if llm_profile_id:
            temp_client = self.agent_manager.create_llm_client_from_profile(llm_profile_id)
            if temp_client:
                agent.llm_client = temp_client
                used_profile_id = llm_profile_id
            else:
                # Profile not found, keep using default
                used_profile_id = self._get_agent_profile_id(role_id)
        else:
            used_profile_id = self._get_agent_profile_id(role_id)
        
        try:
            # Build context for AI
            context_message = message or "Continue the game."
            
            # Use template if provided, otherwise use agent's default
            if template:
                prompt = self.prompt_renderer.render_with_game_state(
                    template, game_state, {"user_message": context_message}
                )
            else:
                prompt = context_message
            
            # Track all state diffs and tool calls
            all_state_diffs = []
            all_tool_calls = []
            final_content = None
            
            # Prepare context for tool execution
            tool_context = {
                "game_engine": self.game_engine,
                "game_state": game_state,
                "role_id": role_id
            }
            
            # Initial LLM call
            response = await agent.get_response(game_state, prompt)
            
            # Iterate through tool calling loop
            for iteration in range(max_tool_iterations):
                if response.get("error"):
                    break
                
                # Check if there are tool calls
                tool_calls = response.get("tool_calls", [])
                
                if not tool_calls:
                    # No more tool calls, we're done
                    final_content = response.get("content")
                    break
                
                # Execute tool calls
                tool_results = self.tool_executor.execute_tool_calls(tool_calls, tool_context)
                all_tool_calls.extend(tool_calls)
                
                # Collect state diffs from tool results
                for result in tool_results:
                    if result.get("state_diffs"):
                        all_state_diffs.extend(result["state_diffs"])
                
                # Format results for LLM
                tool_messages = self.tool_executor.format_tool_results_for_llm(tool_results)
                
                # Add tool call message to agent history
                agent.add_message("assistant", json.dumps(tool_calls))
                for tool_msg in tool_messages:
                    agent.add_message("tool", tool_msg["content"])
                
                # Call LLM again with tool results
                response = await agent.get_response(game_state, "Continue based on tool results.")
        
            # If we got content, save it as a message
            if final_content:
                # Get profile info for metadata
                profile = self.agent_manager.profile_registry.get_profile(used_profile_id) if used_profile_id else None
                profile_metadata = {}
                if profile:
                    profile_metadata = {
                        "used_profile_id": used_profile_id,
                        "provider_type": profile.provider_type.value,
                        "model": profile.model
                    }
                
                new_state = self.game_engine.add_message(
                    sender_id=role_id,
                    content=final_content,
                    message_type="text",
                    metadata={
                        "tool_calls": all_tool_calls,
                        "iterations": iteration + 1,
                        **profile_metadata
                    }
                )
                
                # Get last event to extract any state_diffs
                last_event = self.game_engine.get_event_history()[-1]
                event_diffs = [diff.dict() for diff in last_event.state_diffs]
                
                return {
                    "content": final_content,
                    "state_diffs": event_diffs + self._normalize_state_diffs(all_state_diffs),
                    "current_state": new_state.dict(),
                    "tool_calls": all_tool_calls,
                    "role_id": role_id,
                    "is_ai": True,
                    "used_profile_id": used_profile_id
                }
            else:
                # No content generated, just return state
                return {
                    "content": None,
                    "state_diffs": self._normalize_state_diffs(all_state_diffs),
                    "current_state": game_state.dict(),
                    "tool_calls": all_tool_calls,
                    "role_id": role_id,
                    "is_ai": True,
                    "error": response.get("error"),
                    "used_profile_id": used_profile_id
                }
        finally:
            # Restore original LLM client if we temporarily switched
            if llm_profile_id:
                agent.llm_client = original_llm_client
    
    def process_chat_sync(
        self,
        role_id: str,
        message: Optional[str] = None,
        template: Optional[str] = None,
        max_tool_iterations: int = 3,
        llm_profile_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of process_chat.
        """
        # Get current game state
        game_state = self.game_engine.get_state()
        
        # Check if this is an AI character
        is_ai = self.agent_manager and self.agent_manager.has_agent(role_id)
        
        if is_ai:
            return self._process_ai_chat_sync(
                role_id, message, template, max_tool_iterations, game_state, llm_profile_id
            )
        else:
            # For human, just add message
            new_state = self.game_engine.add_message(
                sender_id=role_id,
                content=message or "",
                message_type="text"
            )
            
            return {
                "content": message,
                "state_diffs": [],
                "current_state": new_state.dict(),
                "tool_calls": [],
                "role_id": role_id,
                "is_ai": False
            }
    
    def _process_ai_chat_sync(
        self,
        role_id: str,
        message: Optional[str],
        template: Optional[str],
        max_tool_iterations: int,
        game_state: GameState,
        llm_profile_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous processing of AI chat"""
        agent = self.agent_manager.get_agent(role_id)
        if not agent:
            raise ValueError(f"No AI agent found for character {role_id}")
        
        # Track which profile is being used
        used_profile_id = None
        original_llm_client = agent.llm_client
        
        # If a specific profile is requested, temporarily switch the agent's LLM client
        if llm_profile_id:
            temp_client = self.agent_manager.create_llm_client_from_profile(llm_profile_id)
            if temp_client:
                agent.llm_client = temp_client
                used_profile_id = llm_profile_id
            else:
                # Profile not found, keep using default
                used_profile_id = self._get_agent_profile_id(role_id)
        else:
            used_profile_id = self._get_agent_profile_id(role_id)
        
        try:
            # Build context for AI
            context_message = message or "Continue the game."
            
            # Use template if provided
            if template:
                prompt = self.prompt_renderer.render_with_game_state(
                    template, game_state, {"user_message": context_message}
                )
            else:
                prompt = context_message
            
            # Track all state diffs and tool calls
            all_state_diffs = []
            all_tool_calls = []
            final_content = None
            
            # Prepare context for tool execution
            tool_context = {
                "game_engine": self.game_engine,
                "game_state": game_state,
                "role_id": role_id
            }
            
            # Initial LLM call
            response = agent.get_response_sync(game_state, prompt)
            
            # Iterate through tool calling loop
            for iteration in range(max_tool_iterations):
                if response.get("error"):
                    break
                
                # Check if there are tool calls
                tool_calls = response.get("tool_calls", [])
                
                if not tool_calls:
                    # No more tool calls, we're done
                    final_content = response.get("content")
                    break
                
                # Execute tool calls
                tool_results = self.tool_executor.execute_tool_calls(tool_calls, tool_context)
                all_tool_calls.extend(tool_calls)
                
                # Collect state diffs from tool results
                for result in tool_results:
                    if result.get("state_diffs"):
                        all_state_diffs.extend(result["state_diffs"])
                
                # Format results for LLM
                tool_messages = self.tool_executor.format_tool_results_for_llm(tool_results)
                
                # Add tool call message to agent history
                agent.add_message("assistant", json.dumps(tool_calls))
                for tool_msg in tool_messages:
                    agent.add_message("tool", tool_msg["content"])
                
                # Call LLM again with tool results
                response = agent.get_response_sync(game_state, "Continue based on tool results.")
        
            # If we got content, save it as a message
            if final_content:
                # Get profile info for metadata
                profile = self.agent_manager.profile_registry.get_profile(used_profile_id) if used_profile_id else None
                profile_metadata = {}
                if profile:
                    profile_metadata = {
                        "used_profile_id": used_profile_id,
                        "provider_type": profile.provider_type.value,
                        "model": profile.model
                    }
                
                new_state = self.game_engine.add_message(
                    sender_id=role_id,
                    content=final_content,
                    message_type="text",
                    metadata={
                        "tool_calls": all_tool_calls,
                        "iterations": iteration + 1,
                        **profile_metadata
                    }
                )
                
                # Get last event to extract any state_diffs
                last_event = self.game_engine.get_event_history()[-1]
                event_diffs = [diff.dict() for diff in last_event.state_diffs]
                
                return {
                    "content": final_content,
                    "state_diffs": event_diffs + self._normalize_state_diffs(all_state_diffs),
                    "current_state": new_state.dict(),
                    "tool_calls": all_tool_calls,
                    "role_id": role_id,
                    "is_ai": True,
                    "used_profile_id": used_profile_id
                }
            else:
                # No content generated, just return state
                return {
                    "content": None,
                    "state_diffs": self._normalize_state_diffs(all_state_diffs),
                    "current_state": game_state.dict(),
                    "tool_calls": all_tool_calls,
                    "role_id": role_id,
                    "is_ai": True,
                    "error": response.get("error"),
                    "used_profile_id": used_profile_id
                }
        finally:
            # Restore original LLM client if we temporarily switched
            if llm_profile_id:
                agent.llm_client = original_llm_client
