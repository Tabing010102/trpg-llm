"""API request/response schemas"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request to create a new game session"""
    config: Dict[str, Any] = Field(..., description="Game configuration")


class CreateSessionResponse(BaseModel):
    """Response for session creation"""
    session_id: str
    state: Dict[str, Any]


class ActionRequest(BaseModel):
    """Request to perform a game action"""
    actor_id: str = Field(..., description="Character performing the action")
    action_type: str = Field(..., description="Type of action")
    data: Dict[str, Any] = Field(default_factory=dict, description="Action data")
    state_diffs: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional state diffs"
    )


class ActionResponse(BaseModel):
    """Response for action execution"""
    session_id: str
    state: Dict[str, Any]


class DiceRollRequest(BaseModel):
    """Request to roll dice"""
    notation: str = Field(..., description="Dice notation (e.g., '1d20', '3d6+5')")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    character_id: Optional[str] = Field(None, description="Character making the roll")
    modifier: int = Field(0, description="Additional modifier")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    target_value: Optional[int] = Field(None, description="Target value for success")


class DiceRollResponse(BaseModel):
    """Response for dice roll"""
    session_id: str
    result: Dict[str, Any]
    state: Dict[str, Any]


class StateUpdateRequest(BaseModel):
    """Request to update game state"""
    actor_id: Optional[str] = Field(None, description="Actor making the change")
    path: str = Field(..., description="State path (dot notation)")
    operation: str = Field(..., description="Operation type")
    value: Any = Field(..., description="Value for the operation")


class MessageRequest(BaseModel):
    """Request to add a message"""
    sender_id: str = Field(..., description="Message sender")
    content: str = Field(..., description="Message content")
    message_type: str = Field("text", description="Message type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RollbackRequest(BaseModel):
    """Request to rollback game state"""
    event_id: Optional[str] = Field(None, description="Event ID to rollback to")
    timestamp: Optional[datetime] = Field(None, description="Timestamp to rollback to")
