"""Tests for prompt renderer"""

import pytest
from trpg_llm.core.prompt_renderer import PromptRenderer
from trpg_llm.models.game_state import GameState, GameConfig
from trpg_llm.models.character import Character, CharacterType, CharacterControlType


class TestPromptRenderer:
    """Test PromptRenderer functionality"""
    
    def test_simple_render(self):
        """Test rendering a simple template"""
        renderer = PromptRenderer()
        
        template = "Hello {{ name }}!"
        context = {"name": "World"}
        
        result = renderer.render(template, context)
        
        assert result == "Hello World!"
    
    def test_render_with_conditionals(self):
        """Test rendering with conditionals"""
        renderer = PromptRenderer()
        
        template = """
        {% if active %}
        System is active
        {% else %}
        System is inactive
        {% endif %}
        """
        
        result = renderer.render(template, {"active": True})
        assert "active" in result
        
        result = renderer.render(template, {"active": False})
        assert "inactive" in result
    
    def test_render_with_loops(self):
        """Test rendering with loops"""
        renderer = PromptRenderer()
        
        template = """
        {% for item in items %}
        - {{ item }}
        {% endfor %}
        """
        
        result = renderer.render(template, {"items": ["a", "b", "c"]})
        
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result
    
    def test_render_with_game_state(self):
        """Test rendering with game state hydration"""
        renderer = PromptRenderer()
        
        # Create a minimal game config and state
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={
                "player1": {
                    "id": "player1",
                    "name": "Hero",
                    "type": "player",
                    "control": "human"
                }
            }
        )
        
        game_state = GameState(
            session_id="test",
            config=config,
            current_turn=1
        )
        
        template = """
        Game: {{ game_name }}
        Turn: {{ current_turn }}
        """
        
        result = renderer.render_with_game_state(template, game_state)
        
        assert "Test Game" in result
        assert "1" in result
    
    def test_format_character_filter(self):
        """Test custom character formatting filter"""
        renderer = PromptRenderer()
        
        template = "{{ character | format_character }}"
        
        context = {
            "character": {
                "name": "Test Hero",
                "type": "player",
                "attributes": {"strength": 15},
                "state": {"hp": 20}
            }
        }
        
        result = renderer.render(template, context)
        
        assert "Test Hero" in result
        assert "strength=15" in result
        assert "hp=20" in result
    
    def test_format_state_filter(self):
        """Test custom state formatting filter"""
        renderer = PromptRenderer()
        
        template = "{{ state | format_state }}"
        
        context = {
            "state": {
                "location": "Village",
                "time": "Morning",
                "weather": "Sunny"
            }
        }
        
        result = renderer.render(template, context)
        
        assert "location: Village" in result
        assert "time: Morning" in result
    
    def test_template_syntax_error(self):
        """Test handling of template syntax errors"""
        renderer = PromptRenderer()
        
        template = "{{ unclosed"
        
        with pytest.raises(ValueError, match="Template syntax error"):
            renderer.render(template, {})
    
    def test_hydrate_game_state(self):
        """Test state hydration"""
        renderer = PromptRenderer()
        
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            description="A test game",
            characters={
                "player1": Character(
                    id="player1",
                    name="Hero",
                    type=CharacterType.PLAYER,
                    control=CharacterControlType.HUMAN,
                    attributes={"str": 15},
                    state={"hp": 20}
                )
            }
        )
        
        game_state = GameState(
            session_id="test",
            config=config,
            state={"location": "Village"},
            current_turn=5,
            characters={
                "player1": Character(
                    id="player1",
                    name="Hero",
                    type=CharacterType.PLAYER,
                    control=CharacterControlType.HUMAN,
                    attributes={"str": 15},
                    state={"hp": 20}
                )
            }
        )
        
        context = renderer._hydrate_game_state(game_state)
        
        assert context["game_name"] == "Test Game"
        assert context["rule_system"] == "generic"
        assert context["current_turn"] == 5
        assert "player1" in context["characters"]
        assert context["characters"]["player1"]["name"] == "Hero"
        assert context["state"]["location"] == "Village"
    
    def test_default_prompt_creation(self):
        """Test default prompt creation"""
        renderer = PromptRenderer()
        
        config = GameConfig(
            name="Test Game",
            rule_system="generic",
            characters={}
        )
        
        game_state = GameState(
            session_id="test",
            config=config
        )
        
        prompt = renderer.create_default_prompt("player", game_state, "What do you do?")
        
        assert "Test Game" in prompt
        assert "What do you do?" in prompt
