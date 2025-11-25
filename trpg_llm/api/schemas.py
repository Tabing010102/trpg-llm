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


class ChatRequest(BaseModel):
    """Request for chat/message pipeline"""
    role_id: str = Field(..., description="Character ID sending/generating message")
    message: Optional[str] = Field(None, description="Message content (required for humans)")
    template: Optional[str] = Field(None, description="Optional Jinja2 template for prompt")
    max_tool_iterations: int = Field(3, description="Max tool calling iterations")
    llm_profile_id: Optional[str] = Field(None, description="Optional LLM profile ID to use for this request")


class ChatResponse(BaseModel):
    """Response for chat pipeline"""
    content: Optional[str] = Field(None, description="Generated message content")
    state_diffs: List[Dict[str, Any]] = Field(default_factory=list, description="State changes")
    current_state: Dict[str, Any] = Field(..., description="Current game state")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tool calls made")
    role_id: str = Field(..., description="Character ID")
    is_ai: bool = Field(..., description="Whether this is an AI character")
    error: Optional[str] = Field(None, description="Error message if any")
    used_profile_id: Optional[str] = Field(None, description="Profile ID actually used for this message")


class RedrawMessageRequest(BaseModel):
    """Request to redraw last AI message"""
    character_id: str = Field(..., description="AI character whose message to redraw")
    template: Optional[str] = Field(None, description="Optional template for regeneration")
    llm_profile_id: Optional[str] = Field(None, description="Optional LLM profile ID for regeneration")


class EditEventRequest(BaseModel):
    """Request to edit an event"""
    event_id: str = Field(..., description="ID of event to edit")
    new_data: Optional[Dict[str, Any]] = Field(None, description="New event data")
    new_state_diffs: Optional[List[Dict[str, Any]]] = Field(None, description="New state diffs")


class EditEventResponse(BaseModel):
    """Response for event editing"""
    session_id: str
    event_id: str
    current_state: Dict[str, Any]


class SetCharacterProfileRequest(BaseModel):
    """Request to set a character's profile for a session"""
    profile_id: str = Field(..., description="Profile ID to use for this character")
