"""Tool execution system for function calling"""

from typing import Dict, Any, Callable, List, Optional
import json
from functools import wraps

from ..models.event import StateDiff


class ToolRegistry:
    """Registry for tool functions that can be called by LLM"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self,
        name: str,
        schema: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to register a tool function.
        
        Args:
            name: Name of the tool
            schema: OpenAI function calling schema for the tool
        """
        def decorator(func: Callable) -> Callable:
            self._tools[name] = func
            if schema:
                self._tool_schemas[name] = schema
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def register_function(
        self,
        name: str,
        func: Callable,
        schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool function directly"""
        self._tools[name] = func
        if schema:
            self._tool_schemas[name] = schema
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a registered tool by name"""
        return self._tools.get(name)
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool schema by name"""
        return self._tool_schemas.get(name)
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all registered tool schemas"""
        return list(self._tool_schemas.values())
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())


class ToolExecutor:
    """
    Executes tool calls from LLM responses.
    Dispatches to registered functions and returns results.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single tool call.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            context: Additional context (e.g., game_engine, game_state)
        
        Returns:
            Result dictionary with success status, result, and any state_diffs
        """
        tool_func = self.registry.get_tool(tool_name)
        
        if not tool_func:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "result": None,
                "state_diffs": []
            }
        
        try:
            # Execute the tool with context (always pass both arguments)
            result = tool_func(arguments, context if context is not None else {})
            
            # Normalize result format
            if isinstance(result, dict):
                # If result already has our expected keys, use it
                if "result" in result or "state_diffs" in result:
                    return {
                        "success": True,
                        "result": result.get("result"),
                        "state_diffs": result.get("state_diffs", []),
                        "error": None
                    }
                else:
                    # Otherwise, treat the whole dict as the result
                    return {
                        "success": True,
                        "result": result,
                        "state_diffs": [],
                        "error": None
                    }
            else:
                return {
                    "success": True,
                    "result": result,
                    "state_diffs": [],
                    "error": None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "state_diffs": []
            }
    
    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls from an LLM response.
        
        Args:
            tool_calls: List of tool calls from LLM
            context: Additional context for execution
        
        Returns:
            List of execution results
        """
        results = []
        
        for tool_call in tool_calls:
            # Extract tool information
            tool_id = tool_call.get("id")
            tool_type = tool_call.get("type", "function")
            
            if tool_type != "function":
                results.append({
                    "tool_call_id": tool_id,
                    "success": False,
                    "error": f"Unsupported tool type: {tool_type}",
                    "result": None,
                    "state_diffs": []
                })
                continue
            
            function_info = tool_call.get("function", {})
            function_name = function_info.get("name")
            
            # Parse arguments
            try:
                arguments_str = function_info.get("arguments", "{}")
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                else:
                    arguments = arguments_str
            except json.JSONDecodeError as e:
                results.append({
                    "tool_call_id": tool_id,
                    "success": False,
                    "error": f"Invalid JSON arguments: {str(e)}",
                    "result": None,
                    "state_diffs": []
                })
                continue
            
            # Execute the tool
            result = self.execute_tool_call(function_name, arguments, context)
            result["tool_call_id"] = tool_id
            results.append(result)
        
        return results
    
    def format_tool_results_for_llm(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format tool execution results for LLM consumption.
        Returns messages in OpenAI tool response format.
        """
        messages = []
        
        for result in results:
            tool_call_id = result.get("tool_call_id")
            
            if result.get("success"):
                content = json.dumps({
                    "result": result.get("result"),
                    "state_diffs": result.get("state_diffs", [])
                })
            else:
                content = json.dumps({
                    "error": result.get("error")
                })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content
            })
        
        return messages
