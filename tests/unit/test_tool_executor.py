"""Tests for tool executor"""

import pytest
from trpg_llm.core.tool_executor import ToolRegistry, ToolExecutor


class TestToolRegistry:
    """Test ToolRegistry functionality"""
    
    def test_register_function(self):
        """Test registering a function"""
        registry = ToolRegistry()
        
        def test_func(args, context):
            return {"result": "success"}
        
        registry.register_function("test", test_func)
        
        assert "test" in registry.list_tools()
        assert registry.get_tool("test") == test_func
    
    def test_register_with_decorator(self):
        """Test registering with decorator"""
        registry = ToolRegistry()
        
        @registry.register("decorated_tool")
        def decorated_func(args, context):
            return {"result": "decorated"}
        
        assert "decorated_tool" in registry.list_tools()
        assert registry.get_tool("decorated_tool") is not None
    
    def test_register_with_schema(self):
        """Test registering with schema"""
        registry = ToolRegistry()
        
        schema = {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {}
            }
        }
        
        def test_func(args, context):
            return {"result": "ok"}
        
        registry.register_function("test_tool", test_func, schema)
        
        assert registry.get_schema("test_tool") == schema
        assert len(registry.get_all_schemas()) == 1


class TestToolExecutor:
    """Test ToolExecutor functionality"""
    
    def test_execute_simple_tool(self):
        """Test executing a simple tool"""
        registry = ToolRegistry()
        
        def simple_tool(args, context):
            return {"result": args.get("input") * 2}
        
        registry.register_function("double", simple_tool)
        executor = ToolExecutor(registry)
        
        result = executor.execute_tool_call(
            "double",
            {"input": 5},
            {}
        )
        
        assert result["success"] is True
        assert result["result"] == 10  # Tool returned {"result": 10}, so we extract 10
    
    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist"""
        registry = ToolRegistry()
        executor = ToolExecutor(registry)
        
        result = executor.execute_tool_call(
            "nonexistent",
            {},
            {}
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_execute_tool_with_error(self):
        """Test executing a tool that raises an error"""
        registry = ToolRegistry()
        
        def error_tool(args, context):
            raise ValueError("Test error")
        
        registry.register_function("error", error_tool)
        executor = ToolExecutor(registry)
        
        result = executor.execute_tool_call(
            "error",
            {},
            {}
        )
        
        assert result["success"] is False
        assert "Test error" in result["error"]
    
    def test_execute_tool_with_state_diffs(self):
        """Test tool that returns state_diffs"""
        registry = ToolRegistry()
        
        def state_change_tool(args, context):
            return {
                "result": "changed",
                "state_diffs": [
                    {"path": "test.value", "operation": "set", "value": 42}
                ]
            }
        
        registry.register_function("state_change", state_change_tool)
        executor = ToolExecutor(registry)
        
        result = executor.execute_tool_call(
            "state_change",
            {},
            {}
        )
        
        assert result["success"] is True
        assert len(result["state_diffs"]) == 1
        assert result["state_diffs"][0]["value"] == 42
    
    def test_execute_multiple_tool_calls(self):
        """Test executing multiple tool calls"""
        registry = ToolRegistry()
        
        def add_tool(args, context):
            return {"result": args["a"] + args["b"]}
        
        registry.register_function("add", add_tool)
        executor = ToolExecutor(registry)
        
        tool_calls = [
            {
                "id": "call1",
                "type": "function",
                "function": {
                    "name": "add",
                    "arguments": '{"a": 1, "b": 2}'
                }
            },
            {
                "id": "call2",
                "type": "function",
                "function": {
                    "name": "add",
                    "arguments": '{"a": 3, "b": 4}'
                }
            }
        ]
        
        results = executor.execute_tool_calls(tool_calls, {})
        
        assert len(results) == 2
        assert results[0]["result"] == 3
        assert results[1]["result"] == 7
    
    def test_format_tool_results_for_llm(self):
        """Test formatting tool results for LLM"""
        registry = ToolRegistry()
        executor = ToolExecutor(registry)
        
        results = [
            {
                "tool_call_id": "call1",
                "success": True,
                "result": "test result",
                "state_diffs": []
            },
            {
                "tool_call_id": "call2",
                "success": False,
                "error": "test error"
            }
        ]
        
        formatted = executor.format_tool_results_for_llm(results)
        
        assert len(formatted) == 2
        assert formatted[0]["role"] == "tool"
        assert formatted[0]["tool_call_id"] == "call1"
        assert "test result" in formatted[0]["content"]
        assert "test error" in formatted[1]["content"]
