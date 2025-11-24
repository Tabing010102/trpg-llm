"""Prompt rendering system with Jinja2 support"""

from typing import Dict, Any, Optional
from jinja2 import Environment, Template, TemplateSyntaxError
from ..models.game_state import GameState


class PromptRenderer:
    """
    Renders prompts using Jinja2 templates.
    Supports hydrating game state into prompt templates.
    """
    
    def __init__(self):
        self.env = Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['format_character'] = self._format_character
        self.env.filters['format_state'] = self._format_state
    
    def render(
        self,
        template_str: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a prompt template with given context.
        
        Args:
            template_str: Jinja2 template string
            context: Context variables for rendering
        
        Returns:
            Rendered prompt string
        """
        try:
            template = self.env.from_string(template_str)
            return template.render(**context)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Template rendering failed: {str(e)}")
    
    def render_with_game_state(
        self,
        template_str: str,
        game_state: GameState,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render a prompt with game state hydration.
        
        Args:
            template_str: Jinja2 template string
            game_state: Current game state
            additional_context: Additional context variables
        
        Returns:
            Rendered prompt string
        """
        # Build context from game state
        context = self._hydrate_game_state(game_state)
        
        # Merge additional context
        if additional_context:
            context.update(additional_context)
        
        return self.render(template_str, context)
    
    def _hydrate_game_state(self, game_state: GameState) -> Dict[str, Any]:
        """Convert game state to template context"""
        return {
            "session_id": game_state.session_id,
            "game_name": game_state.config.name,
            "rule_system": game_state.config.rule_system,
            "description": game_state.config.description,
            "state": game_state.state,
            "characters": {
                char_id: {
                    "id": char.id,
                    "name": char.name,
                    "type": char.type.value if hasattr(char.type, 'value') else char.type,
                    "control": char.control.value if hasattr(char.control, 'value') else char.control,
                    "attributes": char.attributes,
                    "state": char.state,
                    "description": char.description,
                    "background": char.background,
                }
                for char_id, char in game_state.characters.items()
            },
            "current_turn": game_state.current_turn,
            "current_phase": game_state.current_phase,
            "current_actor": game_state.current_actor,
            "messages": game_state.messages,
            "recent_messages": game_state.messages[-10:] if game_state.messages else [],
        }
    
    def _format_character(self, character_data: Dict[str, Any]) -> str:
        """Custom filter to format character information"""
        lines = [
            f"Name: {character_data.get('name', 'Unknown')}",
            f"Type: {character_data.get('type', 'unknown')}",
        ]
        
        if character_data.get('description'):
            lines.append(f"Description: {character_data['description']}")
        
        if character_data.get('attributes'):
            attrs = ", ".join(
                f"{k}={v}" for k, v in character_data['attributes'].items()
            )
            lines.append(f"Attributes: {attrs}")
        
        if character_data.get('state'):
            state = ", ".join(
                f"{k}={v}" for k, v in character_data['state'].items()
            )
            lines.append(f"State: {state}")
        
        return "\n  ".join(lines)
    
    def _format_state(self, state_data: Dict[str, Any]) -> str:
        """Custom filter to format state information"""
        if not state_data:
            return "No state data"
        
        lines = []
        for key, value in state_data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{key}: {type(value).__name__}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n  ".join(lines)
    
    def create_default_prompt(
        self,
        role: str,
        game_state: GameState,
        user_message: Optional[str] = None
    ) -> str:
        """
        Create a default prompt for a role.
        
        Args:
            role: Character role (gm, player, npc)
            game_state: Current game state
            user_message: Optional user message to include
        
        Returns:
            Formatted prompt string
        """
        template = """
Game: {{ game_name }} ({{ rule_system }})
{% if description %}{{ description }}{% endif %}

Current Turn: {{ current_turn }}
{% if current_phase %}Phase: {{ current_phase }}{% endif %}

{% if characters %}
Characters:
{% for char_id, char in characters.items() %}
- {{ char | format_character | indent(2) }}
{% endfor %}
{% endif %}

{% if state %}
Global State:
  {{ state | format_state | indent(2) }}
{% endif %}

{% if recent_messages %}
Recent Events:
{% for msg in recent_messages %}
- {{ msg.sender_id }}: {{ msg.content }}
{% endfor %}
{% endif %}

{% if user_message %}
Current Situation:
{{ user_message }}
{% endif %}
"""
        
        context = self._hydrate_game_state(game_state)
        context["user_message"] = user_message
        
        return self.render(template, context)
