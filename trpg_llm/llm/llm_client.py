"""LLM client wrapper using LiteLLM"""

from typing import Dict, Any, List, Optional
import json

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class LLMClient:
    """
    Wrapper for LiteLLM to support multiple LLM providers.
    Supports OpenAI, Anthropic, Azure, Cohere, etc.
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM is not installed. Install it with: pip install litellm"
            )
        
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get completion from LLM.
        """
        completion_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **self.kwargs,
            **kwargs,
        }
        
        if max_tokens:
            completion_kwargs["max_tokens"] = max_tokens
        
        if tools:
            completion_kwargs["tools"] = tools
            completion_kwargs["tool_choice"] = "auto"
        
        if self.api_key:
            completion_kwargs["api_key"] = self.api_key
        
        if self.base_url:
            completion_kwargs["api_base"] = self.base_url
        
        try:
            response = await litellm.acompletion(**completion_kwargs)
            return self._format_response(response)
        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "tool_calls": None,
            }
    
    def complete_sync(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous version of complete.
        """
        completion_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **self.kwargs,
            **kwargs,
        }
        
        if max_tokens:
            completion_kwargs["max_tokens"] = max_tokens
        
        if tools:
            completion_kwargs["tools"] = tools
            completion_kwargs["tool_choice"] = "auto"
        
        if self.api_key:
            completion_kwargs["api_key"] = self.api_key
        
        if self.base_url:
            completion_kwargs["api_base"] = self.base_url
        
        try:
            response = litellm.completion(**completion_kwargs)
            return self._format_response(response)
        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "tool_calls": None,
            }
    
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Format LiteLLM response into standard format"""
        try:
            choice = response.choices[0]
            message = choice.message
            
            result = {
                "content": message.content if hasattr(message, "content") else None,
                "tool_calls": [],
                "finish_reason": choice.finish_reason,
            }
            
            # Extract tool calls if present
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    })
            
            return result
        except Exception as e:
            return {
                "error": f"Failed to format response: {str(e)}",
                "content": None,
                "tool_calls": None,
            }
