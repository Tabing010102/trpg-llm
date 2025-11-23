"""Tests for state machine and event sourcing"""

import pytest
from datetime import datetime, timedelta

from trpg_llm.state.state_machine import StateMachine
from trpg_llm.models.game_state import GameConfig
from trpg_llm.models.event import Event, EventType, StateDiff


class TestStateMachine:
    """Test state machine functionality"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return GameConfig(
            name="Test Game",
            rule_system="test",
            initial_state={
                "counter": 0,
                "items": [],
            },
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Test Player",
                    "type": "player",
                    "control": "human",
                },
            },
        )
    
    @pytest.fixture
    def state_machine(self, config):
        """Create test state machine"""
        return StateMachine("test-session", config)
    
    def test_initialization(self, state_machine, config):
        """Test state machine initialization"""
        assert state_machine.session_id == "test-session"
        assert state_machine.config == config
        assert len(state_machine.event_history) == 0
    
    def test_get_initial_state(self, state_machine):
        """Test getting initial state"""
        state = state_machine.get_current_state()
        
        assert state.session_id == "test-session"
        assert state.state["counter"] == 0
        assert state.state["items"] == []
        assert "player1" in state.characters
    
    def test_add_event(self, state_machine):
        """Test adding an event"""
        event = state_machine.create_event(
            event_type=EventType.ACTION,
            actor_id="player1",
            data={"action": "test"},
        )
        
        state = state_machine.add_event(event)
        
        assert len(state_machine.event_history) == 1
        assert state_machine.event_history[0].type == EventType.ACTION
    
    def test_state_diff_set(self, state_machine):
        """Test SET operation in state diff"""
        diff = StateDiff(path="counter", operation="set", value=10)
        event = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[diff],
        )
        
        state = state_machine.add_event(event)
        
        assert state.state["counter"] == 10
    
    def test_state_diff_add(self, state_machine):
        """Test ADD operation in state diff"""
        diff1 = StateDiff(path="counter", operation="set", value=5)
        diff2 = StateDiff(path="counter", operation="add", value=3)
        
        state_machine.add_event(
            state_machine.create_event(
                event_type=EventType.STATE_UPDATE,
                state_diffs=[diff1],
            )
        )
        state = state_machine.add_event(
            state_machine.create_event(
                event_type=EventType.STATE_UPDATE,
                state_diffs=[diff2],
            )
        )
        
        assert state.state["counter"] == 8
    
    def test_state_diff_append(self, state_machine):
        """Test APPEND operation in state diff"""
        diff = StateDiff(path="items", operation="append", value="sword")
        event = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[diff],
        )
        
        state = state_machine.add_event(event)
        
        assert "sword" in state.state["items"]
        assert len(state.state["items"]) == 1
    
    def test_event_replay(self, state_machine):
        """Test that state is computed correctly from event history"""
        # Add multiple events
        events = [
            state_machine.create_event(
                event_type=EventType.STATE_UPDATE,
                state_diffs=[StateDiff(path="counter", operation="set", value=1)],
            ),
            state_machine.create_event(
                event_type=EventType.STATE_UPDATE,
                state_diffs=[StateDiff(path="counter", operation="add", value=2)],
            ),
            state_machine.create_event(
                event_type=EventType.STATE_UPDATE,
                state_diffs=[StateDiff(path="counter", operation="add", value=3)],
            ),
        ]
        
        for event in events:
            state_machine.add_event(event)
        
        # Get state should replay all events
        state = state_machine.get_current_state()
        assert state.state["counter"] == 6
    
    def test_rollback_to_event(self, state_machine):
        """Test rollback to specific event"""
        # Add events
        event1 = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[StateDiff(path="counter", operation="set", value=5)],
        )
        state_machine.add_event(event1)
        
        event2 = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[StateDiff(path="counter", operation="add", value=10)],
        )
        state_machine.add_event(event2)
        
        # Rollback to first event
        state = state_machine.rollback_to(event1.id)
        
        assert state.state["counter"] == 5
        assert len(state_machine.event_history) == 1
    
    def test_rollback_to_timestamp(self, state_machine):
        """Test rollback to specific timestamp"""
        # Add event at current time
        event1 = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[StateDiff(path="counter", operation="set", value=5)],
        )
        state_machine.add_event(event1)
        
        # Remember timestamp
        cutoff_time = datetime.utcnow()
        
        # Add event in the future (simulate)
        event2 = state_machine.create_event(
            event_type=EventType.STATE_UPDATE,
            state_diffs=[StateDiff(path="counter", operation="add", value=10)],
        )
        event2.timestamp = cutoff_time + timedelta(seconds=1)
        state_machine.add_event(event2)
        
        # Rollback to cutoff time
        state = state_machine.rollback_to_timestamp(cutoff_time)
        
        assert state.state["counter"] == 5
        assert len(state_machine.event_history) == 1
