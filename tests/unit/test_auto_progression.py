"""Unit tests for auto-progression manager"""

import pytest
from trpg_llm.core.auto_progression import (
    AutoProgressionManager,
    AutoProgressionConfig,
    ProgressionState,
)


class TestAutoProgressionManager:
    """Tests for AutoProgressionManager"""
    
    @pytest.fixture
    def characters(self):
        """Sample characters for testing"""
        return {
            "player1": {
                "id": "player1",
                "name": "Hero",
                "type": "player",
                "control": "human",
            },
            "gm": {
                "id": "gm",
                "name": "Game Master",
                "type": "gm",
                "control": "ai",
            },
            "npc1": {
                "id": "npc1",
                "name": "NPC",
                "type": "npc",
                "control": "ai",
            },
            "player2": {
                "id": "player2",
                "name": "AI Player",
                "type": "player",
                "control": "ai",
            },
        }
    
    @pytest.fixture
    def manager(self, characters):
        """Create a manager with default config"""
        config = AutoProgressionConfig(
            enabled=True,
            turn_order=["gm", "player1", "npc1", "player2"],
            stop_before_human=True,
            continue_after_human=True,
        )
        return AutoProgressionManager(characters, config)
    
    def test_initialization(self, manager):
        """Test manager initializes correctly"""
        status = manager.get_status()
        assert status.state == ProgressionState.IDLE
        assert status.queue == []
        assert status.completed == []
        assert status.error is None
    
    def test_start_progression_from_beginning(self, manager):
        """Test starting progression from the beginning"""
        status = manager.start_progression()
        
        # GM should be first (AI)
        assert status.state == ProgressionState.PROGRESSING
        assert "gm" in status.queue
        assert "player1" not in status.queue  # Human, should stop before
    
    def test_start_progression_after_human(self, manager):
        """Test starting progression after human speaks"""
        status = manager.start_progression(from_character_id="player1")
        
        # Should start with npc1 (after player1)
        assert status.state == ProgressionState.PROGRESSING
        assert status.queue == ["npc1", "player2"]
    
    def test_mark_completed(self, manager):
        """Test marking a character's turn as completed"""
        manager.start_progression()
        
        # Mark GM as completed
        status = manager.mark_completed("gm")
        
        assert "gm" in status.completed
        assert "gm" not in status.queue
    
    def test_progression_stops_before_human(self, manager):
        """Test that progression stops before human character"""
        status = manager.start_progression()
        
        # GM is first AI, player1 is human - should only queue GM
        assert "gm" in status.queue
        assert "player1" not in status.queue
        
        # Mark GM as completed
        status = manager.mark_completed("gm")
        
        # Should now be waiting for user
        assert status.state == ProgressionState.WAITING_FOR_USER
    
    def test_mark_error(self, manager):
        """Test marking an error during progression"""
        manager.start_progression()
        
        status = manager.mark_error("gm", "LLM call failed")
        
        assert status.state == ProgressionState.ERROR
        assert status.error is not None
        assert status.error.character_id == "gm"
        assert status.error.error_message == "LLM call failed"
    
    def test_retry_from_error(self, manager):
        """Test retrying after an error"""
        manager.start_progression()
        manager.mark_error("gm", "LLM call failed")
        
        status = manager.retry_from_error()
        
        assert status.state == ProgressionState.PROGRESSING
        assert status.error is None
    
    def test_skip_current(self, manager):
        """Test skipping the current character"""
        manager.start_progression()
        
        # Skip GM
        status = manager.skip_current()
        
        assert "gm" not in status.queue
    
    def test_pause_and_resume(self, manager):
        """Test pausing and resuming progression"""
        manager.start_progression()
        
        status = manager.pause()
        assert status.state == ProgressionState.PAUSED
        
        status = manager.resume()
        assert status.state == ProgressionState.PROGRESSING
    
    def test_handle_human_message(self, manager):
        """Test handling a human message"""
        status = manager.handle_human_message("player1")
        
        # Should start progression from player1's position
        assert status.state == ProgressionState.PROGRESSING
        # Should queue characters after player1
        assert "npc1" in status.queue
        assert "player2" in status.queue
    
    def test_disabled_manager(self, characters):
        """Test manager when disabled"""
        config = AutoProgressionConfig(
            enabled=False,
            turn_order=["gm", "player1"],
        )
        manager = AutoProgressionManager(characters, config)
        
        status = manager.start_progression()
        
        assert status.state == ProgressionState.PAUSED
    
    def test_set_enabled(self, manager):
        """Test enabling/disabling the manager"""
        manager.set_enabled(False)
        status = manager.get_status()
        assert status.state == ProgressionState.PAUSED
        
        manager.set_enabled(True)
        status = manager.get_status()
        assert status.state == ProgressionState.IDLE
    
    def test_update_turn_order(self, manager):
        """Test updating the turn order"""
        manager.update_turn_order(["npc1", "player1", "gm"])
        
        status = manager.start_progression()
        
        # NPC1 should be first now
        assert status.queue[0] == "npc1"
    
    def test_get_human_characters(self, manager):
        """Test getting list of human characters"""
        humans = manager.get_human_characters()
        
        assert "player1" in humans
        assert "gm" not in humans
        assert "npc1" not in humans
    
    def test_get_ai_characters(self, manager):
        """Test getting list of AI characters"""
        ai_chars = manager.get_ai_characters()
        
        assert "gm" in ai_chars
        assert "npc1" in ai_chars
        assert "player2" in ai_chars
        assert "player1" not in ai_chars
    
    def test_empty_turn_order(self, characters):
        """Test manager with empty turn order"""
        config = AutoProgressionConfig(
            enabled=True,
            turn_order=[],
        )
        manager = AutoProgressionManager(characters, config)
        
        status = manager.start_progression()
        
        assert status.state == ProgressionState.IDLE
        assert status.queue == []
    
    def test_continue_after_human_disabled(self, characters):
        """Test with continue_after_human disabled"""
        config = AutoProgressionConfig(
            enabled=True,
            turn_order=["gm", "player1", "npc1"],
            stop_before_human=True,
            continue_after_human=False,
        )
        manager = AutoProgressionManager(characters, config)
        
        status = manager.handle_human_message("player1")
        
        # Should go to idle instead of progressing
        assert status.state == ProgressionState.IDLE
    
    def test_stop_before_human_disabled(self, characters):
        """Test with stop_before_human disabled"""
        config = AutoProgressionConfig(
            enabled=True,
            turn_order=["gm", "player1", "npc1"],
            stop_before_human=False,
            continue_after_human=True,
        )
        manager = AutoProgressionManager(characters, config)
        
        status = manager.start_progression()
        
        # Should queue all AI characters
        assert "gm" in status.queue
        assert "npc1" in status.queue
        # player1 is human, not AI, so won't be in queue
        assert "player1" not in status.queue
    
    def test_full_cycle_progression(self, characters):
        """Test a full cycle of progression"""
        config = AutoProgressionConfig(
            enabled=True,
            turn_order=["gm", "player1", "npc1", "player2"],
            stop_before_human=True,
            continue_after_human=True,
        )
        manager = AutoProgressionManager(characters, config)
        
        # Start from beginning - should queue GM only (stops before player1)
        status = manager.start_progression()
        assert status.queue == ["gm"]
        
        # GM speaks
        status = manager.mark_completed("gm")
        assert status.state == ProgressionState.WAITING_FOR_USER
        
        # Human player1 speaks
        status = manager.handle_human_message("player1")
        assert status.queue == ["npc1", "player2"]
        
        # NPC1 speaks
        status = manager.mark_completed("npc1")
        assert "npc1" in status.completed
        
        # Player2 (AI) speaks
        status = manager.mark_completed("player2")
        assert status.state == ProgressionState.IDLE  # Cycle complete
