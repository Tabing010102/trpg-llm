"""State operations and atomic updates"""

from typing import Any, Dict
from enum import Enum
import copy


class StateOperation(str, Enum):
    """Supported state operations"""
    SET = "set"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    APPEND = "append"
    REMOVE = "remove"
    DELETE = "delete"


def get_nested_value(state: Dict[str, Any], path: str) -> Any:
    """Get value from nested dictionary using dot notation path"""
    keys = path.split(".")
    value = state
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdigit():
            idx = int(key)
            value = value[idx] if idx < len(value) else None
        else:
            return None
    
    return value


def set_nested_value(state: Dict[str, Any], path: str, value: Any) -> None:
    """Set value in nested dictionary using dot notation path"""
    keys = path.split(".")
    target = state
    
    # Navigate to parent
    for key in keys[:-1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    
    # Set final value
    target[keys[-1]] = value


def apply_state_diff(state: Dict[str, Any], path: str, operation: str, value: Any) -> Any:
    """
    Apply a state diff operation to the state.
    Returns the previous value.
    """
    previous_value = get_nested_value(state, path)
    
    if operation == StateOperation.SET:
        set_nested_value(state, path, value)
    
    elif operation == StateOperation.ADD:
        current = get_nested_value(state, path)
        if current is None:
            current = 0
        set_nested_value(state, path, current + value)
    
    elif operation == StateOperation.SUBTRACT:
        current = get_nested_value(state, path)
        if current is None:
            current = 0
        set_nested_value(state, path, current - value)
    
    elif operation == StateOperation.MULTIPLY:
        current = get_nested_value(state, path)
        if current is None:
            current = 1
        set_nested_value(state, path, current * value)
    
    elif operation == StateOperation.APPEND:
        current = get_nested_value(state, path)
        if current is None:
            current = []
        if isinstance(current, list):
            current.append(value)
            set_nested_value(state, path, current)
    
    elif operation == StateOperation.REMOVE:
        current = get_nested_value(state, path)
        if current is not None and isinstance(current, list):
            if value in current:
                current.remove(value)
                set_nested_value(state, path, current)
    
    elif operation == StateOperation.DELETE:
        keys = path.split(".")
        target = state
        for key in keys[:-1]:
            if key in target:
                target = target[key]
            else:
                return previous_value
        
        if keys[-1] in target:
            del target[keys[-1]]
    
    return previous_value
