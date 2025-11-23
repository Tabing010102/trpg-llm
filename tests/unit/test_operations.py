"""Tests for state operations"""

import pytest
from trpg_llm.state.operations import (
    get_nested_value,
    set_nested_value,
    apply_state_diff,
    StateOperation,
)


class TestStateOperations:
    """Test state operation functions"""
    
    def test_get_nested_value_simple(self):
        """Test getting simple nested value"""
        state = {"a": {"b": {"c": 42}}}
        value = get_nested_value(state, "a.b.c")
        assert value == 42
    
    def test_get_nested_value_missing(self):
        """Test getting missing nested value"""
        state = {"a": {"b": 1}}
        value = get_nested_value(state, "a.c")
        assert value is None
    
    def test_set_nested_value(self):
        """Test setting nested value"""
        state = {"a": {}}
        set_nested_value(state, "a.b.c", 42)
        assert state["a"]["b"]["c"] == 42
    
    def test_apply_state_diff_set(self):
        """Test SET operation"""
        state = {"value": 0}
        prev = apply_state_diff(state, "value", StateOperation.SET, 10)
        
        assert state["value"] == 10
        assert prev == 0
    
    def test_apply_state_diff_add(self):
        """Test ADD operation"""
        state = {"counter": 5}
        apply_state_diff(state, "counter", StateOperation.ADD, 3)
        
        assert state["counter"] == 8
    
    def test_apply_state_diff_subtract(self):
        """Test SUBTRACT operation"""
        state = {"hp": 20}
        apply_state_diff(state, "hp", StateOperation.SUBTRACT, 5)
        
        assert state["hp"] == 15
    
    def test_apply_state_diff_multiply(self):
        """Test MULTIPLY operation"""
        state = {"damage": 10}
        apply_state_diff(state, "damage", StateOperation.MULTIPLY, 2)
        
        assert state["damage"] == 20
    
    def test_apply_state_diff_append(self):
        """Test APPEND operation"""
        state = {"items": ["sword"]}
        apply_state_diff(state, "items", StateOperation.APPEND, "shield")
        
        assert state["items"] == ["sword", "shield"]
    
    def test_apply_state_diff_remove(self):
        """Test REMOVE operation"""
        state = {"items": ["sword", "shield", "potion"]}
        apply_state_diff(state, "items", StateOperation.REMOVE, "shield")
        
        assert state["items"] == ["sword", "potion"]
    
    def test_apply_state_diff_delete(self):
        """Test DELETE operation"""
        state = {"a": 1, "b": 2}
        apply_state_diff(state, "b", StateOperation.DELETE, None)
        
        assert "b" not in state
        assert state["a"] == 1
    
    def test_apply_state_diff_nested(self):
        """Test operations on nested paths"""
        state = {"character": {"stats": {"hp": 20}}}
        apply_state_diff(state, "character.stats.hp", StateOperation.SUBTRACT, 5)
        
        assert state["character"]["stats"]["hp"] == 15
