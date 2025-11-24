"""Game engine that orchestrates game flow"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timezone

from ..models.game_state import GameConfig, GameState, GameSession
from ..models.event import Event, EventType, StateDiff
from ..models.dice import DiceRoll
from ..state.state_machine import StateMachine
from .dice import DiceSystem
from ..sandbox.sandbox import ScriptSandbox


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
        self.sandbox = ScriptSandbox()
        
        # Initialize game
        self._initialize_game()
    
    def _initialize_game(self) -> None:
        """Initialize the game with starting event"""
        start_event = self.state_machine.create_event(
            event_type=EventType.GAME_START,
            data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
        
        new_state = self.state_machine.add_event(event)
        
        # Execute script hooks if configured
        self._execute_script_hook("on_turn_end", new_state)
        
        return new_state
    
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
    
    def _execute_script_hook(self, hook_name: str, game_state: GameState) -> None:
        """
        Execute a script hook if configured.
        
        Args:
            hook_name: Name of the hook (e.g., 'on_turn_end')
            game_state: Current game state
        """
        if not self.config.scripts or hook_name not in self.config.scripts:
            return
        
        script = self.config.scripts[hook_name]
        
        # Build read-only context for script
        context = {
            "state": game_state.state,
            "characters": {
                char_id: {
                    "id": char.id,
                    "name": char.name,
                    "type": char.type.value if hasattr(char.type, 'value') else char.type,
                    "attributes": char.attributes,
                    "state": char.state,
                }
                for char_id, char in game_state.characters.items()
            },
            "current_turn": game_state.current_turn,
            "current_phase": game_state.current_phase,
            "current_actor": game_state.current_actor,
        }
        
        try:
            # Execute script and get result
            result = self.sandbox.execute_statement(script, context)
            
            # Check if script generated state updates
            # Scripts should set a special 'state_updates' variable
            if "state_updates" in result and isinstance(result["state_updates"], list):
                for update in result["state_updates"]:
                    if isinstance(update, dict) and "path" in update:
                        self.update_state(
                            actor_id="system",
                            path=update["path"],
                            operation=update.get("operation", "set"),
                            value=update.get("value")
                        )
        except Exception as e:
            # Log error but don't crash the game
            print(f"Script hook '{hook_name}' failed: {str(e)}")
    
    def execute_script(
        self,
        script: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a custom script with optional context.
        
        Args:
            script: Python script to execute
            context: Optional context variables
        
        Returns:
            Result of script execution
        """
        game_state = self.get_state()
        
        # Build default context
        default_context = {
            "state": game_state.state,
            "characters": {
                char_id: {
                    "id": char.id,
                    "name": char.name,
                    "type": char.type.value if hasattr(char.type, 'value') else char.type,
                    "attributes": char.attributes,
                    "state": char.state,
                }
                for char_id, char in game_state.characters.items()
            },
            "current_turn": game_state.current_turn,
        }
        
        # Merge with provided context
        if context:
            default_context.update(context)
        
        return self.sandbox.execute_statement(script, default_context)
    
    def redraw_last_ai_message(self, character_id: str) -> GameState:
        """
        Redraw (regenerate) the last message from an AI character.
        Finds the last message event from the character, rolls back to before it,
        then returns the state ready for regeneration.
        
        Args:
            character_id: ID of the AI character whose message to redraw
        
        Returns:
            Game state after rollback, ready for regeneration
        """
        # Find the last message event from this character
        event_history = self.get_event_history()
        last_message_event = None
        for event in reversed(event_history):
            if (event.type == EventType.MESSAGE and 
                event.actor_id == character_id):
                last_message_event = event
                break
        
        if not last_message_event:
            raise ValueError(f"No message found from character {character_id}")
        
        # Find the event before this message
        event_index = event_history.index(last_message_event)
        if event_index > 0:
            previous_event = event_history[event_index - 1]
            return self.rollback_to_event(previous_event.id)
        else:
            # This was the first event, rollback to start
            self.state_machine.event_history = []
            return self.get_state()
    
    def edit_event(
        self,
        event_id: str,
        new_data: Optional[Dict[str, Any]] = None,
        new_state_diffs: Optional[List[StateDiff]] = None
    ) -> GameState:
        """
        Edit an event's data or state_diffs.
        After editing, recomputes the state by replaying all events.
        
        Args:
            event_id: ID of the event to edit
            new_data: New data for the event (optional)
            new_state_diffs: New state_diffs for the event (optional)
        
        Returns:
            Updated game state
        """
        # Find the event
        event_history = self.get_event_history()
        event_index = None
        for i, event in enumerate(event_history):
            if event.id == event_id:
                event_index = i
                break
        
        if event_index is None:
            raise ValueError(f"Event {event_id} not found")
        
        # Get the event
        event = event_history[event_index]
        
        # Update event data
        if new_data is not None:
            event.data = new_data
        
        if new_state_diffs is not None:
            event.state_diffs = new_state_diffs
        
        # Recompute state by replaying all events
        return self.state_machine.get_current_state()
    
    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Get an event by its ID.
        
        Args:
            event_id: ID of the event
        
        Returns:
            Event if found, None otherwise
        """
        event_history = self.get_event_history()
        for event in event_history:
            if event.id == event_id:
                return event
        return None
    
    def find_events_by_type(self, event_type: EventType) -> List[Event]:
        """
        Find all events of a specific type.
        
        Args:
            event_type: Type of events to find
        
        Returns:
            List of matching events
        """
        event_history = self.get_event_history()
        return [e for e in event_history if e.type == event_type]
    
    def find_events_by_actor(self, actor_id: str) -> List[Event]:
        """
        Find all events by a specific actor.
        
        Args:
            actor_id: ID of the actor
        
        Returns:
            List of matching events
        """
        event_history = self.get_event_history()
        return [e for e in event_history if e.actor_id == actor_id]
