"""Character models for TRPG system"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class CharacterType(str, Enum):
    """Type of character in the game"""
    PLAYER = "player"  # Player character (PC)
    NPC = "npc"  # Non-player character
    GM = "gm"  # Game Master


class CharacterControlType(str, Enum):
    """Who controls the character"""
    HUMAN = "human"  # Human player
    AI = "ai"  # AI controlled


class Character(BaseModel):
    """Character representation in TRPG"""
    
    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., description="Character name")
    type: CharacterType = Field(..., description="Character type (player/npc/gm)")
    control: CharacterControlType = Field(..., description="Control type (human/ai)")
    
    # Character attributes (flexible for different rule systems)
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Character attributes (stats, skills, etc.)"
    )
    
    # Character state (health, sanity, etc.)
    state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current character state"
    )
    
    # Inventory and equipment
    inventory: List[str] = Field(
        default_factory=list,
        description="Character inventory items"
    )
    
    # Background and description
    description: Optional[str] = Field(None, description="Character description")
    background: Optional[str] = Field(None, description="Character background story")
    
    # AI configuration (if AI controlled)
    ai_config: Optional[Dict[str, Any]] = Field(
        None,
        description="AI configuration for this character"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        use_enum_values = True


class CharacterSheet(BaseModel):
    """Detailed character sheet for specific rule systems"""
    
    character: Character
    rule_system: str = Field(..., description="Rule system (e.g., 'coc7e')")
    
    # Rule-specific data
    skills: Dict[str, int] = Field(default_factory=dict, description="Character skills")
    attributes: Dict[str, int] = Field(default_factory=dict, description="Character attributes")
    
    # CoC specific
    sanity: Optional[int] = Field(None, description="Sanity points (CoC)")
    hp: Optional[int] = Field(None, description="Hit points")
    mp: Optional[int] = Field(None, description="Magic points")
    luck: Optional[int] = Field(None, description="Luck points")
    
    class Config:
        use_enum_values = True
