"""State machine with event sourcing"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import copy
import uuid

from ..models.event import Event, EventType, StateDiff
from ..models.game_state import GameState, GameConfig, GameSession
from ..models.character import Character
from .operations import apply_state_diff


class StateMachine:
    """
    State Machine that manages game state through event sourcing.
    All state changes are recorded as events with state diffs.
    Current state is computed from event history.
    """
    
    def __init__(self, session_id: str, config: GameConfig):
        self.session_id = session_id
        self.config = config
        self.event_history: List[Event] = []
        self._current_state: Optional[GameState] = None
    
    def get_current_state(self) -> GameState:
        """
        Compute current state from event history.
        Uses event sourcing pattern to replay all events.
        """
        # Start with initial state from config
        state_data = copy.deepcopy(self.config.initial_state)
        
        # Initialize characters from config
        characters = {}
        for char_id, char_data in self.config.characters.items():
            if isinstance(char_data, dict):
                characters[char_id] = Character(**char_data)
            else:
                characters[char_id] = char_data
        
        # Create base state
        current_state = GameState(
            session_id=self.session_id,
            config=self.config,
            state=state_data,
            characters=characters,
        )
        
        # Replay all events
        for event in self.event_history:
            self._apply_event(current_state, event)
        
        return current_state
    
    def _apply_event(self, state: GameState, event: Event) -> None:
        """Apply an event's state diffs to the state"""
        
        # Apply all state diffs
        for diff in event.state_diffs:
            # Check if path targets character state
            if diff.path.startswith("characters."):
                # Parse character path: characters.player1.state.hp -> ["characters", "player1", "state", "hp"]
                parts = diff.path.split(".", 2)  # Split into ["characters", "player1", "state.hp"]
                if len(parts) >= 3:
                    char_id = parts[1]
                    char_path = parts[2]  # e.g., "state.hp"
                    
                    if char_id in state.characters:
                        # Get character as dict for manipulation
                        char_dict = state.characters[char_id].dict()
                        apply_state_diff(char_dict, char_path, diff.operation, diff.value)
                        # Update character with modified data
                        state.characters[char_id] = Character(**char_dict)
            else:
                # Apply to global state
                apply_state_diff(state.state, diff.path, diff.operation, diff.value)
        
        # Update messages if this is a message event
        if event.type == EventType.MESSAGE:
            state.messages.append(event.data)
        
        # Update turn tracking
        if event.type == EventType.TURN_START:
            state.current_turn = event.data.get("turn_number", state.current_turn)
            state.current_actor = event.data.get("actor_id")
        
        # Update timestamp
        state.updated_at = event.timestamp
    
    def add_event(self, event: Event) -> GameState:
        """
        Add a new event to the history and return updated state.
        """
        # Ensure event has an ID
        if not event.id:
            event.id = str(uuid.uuid4())
        
        # Add to history
        self.event_history.append(event)
        
        # Recompute state
        self._current_state = self.get_current_state()
        return self._current_state
    
    def create_event(
        self,
        event_type: EventType,
        actor_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        state_diffs: Optional[List[StateDiff]] = None,
    ) -> Event:
        """Create a new event with automatic ID and timestamp"""
        return Event(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            type=event_type,
            actor_id=actor_id,
            data=data or {},
            state_diffs=state_diffs or [],
        )
    
    def rollback_to(self, event_id: str) -> GameState:
        """
        Rollback state to a specific event.
        Removes all events after the specified event.
        """
        # Find the event index
        event_index = None
        for i, event in enumerate(self.event_history):
            if event.id == event_id:
                event_index = i
                break
        
        if event_index is None:
            raise ValueError(f"Event {event_id} not found in history")
        
        # Keep only events up to and including the target
        self.event_history = self.event_history[:event_index + 1]
        
        # Recompute state
        self._current_state = self.get_current_state()
        return self._current_state
    
    def rollback_to_timestamp(self, timestamp: datetime) -> GameState:
        """
        Rollback state to a specific timestamp.
        Removes all events after the timestamp.
        """
        # Find the last event before or at the timestamp
        cutoff_index = 0
        for i, event in enumerate(self.event_history):
            if event.timestamp <= timestamp:
                cutoff_index = i
            else:
                break
        
        # Keep only events up to the cutoff
        self.event_history = self.event_history[:cutoff_index + 1]
        
        # Recompute state
        self._current_state = self.get_current_state()
        return self._current_state
    
    def get_session(self) -> GameSession:
        """Get complete game session with state and history"""
        return GameSession(
            session_id=self.session_id,
            config=self.config,
            current_state=self.get_current_state(),
            event_history=self.event_history,
        )
    
    def restore_from_session(self, session: GameSession) -> None:
        """Restore state machine from a saved session"""
        self.session_id = session.session_id
        self.config = session.config
        self.event_history = session.event_history
        self._current_state = None  # Will be recomputed on next get_current_state
