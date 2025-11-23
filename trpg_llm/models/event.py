"""Event and state diff models for event sourcing"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the game"""
    GAME_START = "game_start"
    GAME_END = "game_end"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    ACTION = "action"
    DICE_ROLL = "dice_roll"
    STATE_UPDATE = "state_update"
    MESSAGE = "message"
    CHARACTER_JOIN = "character_join"
    CHARACTER_LEAVE = "character_leave"


class StateDiff(BaseModel):
    """Represents an atomic state change"""
    
    path: str = Field(..., description="JSON path to the state property (e.g., 'characters.player1.state.hp')")
    operation: str = Field(..., description="Operation type: set, add, subtract, multiply, append, remove")
    value: Any = Field(..., description="Value for the operation")
    previous_value: Optional[Any] = Field(None, description="Previous value before change")
    
    class Config:
        use_enum_values = True


class Event(BaseModel):
    """Event in the game timeline"""
    
    id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    type: EventType = Field(..., description="Event type")
    
    # Event source
    actor_id: Optional[str] = Field(None, description="Character/entity that triggered the event")
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    
    # State changes
    state_diffs: List[StateDiff] = Field(
        default_factory=list,
        description="State changes caused by this event"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EventLog(BaseModel):
    """Collection of events for a game session"""
    
    session_id: str = Field(..., description="Game session identifier")
    events: List[Event] = Field(default_factory=list, description="List of events")
    
    def add_event(self, event: Event) -> None:
        """Add an event to the log"""
        self.events.append(event)
    
    def get_events_after(self, timestamp: datetime) -> List[Event]:
        """Get events after a specific timestamp"""
        return [e for e in self.events if e.timestamp > timestamp]
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get events of a specific type"""
        return [e for e in self.events if e.type == event_type]
