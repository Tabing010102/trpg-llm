"""Game state models"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from .character import Character
from .event import Event


class GameConfig(BaseModel):
    """Game configuration loaded from YAML/JSON"""
    
    # Basic info
    name: str = Field(..., description="Game/campaign name")
    rule_system: str = Field(..., description="Rule system (e.g., 'coc7e', 'dnd5e')")
    description: Optional[str] = Field(None, description="Game description")
    
    # Characters configuration
    characters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Character definitions"
    )
    
    # LLM configuration
    llm_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM configuration (models, prompts, tools)"
    )
    
    # Workflow configuration
    workflow: Dict[str, Any] = Field(
        default_factory=dict,
        description="Game workflow and turn order"
    )
    
    # Auto-progression configuration
    auto_progression: Dict[str, Any] = Field(
        default_factory=dict,
        description="Auto-progression settings (enabled, turn_order, stop_before_human, continue_after_human)"
    )
    
    # Scripts and custom logic
    scripts: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom scripts for game logic"
    )
    
    # Initial state
    initial_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Initial game state"
    )
    
    # Tools configuration
    tools: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Available tools/actions"
    )
    
    # LLM Profiles for multi-provider support
    llm_profiles: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="LLM connection profiles for multi-provider support"
    )


class GameState(BaseModel):
    """Current game state (computed from event history)"""
    
    session_id: str = Field(..., description="Game session identifier")
    config: GameConfig = Field(..., description="Game configuration")
    
    # State data
    state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current global state"
    )
    
    # Characters
    characters: Dict[str, Character] = Field(
        default_factory=dict,
        description="Active characters in the game"
    )
    
    # Game flow
    current_turn: int = Field(0, description="Current turn number")
    current_phase: Optional[str] = Field(None, description="Current game phase")
    current_actor: Optional[str] = Field(None, description="Current active character")
    
    # Messages and history
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Message history"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GameSession(BaseModel):
    """Complete game session with state and event log"""
    
    session_id: str = Field(..., description="Game session identifier")
    config: GameConfig = Field(..., description="Game configuration")
    current_state: GameState = Field(..., description="Current game state")
    event_history: List[Event] = Field(
        default_factory=list,
        description="Complete event history"
    )
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
