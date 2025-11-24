"""Dice rolling models"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DiceRoll(BaseModel):
    """Dice roll request"""
    
    notation: str = Field(..., description="Dice notation (e.g., '1d20', '3d6+5')")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    character_id: Optional[str] = Field(None, description="Character making the roll")
    modifier: int = Field(0, description="Additional modifier")
    
    # CoC specific
    difficulty: Optional[str] = Field(None, description="Difficulty level (regular, hard, extreme)")
    target_value: Optional[int] = Field(None, description="Target value for success check")


class DiceResult(BaseModel):
    """Result of a dice roll"""
    
    notation: str = Field(..., description="Original dice notation")
    rolls: List[int] = Field(..., description="Individual die results")
    total: int = Field(..., description="Total result")
    modifier: int = Field(0, description="Applied modifier")
    final_result: int = Field(..., description="Final result with modifier")
    
    # Success check results (optional)
    success: Optional[bool] = Field(None, description="Whether the roll succeeded")
    critical_success: Optional[bool] = Field(None, description="Critical success")
    critical_failure: Optional[bool] = Field(None, description="Critical failure")
    
    # CoC specific
    success_level: Optional[str] = Field(None, description="Success level (regular, hard, extreme)")
    
    # Metadata
    reason: Optional[str] = Field(None, description="Reason for the roll")
    character_id: Optional[str] = Field(None, description="Character making the roll")
