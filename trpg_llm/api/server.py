"""FastAPI server implementation"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, Tuple
import uuid

from ..core.game_engine import GameEngine
from ..models.game_state import GameConfig
from ..models.dice import DiceRoll
from ..models.event import StateDiff
from ..core.chat_pipeline import ChatPipeline
from ..core.builtin_tools import create_builtin_tools_registry
from ..llm.agent_manager import AIAgentManager
from ..core.auto_progression import (
    AutoProgressionManager,
    AutoProgressionConfig,
    ProgressionState,
)
from .schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    ActionRequest,
    ActionResponse,
    DiceRollRequest,
    DiceRollResponse,
    StateUpdateRequest,
    MessageRequest,
    RollbackRequest,
    ChatRequest,
    ChatResponse,
    RedrawMessageRequest,
    EditEventRequest,
    EditEventResponse,
    SetCharacterProfileRequest,
    AutoProgressionConfigRequest,
    AutoProgressionStatusResponse,
    AutoProgressionConfigResponse,
    AutoProgressResponse,
    ProgressionErrorResponse,
)


# Global storage for game sessions (in production, use database)
GAME_SESSIONS: Dict[str, GameEngine] = {}
CHAT_PIPELINES: Dict[str, ChatPipeline] = {}
AGENT_MANAGERS: Dict[str, AIAgentManager] = {}

# Global LLM profile registry (instance-level configuration)
from ..llm.profile import LLMProfileRegistry, LLMProfile
GLOBAL_PROFILE_REGISTRY: Optional[LLMProfileRegistry] = None

# Per-session character profile overrides: {session_id: {character_id: profile_id}}
SESSION_CHARACTER_PROFILES: Dict[str, Dict[str, str]] = {}

# Per-session auto-progression managers
AUTO_PROGRESSION_MANAGERS: Dict[str, AutoProgressionManager] = {}


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="TRPG-LLM API",
        description="Configuration-driven TRPG framework with LLM integration",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """Health check endpoint"""
        return {
            "name": "TRPG-LLM API",
            "version": "0.1.0",
            "status": "running",
        }
    
    # ===== Global LLM Profile Management =====
    
    @app.get("/api/v1/profiles")
    async def list_profiles():
        """List all global LLM profiles"""
        global GLOBAL_PROFILE_REGISTRY
        if GLOBAL_PROFILE_REGISTRY is None:
            return {"profiles": []}
        
        profiles = []
        for profile_id in GLOBAL_PROFILE_REGISTRY.list_profiles():
            profile = GLOBAL_PROFILE_REGISTRY.get_profile(profile_id)
            if profile:
                profiles.append(profile.dict())
        
        return {"profiles": profiles}
    
    @app.post("/api/v1/profiles")
    async def set_profiles(profiles: list):
        """Set global LLM profiles (replaces all existing profiles)"""
        global GLOBAL_PROFILE_REGISTRY
        GLOBAL_PROFILE_REGISTRY = LLMProfileRegistry(profiles)
        return {"message": "Profiles updated", "count": len(profiles)}
    
    @app.post("/api/v1/profiles/add")
    async def add_profile(profile: dict):
        """Add a single profile to the global registry"""
        global GLOBAL_PROFILE_REGISTRY
        profile_id = profile.get('id')
        
        # Validate profile ID exists
        if not profile_id:
            raise HTTPException(status_code=400, detail="Profile must have an 'id' field")
        
        # Check for duplicate
        if GLOBAL_PROFILE_REGISTRY and profile_id in GLOBAL_PROFILE_REGISTRY.profiles:
            raise HTTPException(status_code=409, detail=f"Profile '{profile_id}' already exists. Use PUT to update.")
        
        if GLOBAL_PROFILE_REGISTRY is None:
            GLOBAL_PROFILE_REGISTRY = LLMProfileRegistry([profile])
        else:
            new_profile = LLMProfile(**profile)
            GLOBAL_PROFILE_REGISTRY.profiles[new_profile.id] = new_profile
        return {"message": f"Profile '{profile_id}' added"}
    
    @app.delete("/api/v1/profiles/{profile_id}")
    async def delete_profile(profile_id: str):
        """Delete a profile from the global registry"""
        global GLOBAL_PROFILE_REGISTRY
        if GLOBAL_PROFILE_REGISTRY and profile_id in GLOBAL_PROFILE_REGISTRY.profiles:
            del GLOBAL_PROFILE_REGISTRY.profiles[profile_id]
            return {"message": f"Profile '{profile_id}' deleted"}
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # ===== Session Character Profile Overrides =====
    
    @app.get("/sessions/{session_id}/character-profiles")
    async def get_session_character_profiles(session_id: str):
        """Get character profile overrides for a session"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"session_id": session_id, "character_profiles": SESSION_CHARACTER_PROFILES.get(session_id, {})}
    
    @app.put("/sessions/{session_id}/character-profiles/{character_id}")
    async def set_character_profile(session_id: str, character_id: str, request: SetCharacterProfileRequest):
        """Set or update the default profile for a character in a session"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate profile exists in global registry
        if GLOBAL_PROFILE_REGISTRY is None or not GLOBAL_PROFILE_REGISTRY.has_profile(request.profile_id):
            raise HTTPException(
                status_code=400, 
                detail=f"Profile '{request.profile_id}' not found. Please add it to the global registry first."
            )
        
        # Initialize session character profiles if not exists
        if session_id not in SESSION_CHARACTER_PROFILES:
            SESSION_CHARACTER_PROFILES[session_id] = {}
        
        SESSION_CHARACTER_PROFILES[session_id][character_id] = request.profile_id
        return {
            "message": f"Character '{character_id}' profile set to '{request.profile_id}'",
            "session_id": session_id,
            "character_id": character_id,
            "profile_id": request.profile_id
        }
    
    @app.delete("/sessions/{session_id}/character-profiles/{character_id}")
    async def reset_character_profile(session_id: str, character_id: str):
        """Reset a character's profile to use the game preset default"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id in SESSION_CHARACTER_PROFILES and character_id in SESSION_CHARACTER_PROFILES[session_id]:
            del SESSION_CHARACTER_PROFILES[session_id][character_id]
            return {"message": f"Character '{character_id}' profile reset to default"}
        
        return {"message": f"Character '{character_id}' was already using default profile"}
    
    @app.post("/sessions", response_model=CreateSessionResponse)
    async def create_session(request: CreateSessionRequest):
        """Create a new game session"""
        try:
            # Create game engine
            session_id = str(uuid.uuid4())
            config = GameConfig(**request.config)
            engine = GameEngine(config, session_id)
            
            # Create AI agent manager with global profile registry
            agent_manager = AIAgentManager(config, global_profile_registry=GLOBAL_PROFILE_REGISTRY)
            
            # Create tool registry and chat pipeline
            tool_registry = create_builtin_tools_registry()
            chat_pipeline = ChatPipeline(engine, tool_registry, agent_manager)
            
            # Store session
            GAME_SESSIONS[session_id] = engine
            AGENT_MANAGERS[session_id] = agent_manager
            CHAT_PIPELINES[session_id] = chat_pipeline
            
            # Initialize session character profiles (empty - use game preset defaults)
            SESSION_CHARACTER_PROFILES[session_id] = {}
            
            # Initialize auto-progression manager
            auto_config_dict = config.auto_progression or {}
            auto_config = AutoProgressionConfig(
                enabled=auto_config_dict.get("enabled", False),
                turn_order=auto_config_dict.get("turn_order", config.workflow.get("turn_order", [])),
                stop_before_human=auto_config_dict.get("stop_before_human", True),
                continue_after_human=auto_config_dict.get("continue_after_human", True),
            )
            AUTO_PROGRESSION_MANAGERS[session_id] = AutoProgressionManager(
                characters=config.characters,
                config=auto_config
            )
            
            # Get initial state
            state = engine.get_state()
            
            return CreateSessionResponse(
                session_id=session_id,
                state=state.dict(),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get game session state"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        engine = GAME_SESSIONS[session_id]
        state = engine.get_state()
        
        return {"session_id": session_id, "state": state.dict()}
    
    @app.get("/sessions/{session_id}/history")
    async def get_history(session_id: str):
        """Get event history for a session"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        engine = GAME_SESSIONS[session_id]
        events = engine.get_event_history()
        
        return {
            "session_id": session_id,
            "events": [event.dict() for event in events],
        }
    
    @app.post("/sessions/{session_id}/actions", response_model=ActionResponse)
    async def perform_action(session_id: str, request: ActionRequest):
        """Perform a game action"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            # Convert state_diffs if provided
            state_diffs = None
            if request.state_diffs:
                state_diffs = [StateDiff(**diff) for diff in request.state_diffs]
            
            # Perform action
            state = engine.perform_action(
                actor_id=request.actor_id,
                action_type=request.action_type,
                data=request.data,
                state_diffs=state_diffs,
            )
            
            return ActionResponse(
                session_id=session_id,
                state=state.dict(),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/dice", response_model=DiceRollResponse)
    async def roll_dice(session_id: str, request: DiceRollRequest):
        """Roll dice"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            # Create dice roll
            dice_roll = DiceRoll(**request.dict())
            
            # Execute roll
            state = engine.roll_dice(dice_roll)
            
            # Get the result from the last event
            last_event = engine.get_event_history()[-1]
            result = last_event.data.get("result", {})
            
            return DiceRollResponse(
                session_id=session_id,
                result=result,
                state=state.dict(),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/state")
    async def update_state(session_id: str, request: StateUpdateRequest):
        """Update game state"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            state = engine.update_state(
                actor_id=request.actor_id,
                path=request.path,
                operation=request.operation,
                value=request.value,
            )
            
            return {"session_id": session_id, "state": state.dict()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/messages")
    async def add_message(session_id: str, request: MessageRequest):
        """Add a message to the game"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            state = engine.add_message(
                sender_id=request.sender_id,
                content=request.content,
                message_type=request.message_type,
                metadata=request.metadata,
            )
            
            return {"session_id": session_id, "state": state.dict()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/rollback")
    async def rollback(session_id: str, request: RollbackRequest):
        """Rollback game state to a specific event or timestamp"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            if request.event_id:
                state = engine.rollback_to_event(request.event_id)
            elif request.timestamp:
                state = engine.rollback_to_timestamp(request.timestamp)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either event_id or timestamp must be provided"
                )
            
            return {"session_id": session_id, "state": state.dict()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.delete("/sessions/{session_id}")
    async def delete_session(session_id: str):
        """Delete a game session"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        del GAME_SESSIONS[session_id]
        if session_id in CHAT_PIPELINES:
            del CHAT_PIPELINES[session_id]
        if session_id in AGENT_MANAGERS:
            del AGENT_MANAGERS[session_id]
        if session_id in SESSION_CHARACTER_PROFILES:
            del SESSION_CHARACTER_PROFILES[session_id]
        if session_id in AUTO_PROGRESSION_MANAGERS:
            del AUTO_PROGRESSION_MANAGERS[session_id]
        
        return {"message": "Session deleted", "session_id": session_id}
    
    @app.post("/api/v1/sessions/{session_id}/chat", response_model=ChatResponse)
    async def chat(session_id: str, request: ChatRequest):
        """
        Process a chat message through the full pipeline.
        Supports both human and AI characters.
        """
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            pipeline = CHAT_PIPELINES[session_id]
            
            # Determine which profile to use:
            # 1. Request-level override (highest priority)
            # 2. Session-level character override
            # 3. Game preset default (handled by pipeline)
            profile_id = request.llm_profile_id
            if not profile_id:
                session_profiles = SESSION_CHARACTER_PROFILES.get(session_id, {})
                profile_id = session_profiles.get(request.role_id)
            
            result = await pipeline.process_chat(
                role_id=request.role_id,
                message=request.message,
                template=request.template,
                max_tool_iterations=request.max_tool_iterations,
                llm_profile_id=profile_id
            )
            
            return ChatResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/redraw")
    async def redraw_message(session_id: str, request: RedrawMessageRequest):
        """
        Redraw (regenerate) the last message from an AI character.
        Rolls back to before the message and regenerates it.
        """
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            pipeline = CHAT_PIPELINES[session_id]
            
            # Determine which profile to use:
            # 1. Request-level override (highest priority)
            # 2. Try to get from last message metadata
            # 3. Session-level character override
            # 4. Game preset default (handled by pipeline)
            profile_id_to_use = request.llm_profile_id
            if not profile_id_to_use:
                # Try to get from last message metadata
                events = engine.get_event_history()
                for event in reversed(events):
                    if event.event_type.value == "MESSAGE" and event.actor_id == request.character_id:
                        if event.metadata and "used_profile_id" in event.metadata:
                            profile_id_to_use = event.metadata["used_profile_id"]
                        break
            
            if not profile_id_to_use:
                # Fallback to session character profile override
                session_profiles = SESSION_CHARACTER_PROFILES.get(session_id, {})
                profile_id_to_use = session_profiles.get(request.character_id)
            
            # Rollback to before the last message
            state = engine.redraw_last_ai_message(request.character_id)
            
            # Regenerate the message
            result = await pipeline.process_chat(
                role_id=request.character_id,
                message=None,
                template=request.template,
                llm_profile_id=profile_id_to_use
            )
            
            return ChatResponse(**result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/sessions/{session_id}/events/{event_id}/edit", response_model=EditEventResponse)
    async def edit_event(session_id: str, event_id: str, request: EditEventRequest):
        """
        Edit an event's data or state_diffs.
        After editing, recomputes the current state.
        """
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            engine = GAME_SESSIONS[session_id]
            
            # Convert state diffs if provided
            new_state_diffs = None
            if request.new_state_diffs:
                new_state_diffs = [StateDiff(**diff) for diff in request.new_state_diffs]
            
            # Edit the event
            new_state = engine.edit_event(
                event_id=event_id,
                new_data=request.new_data,
                new_state_diffs=new_state_diffs
            )
            
            return EditEventResponse(
                session_id=session_id,
                event_id=event_id,
                current_state=new_state.dict()
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ===== Auto-Progression Endpoints =====
    
    def _convert_progression_status(status) -> AutoProgressionStatusResponse:
        """Convert internal progression status to API response"""
        error_response = None
        if status.error:
            error_response = ProgressionErrorResponse(
                character_id=status.error.character_id,
                error_message=status.error.error_message,
                position_in_queue=status.error.position_in_queue
            )
        
        return AutoProgressionStatusResponse(
            state=status.state.value,
            current_position=status.current_position,
            queue=status.queue,
            completed=status.completed,
            error=error_response,
            last_speaker_id=status.last_speaker_id
        )
    
    @app.get("/sessions/{session_id}/auto-progress/config", response_model=AutoProgressionConfigResponse)
    async def get_auto_progression_config(session_id: str):
        """Get auto-progression configuration for a session"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        config = manager.config
        
        return AutoProgressionConfigResponse(
            session_id=session_id,
            enabled=config.enabled,
            turn_order=config.turn_order,
            stop_before_human=config.stop_before_human,
            continue_after_human=config.continue_after_human
        )
    
    @app.put("/sessions/{session_id}/auto-progress/config", response_model=AutoProgressionConfigResponse)
    async def update_auto_progression_config(session_id: str, request: AutoProgressionConfigRequest):
        """Update auto-progression configuration"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        
        # Update only provided fields
        if request.enabled is not None:
            manager.set_enabled(request.enabled)
        if request.turn_order is not None:
            manager.update_turn_order(request.turn_order)
        if request.stop_before_human is not None:
            manager.config.stop_before_human = request.stop_before_human
        if request.continue_after_human is not None:
            manager.config.continue_after_human = request.continue_after_human
        
        config = manager.config
        return AutoProgressionConfigResponse(
            session_id=session_id,
            enabled=config.enabled,
            turn_order=config.turn_order,
            stop_before_human=config.stop_before_human,
            continue_after_human=config.continue_after_human
        )
    
    @app.get("/sessions/{session_id}/auto-progress/status", response_model=AutoProgressionStatusResponse)
    async def get_auto_progression_status(session_id: str):
        """Get current auto-progression status"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        status = manager.get_status()
        
        return _convert_progression_status(status)
    
    @app.post("/sessions/{session_id}/auto-progress", response_model=AutoProgressResponse)
    async def run_auto_progression(session_id: str, from_character_id: Optional[str] = None):
        """
        Run auto-progression for AI characters.
        
        This will process all queued AI characters in sequence until:
        - A human character's turn is reached
        - An error occurs
        - All characters in the queue have completed
        
        Args:
            from_character_id: Start progression after this character (usually the human who just spoke)
        """
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        pipeline = CHAT_PIPELINES[session_id]
        
        # Start progression
        status = manager.start_progression(from_character_id)
        
        messages: list = []
        stopped_reason = None
        
        # Process characters in sequence
        while status.state == ProgressionState.PROGRESSING:
            next_char = manager.get_next_character()
            if not next_char:
                stopped_reason = "completed"
                break
            
            # Determine profile to use
            session_profiles = SESSION_CHARACTER_PROFILES.get(session_id, {})
            profile_id = session_profiles.get(next_char)
            
            try:
                # Process chat for this character
                result = await pipeline.process_chat(
                    role_id=next_char,
                    message=None,  # AI generates its own message
                    llm_profile_id=profile_id
                )
                
                # Check for errors in result
                if result.get("error"):
                    manager.mark_error(next_char, result["error"])
                    stopped_reason = "error"
                    break
                
                # Mark as completed and add to messages
                manager.mark_completed(next_char)
                messages.append(ChatResponse(**result))
                
            except Exception as e:
                manager.mark_error(next_char, str(e))
                stopped_reason = "error"
                break
            
            # Update status for next iteration
            status = manager.get_status()
        
        # Determine final stopped reason
        if not stopped_reason:
            if status.state == ProgressionState.WAITING_FOR_USER:
                stopped_reason = "human_turn"
            elif status.state == ProgressionState.PAUSED:
                stopped_reason = "paused"
            elif status.state == ProgressionState.ERROR:
                stopped_reason = "error"
            else:
                stopped_reason = "completed"
        
        return AutoProgressResponse(
            session_id=session_id,
            status=_convert_progression_status(status),
            messages=messages,
            stopped_reason=stopped_reason
        )
    
    @app.post("/sessions/{session_id}/auto-progress/retry", response_model=AutoProgressResponse)
    async def retry_auto_progression(session_id: str):
        """Retry auto-progression from the error point"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        
        # Reset error state and retry
        manager.retry_from_error()
        
        # Re-run progression
        return await run_auto_progression(session_id)
    
    @app.post("/sessions/{session_id}/auto-progress/skip", response_model=AutoProgressionStatusResponse)
    async def skip_current_character(session_id: str):
        """Skip the current character in the progression queue"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        status = manager.skip_current()
        
        return _convert_progression_status(status)
    
    @app.post("/sessions/{session_id}/auto-progress/pause", response_model=AutoProgressionStatusResponse)
    async def pause_auto_progression(session_id: str):
        """Pause auto-progression"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        status = manager.pause()
        
        return _convert_progression_status(status)
    
    @app.post("/sessions/{session_id}/auto-progress/resume", response_model=AutoProgressResponse)
    async def resume_auto_progression(session_id: str):
        """Resume auto-progression from paused state"""
        if session_id not in GAME_SESSIONS:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_id not in AUTO_PROGRESSION_MANAGERS:
            raise HTTPException(status_code=404, detail="Auto-progression manager not found")
        
        manager = AUTO_PROGRESSION_MANAGERS[session_id]
        manager.resume()
        
        # Continue progression
        return await run_auto_progression(session_id)
    
    return app
