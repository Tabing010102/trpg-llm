"""Game engine that orchestrates game flow"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from ..models.game_state import GameConfig, GameState, GameSession
from ..models.event import Event, EventType, StateDiff
from ..models.dice import DiceRoll
from ..state.state_machine import StateMachine
from .dice import DiceSystem


class GameEngine:
    """
    Main game engine that orchestrates game flow.
    Manages state machine, dice rolling, and game logic.
    """
    
    def __init__(self, config: GameConfig, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.config = config
        self.state_machine = StateMachine(self.session_id, config)
        self.dice_system = DiceSystem()
        
        # Initialize game
        self._initialize_game()
    
    def _initialize_game(self) -> None:
        """Initialize the game with starting event"""
        start_event = self.state_machine.create_event(
            event_type=EventType.GAME_START,
            data={
                "timestamp": datetime.utcnow().isoformat(),
                "config_name": self.config.name,
            }
        )
        self.state_machine.add_event(start_event)
    
    def get_state(self) -> GameState:
        """Get current game state"""
        return self.state_machine.get_current_state()
    
    def get_session(self) -> GameSession:
        """Get complete game session"""
        return self.state_machine.get_session()
    
    def perform_action(
        self,
        actor_id: str,
        action_type: str,
        data: Dict[str, Any],
        state_diffs: Optional[List[StateDiff]] = None,
    ) -> GameState:
        """
        Perform a game action.
        Creates an event and updates state.
        """
        event = self.state_machine.create_event(
            event_type=EventType.ACTION,
            actor_id=actor_id,
            data={
                "action_type": action_type,
                **data,
            },
            state_diffs=state_diffs or [],
        )
        
        return self.state_machine.add_event(event)
    
    def roll_dice(
        self,
        dice_roll: DiceRoll,
    ) -> GameState:
        """
        Perform a dice roll and record it as an event.
        """
        # Execute the roll
        result = self.dice_system.roll(dice_roll)
        
        # Create event
        event = self.state_machine.create_event(
            event_type=EventType.DICE_ROLL,
            actor_id=dice_roll.character_id,
            data={
                "roll": dice_roll.dict(),
                "result": result.dict(),
            },
        )
        
        return self.state_machine.add_event(event)
    
    def update_state(
        self,
        actor_id: Optional[str],
        path: str,
        operation: str,
        value: Any,
    ) -> GameState:
        """
        Update game state with a single state diff.
        """
        state_diff = StateDiff(
            path=path,
            operation=operation,
            value=value,
        )
        
        event = self.state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            actor_id=actor_id,
            data={
                "path": path,
                "operation": operation,
                "value": value,
            },
            state_diffs=[state_diff],
        )
        
        return self.state_machine.add_event(event)
    
    def add_message(
        self,
        sender_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GameState:
        """
        Add a message to the game.
        """
        message_data = {
            "sender_id": sender_id,
            "content": content,
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        event = self.state_machine.create_event(
            event_type=EventType.MESSAGE,
            actor_id=sender_id,
            data=message_data,
        )
        
        return self.state_machine.add_event(event)
    
    def start_turn(
        self,
        actor_id: str,
        turn_number: Optional[int] = None,
    ) -> GameState:
        """
        Start a new turn.
        """
        current_state = self.get_state()
        if turn_number is None:
            turn_number = current_state.current_turn + 1
        
        event = self.state_machine.create_event(
            event_type=EventType.TURN_START,
            actor_id=actor_id,
            data={
                "turn_number": turn_number,
                "actor_id": actor_id,
            },
        )
        
        return self.state_machine.add_event(event)
    
    def end_turn(
        self,
        actor_id: str,
    ) -> GameState:
        """
        End the current turn.
        """
        event = self.state_machine.create_event(
            event_type=EventType.TURN_END,
            actor_id=actor_id,
            data={
                "actor_id": actor_id,
            },
        )
        
        return self.state_machine.add_event(event)
    
    def rollback_to_event(self, event_id: str) -> GameState:
        """
        Rollback game state to a specific event.
        """
        return self.state_machine.rollback_to(event_id)
    
    def rollback_to_timestamp(self, timestamp: datetime) -> GameState:
        """
        Rollback game state to a specific timestamp.
        """
        return self.state_machine.rollback_to_timestamp(timestamp)
    
    def get_event_history(self) -> List[Event]:
        """Get complete event history"""
        return self.state_machine.event_history
