"""Auto-progression manager for automatic dialogue/turn progression"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

from ..models.character import CharacterControlType

logger = logging.getLogger(__name__)


class ProgressionState(str, Enum):
    """State of the auto-progression system"""
    IDLE = "idle"  # Waiting for user input
    PROGRESSING = "progressing"  # AI characters are speaking in sequence
    WAITING_FOR_USER = "waiting_for_user"  # Turn belongs to human player
    ERROR = "error"  # LLM call failed, waiting for retry
    PAUSED = "paused"  # Auto-progression is paused


@dataclass
class ProgressionError:
    """Error information for failed progression"""
    character_id: str
    error_message: str
    position_in_queue: int


@dataclass
class AutoProgressionConfig:
    """Configuration for auto-progression"""
    enabled: bool = False
    turn_order: List[str] = field(default_factory=list)  # Character IDs in order
    stop_before_human: bool = True  # Stop before human-controlled characters
    continue_after_human: bool = True  # Continue auto-progression after human speaks


@dataclass
class ProgressionStatus:
    """Current status of auto-progression"""
    state: ProgressionState
    current_position: int  # Position in turn order
    queue: List[str]  # Remaining characters to process
    completed: List[str]  # Characters that have completed their turn
    error: Optional[ProgressionError] = None
    last_speaker_id: Optional[str] = None


class AutoProgressionManager:
    """
    Manages automatic dialogue progression for TRPG sessions.
    
    This implements a state machine that:
    1. Tracks turn order and current position
    2. Queues AI characters for automatic speech
    3. Stops before human-controlled characters
    4. Handles errors with retry capability
    """
    
    def __init__(
        self,
        characters: Dict[str, Any],
        config: Optional[AutoProgressionConfig] = None
    ):
        """
        Initialize the auto-progression manager.
        
        Args:
            characters: Dictionary of character data (id -> character info)
            config: Auto-progression configuration
        """
        self.characters = characters
        self.config = config or AutoProgressionConfig()
        
        # State tracking
        self._state = ProgressionState.IDLE
        self._current_position = 0
        self._queue: List[str] = []
        self._completed: List[str] = []
        self._error: Optional[ProgressionError] = None
        self._last_speaker_id: Optional[str] = None
    
    def get_status(self) -> ProgressionStatus:
        """Get current progression status"""
        return ProgressionStatus(
            state=self._state,
            current_position=self._current_position,
            queue=self._queue.copy(),
            completed=self._completed.copy(),
            error=self._error,
            last_speaker_id=self._last_speaker_id
        )
    
    def update_config(self, config: AutoProgressionConfig) -> None:
        """Update the progression configuration"""
        self.config = config
        # Reset state if turn order changed
        if not self._state == ProgressionState.PROGRESSING:
            self._reset_state()
    
    def update_turn_order(self, turn_order: List[str]) -> None:
        """Update the turn order"""
        self.config.turn_order = turn_order
        if not self._state == ProgressionState.PROGRESSING:
            self._reset_state()
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable auto-progression"""
        self.config.enabled = enabled
        if not enabled:
            self._state = ProgressionState.PAUSED
        elif self._state == ProgressionState.PAUSED:
            self._state = ProgressionState.IDLE
    
    def _reset_state(self) -> None:
        """Reset progression state"""
        self._current_position = 0
        self._queue = []
        self._completed = []
        self._error = None
        self._state = ProgressionState.IDLE if self.config.enabled else ProgressionState.PAUSED
    
    def _is_human_character(self, character_id: str) -> bool:
        """Check if a character is human-controlled"""
        char = self.characters.get(character_id, {})
        if isinstance(char, dict):
            control = char.get("control", "human")
        else:
            control = getattr(char, "control", CharacterControlType.HUMAN)
            if hasattr(control, "value"):
                control = control.value
        return control == "human" or control == CharacterControlType.HUMAN
    
    def _is_ai_character(self, character_id: str) -> bool:
        """Check if a character is AI-controlled"""
        return not self._is_human_character(character_id)
    
    def start_progression(self, from_character_id: Optional[str] = None) -> ProgressionStatus:
        """
        Start auto-progression from a specific point.
        
        Args:
            from_character_id: Start after this character (usually the human who just spoke)
        
        Returns:
            Current progression status
        """
        if not self.config.enabled:
            self._state = ProgressionState.PAUSED
            return self.get_status()
        
        if not self.config.turn_order:
            logger.warning("No turn order configured, auto-progression disabled")
            self._state = ProgressionState.IDLE
            return self.get_status()
        
        # Find starting position
        if from_character_id and from_character_id in self.config.turn_order:
            from_idx = self.config.turn_order.index(from_character_id)
            start_idx = from_idx + 1
            # When starting after a specific character, we only process
            # characters from that point to the end, not wrapping around
            wrap_around = False
            if start_idx >= len(self.config.turn_order):
                start_idx = 0
                wrap_around = True
        else:
            start_idx = 0
            from_idx = -1
            wrap_around = False
        
        # Build queue of characters to process
        self._queue = []
        self._completed = []
        self._current_position = start_idx
        self._state = ProgressionState.IDLE
        
        # Track if we stopped because of a human
        stopped_for_human = False
        
        # Add characters to queue, stopping before human if configured
        turn_order_len = len(self.config.turn_order)
        
        # Determine how many characters to check
        if from_character_id and from_idx >= 0 and not wrap_around:
            # When starting after a character mid-order, only check remaining characters
            chars_to_check = turn_order_len - start_idx
        else:
            # Otherwise check all characters (full order)
            chars_to_check = turn_order_len
        
        for i in range(chars_to_check):
            idx = (start_idx + i) % turn_order_len
            char_id = self.config.turn_order[idx]
            
            if self.config.stop_before_human and self._is_human_character(char_id):
                # Stop before human character - mark as waiting for user
                stopped_for_human = True
                break
            elif self._is_ai_character(char_id):
                self._queue.append(char_id)
        
        # Determine final state
        if self._queue:
            self._state = ProgressionState.PROGRESSING
        elif stopped_for_human:
            self._state = ProgressionState.WAITING_FOR_USER
        else:
            self._state = ProgressionState.IDLE
        
        return self.get_status()
    
    def get_next_character(self) -> Optional[str]:
        """
        Get the next character to process.
        
        Returns:
            Character ID or None if no more characters in queue
        """
        if self._state != ProgressionState.PROGRESSING:
            return None
        
        if not self._queue:
            self._state = ProgressionState.IDLE
            return None
        
        return self._queue[0]
    
    def mark_completed(self, character_id: str) -> ProgressionStatus:
        """
        Mark a character's turn as completed.
        
        Args:
            character_id: Character that completed their turn
        
        Returns:
            Updated progression status
        """
        if character_id in self._queue:
            self._queue.remove(character_id)
            self._completed.append(character_id)
            self._last_speaker_id = character_id
            self._error = None
        
        # Check if we need to stop for human
        if self._queue:
            next_char = self._queue[0]
            if self.config.stop_before_human and self._is_human_character(next_char):
                self._queue.remove(next_char)
                self._state = ProgressionState.WAITING_FOR_USER
        
        if not self._queue and self._state == ProgressionState.PROGRESSING:
            # Queue is empty - check what's next in turn order
            if self.config.stop_before_human and self._last_speaker_id:
                # Find the last speaker's position and see what's next
                if self._last_speaker_id in self.config.turn_order:
                    last_idx = self.config.turn_order.index(self._last_speaker_id)
                    next_idx = (last_idx + 1) % len(self.config.turn_order)
                    next_char_id = self.config.turn_order[next_idx]
                    
                    if self._is_human_character(next_char_id):
                        self._state = ProgressionState.WAITING_FOR_USER
                    else:
                        self._state = ProgressionState.IDLE
                else:
                    self._state = ProgressionState.IDLE
            else:
                self._state = ProgressionState.IDLE
        
        return self.get_status()
    
    def mark_error(self, character_id: str, error_message: str) -> ProgressionStatus:
        """
        Mark that an error occurred during a character's turn.
        
        Args:
            character_id: Character that encountered error
            error_message: Error description
        
        Returns:
            Updated progression status
        """
        position = self._queue.index(character_id) if character_id in self._queue else -1
        self._error = ProgressionError(
            character_id=character_id,
            error_message=error_message,
            position_in_queue=position
        )
        self._state = ProgressionState.ERROR
        
        return self.get_status()
    
    def retry_from_error(self) -> ProgressionStatus:
        """
        Retry progression from the error point.
        
        Returns:
            Updated progression status
        """
        if self._state != ProgressionState.ERROR or not self._error:
            return self.get_status()
        
        self._error = None
        self._state = ProgressionState.PROGRESSING
        
        return self.get_status()
    
    def skip_current(self) -> ProgressionStatus:
        """
        Skip the current character in queue.
        
        Returns:
            Updated progression status
        """
        if self._queue:
            skipped = self._queue.pop(0)
            logger.info(f"Skipped character: {skipped}")
        
        if self._state == ProgressionState.ERROR:
            self._error = None
            if self._queue:
                self._state = ProgressionState.PROGRESSING
            else:
                self._state = ProgressionState.IDLE
        
        return self.get_status()
    
    def pause(self) -> ProgressionStatus:
        """
        Pause auto-progression.
        
        Returns:
            Updated progression status
        """
        if self._state != ProgressionState.PAUSED:
            self._state = ProgressionState.PAUSED
        
        return self.get_status()
    
    def resume(self) -> ProgressionStatus:
        """
        Resume auto-progression from paused state.
        
        Returns:
            Updated progression status
        """
        if self._state == ProgressionState.PAUSED:
            if self._queue:
                self._state = ProgressionState.PROGRESSING
            else:
                self._state = ProgressionState.IDLE
        
        return self.get_status()
    
    def handle_human_message(self, character_id: str) -> ProgressionStatus:
        """
        Handle a message from a human player.
        
        This should be called when a human player sends a message.
        If continue_after_human is enabled, it will restart progression
        after the human's position.
        
        Args:
            character_id: Human character who sent the message
        
        Returns:
            Updated progression status
        """
        self._last_speaker_id = character_id
        
        if not self.config.enabled:
            self._state = ProgressionState.PAUSED
            return self.get_status()
        
        if self.config.continue_after_human:
            return self.start_progression(from_character_id=character_id)
        else:
            self._state = ProgressionState.IDLE
            return self.get_status()
    
    def get_human_characters(self) -> List[str]:
        """
        Get list of human-controlled characters in turn order.
        
        Returns:
            List of human character IDs
        """
        return [
            char_id for char_id in self.config.turn_order
            if self._is_human_character(char_id)
        ]
    
    def get_ai_characters(self) -> List[str]:
        """
        Get list of AI-controlled characters in turn order.
        
        Returns:
            List of AI character IDs
        """
        return [
            char_id for char_id in self.config.turn_order
            if self._is_ai_character(char_id)
        ]
