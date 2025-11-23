"""Dice rolling system supporting various rule systems"""

import re
import random
from typing import List, Optional, Tuple

from ..models.dice import DiceRoll, DiceResult


class DiceSystem:
    """
    Dice rolling system with support for various notations and rule systems.
    Supports standard notation (1d20, 3d6+5) and CoC skill checks.
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
    
    def parse_notation(self, notation: str) -> Tuple[int, int, int]:
        """
        Parse dice notation into (count, sides, modifier).
        Examples: "1d20", "3d6+5", "1d100-10"
        """
        notation = notation.lower().strip()
        
        # Match pattern like "1d20+5" or "2d6-3"
        pattern = r'(\d+)d(\d+)([+-]\d+)?'
        match = re.match(pattern, notation)
        
        if not match:
            raise ValueError(f"Invalid dice notation: {notation}")
        
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        return count, sides, modifier
    
    def roll_dice(self, count: int, sides: int) -> List[int]:
        """Roll multiple dice and return individual results"""
        return [random.randint(1, sides) for _ in range(count)]
    
    def roll(self, dice_roll: DiceRoll) -> DiceResult:
        """
        Execute a dice roll and return the result.
        """
        # Parse notation
        count, sides, base_modifier = self.parse_notation(dice_roll.notation)
        
        # Apply additional modifier
        total_modifier = base_modifier + dice_roll.modifier
        
        # Roll dice
        rolls = self.roll_dice(count, sides)
        total = sum(rolls)
        final_result = total + total_modifier
        
        # Create result
        result = DiceResult(
            notation=dice_roll.notation,
            rolls=rolls,
            total=total,
            modifier=total_modifier,
            final_result=final_result,
            reason=dice_roll.reason,
            character_id=dice_roll.character_id,
        )
        
        # Check for success if target value is provided (CoC style)
        if dice_roll.target_value is not None:
            result.success = self._check_success(
                final_result,
                dice_roll.target_value,
                dice_roll.difficulty,
            )
            result.critical_success = self._check_critical_success(
                final_result,
                dice_roll.target_value,
            )
            result.critical_failure = self._check_critical_failure(
                final_result,
                dice_roll.target_value,
            )
            result.success_level = self._get_success_level(
                final_result,
                dice_roll.target_value,
            )
        
        return result
    
    def _check_success(
        self,
        roll: int,
        target: int,
        difficulty: Optional[str] = None,
    ) -> bool:
        """
        Check if a roll succeeds against a target value.
        Supports CoC difficulty levels: regular, hard, extreme.
        """
        if difficulty == "hard":
            return roll <= target // 2
        elif difficulty == "extreme":
            return roll <= target // 5
        else:  # regular or None
            return roll <= target
    
    def _check_critical_success(self, roll: int, target: int) -> bool:
        """Check for critical success (CoC: roll of 1)"""
        return roll == 1
    
    def _check_critical_failure(self, roll: int, target: int) -> bool:
        """Check for critical failure (CoC: roll of 100, or 96+ if target < 50)"""
        if roll == 100:
            return True
        if target < 50 and roll >= 96:
            return True
        return False
    
    def _get_success_level(self, roll: int, target: int) -> Optional[str]:
        """
        Determine success level for CoC.
        Returns: "extreme", "hard", "regular", or None for failure.
        """
        if roll <= target // 5:
            return "extreme"
        elif roll <= target // 2:
            return "hard"
        elif roll <= target:
            return "regular"
        return None
    
    def roll_d100(self) -> int:
        """Roll a d100 (common in CoC)"""
        return random.randint(1, 100)
    
    def roll_d20(self) -> int:
        """Roll a d20 (common in D&D)"""
        return random.randint(1, 20)
    
    def roll_d6(self, count: int = 1) -> List[int]:
        """Roll one or more d6"""
        return self.roll_dice(count, 6)
