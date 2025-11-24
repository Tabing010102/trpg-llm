"""Tests for dice rolling system"""

import pytest
from trpg_llm.core.dice import DiceSystem
from trpg_llm.models.dice import DiceRoll


class TestDiceSystem:
    """Test dice rolling functionality"""
    
    def test_parse_notation_simple(self):
        """Test parsing simple dice notation"""
        dice = DiceSystem()
        count, sides, modifier = dice.parse_notation("1d20")
        
        assert count == 1
        assert sides == 20
        assert modifier == 0
    
    def test_parse_notation_with_modifier(self):
        """Test parsing dice notation with modifier"""
        dice = DiceSystem()
        count, sides, modifier = dice.parse_notation("3d6+5")
        
        assert count == 3
        assert sides == 6
        assert modifier == 5
    
    def test_parse_notation_negative_modifier(self):
        """Test parsing dice notation with negative modifier"""
        dice = DiceSystem()
        count, sides, modifier = dice.parse_notation("1d100-10")
        
        assert count == 1
        assert sides == 100
        assert modifier == -10
    
    def test_roll_dice_count(self):
        """Test that correct number of dice are rolled"""
        dice = DiceSystem(seed=42)
        rolls = dice.roll_dice(3, 6)
        
        assert len(rolls) == 3
        assert all(1 <= r <= 6 for r in rolls)
    
    def test_roll_with_seed(self):
        """Test that seeded rolls are reproducible"""
        dice1 = DiceSystem(seed=42)
        rolls1 = dice1.roll_dice(5, 20)
        
        # Create new instance with same seed
        dice2 = DiceSystem(seed=42)
        rolls2 = dice2.roll_dice(5, 20)
        
        # First roll from each instance should be the same
        assert rolls1[0] == rolls2[0]
    
    def test_roll_basic(self):
        """Test basic dice roll"""
        dice = DiceSystem()
        dice_roll = DiceRoll(notation="1d20")
        
        result = dice.roll(dice_roll)
        
        assert result.notation == "1d20"
        assert len(result.rolls) == 1
        assert 1 <= result.final_result <= 20
    
    def test_roll_with_modifier(self):
        """Test dice roll with modifier"""
        dice = DiceSystem(seed=42)
        dice_roll = DiceRoll(notation="1d20", modifier=5)
        
        result = dice.roll(dice_roll)
        
        assert result.modifier == 5
        assert result.final_result == result.total + 5
    
    def test_coc_success_check_regular(self):
        """Test CoC regular success check"""
        dice = DiceSystem(seed=42)
        dice_roll = DiceRoll(
            notation="1d100",
            target_value=50,
            difficulty="regular",
        )
        
        result = dice.roll(dice_roll)
        
        assert result.success is not None
        assert result.success == (result.final_result <= 50)
    
    def test_coc_success_check_hard(self):
        """Test CoC hard success check"""
        dice = DiceSystem()
        
        # A roll of 25 should succeed on hard difficulty for target 50
        assert dice._check_success(25, 50, "hard") is True
        assert dice._check_success(26, 50, "hard") is False
    
    def test_coc_success_check_extreme(self):
        """Test CoC extreme success check"""
        dice = DiceSystem()
        
        # A roll of 10 should succeed on extreme difficulty for target 50
        assert dice._check_success(10, 50, "extreme") is True
        assert dice._check_success(11, 50, "extreme") is False
    
    def test_coc_critical_success(self):
        """Test CoC critical success (roll of 1)"""
        dice = DiceSystem()
        
        assert dice._check_critical_success(1, 50) is True
        assert dice._check_critical_success(2, 50) is False
    
    def test_coc_critical_failure(self):
        """Test CoC critical failure"""
        dice = DiceSystem()
        
        assert dice._check_critical_failure(100, 50) is True
        assert dice._check_critical_failure(96, 40) is True
        assert dice._check_critical_failure(95, 40) is False
    
    def test_success_level(self):
        """Test success level determination"""
        dice = DiceSystem()
        
        assert dice._get_success_level(5, 50) == "extreme"
        assert dice._get_success_level(15, 50) == "hard"
        assert dice._get_success_level(35, 50) == "regular"
        assert dice._get_success_level(51, 50) is None
