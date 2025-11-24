"""FastAPI server implementation"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import uuid

from ..core.game_engine import GameEngine
from ..models.game_state import GameConfig
from ..models.dice import DiceRoll
from ..models.event import StateDiff
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
)


# Global storage for game sessions (in production, use database)
GAME_SESSIONS: Dict[str, GameEngine] = {}


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
    
    @app.post("/sessions", response_model=CreateSessionResponse)
    async def create_session(request: CreateSessionRequest):
        """Create a new game session"""
        try:
            # Create game engine
            session_id = str(uuid.uuid4())
            config = GameConfig(**request.config)
            engine = GameEngine(config, session_id)
            
            # Store session
            GAME_SESSIONS[session_id] = engine
            
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
        
        return {"message": "Session deleted", "session_id": session_id}
    
    return app
