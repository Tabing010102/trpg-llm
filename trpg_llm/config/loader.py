"""Configuration loader for YAML/JSON configs"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Union

from ..models.game_state import GameConfig


class ConfigLoader:
    """
    Load and validate game configuration from YAML or JSON files.
    """
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> GameConfig:
        """
        Load configuration from a YAML or JSON file.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse based on extension
        if file_path.suffix in ['.yaml', '.yml']:
            config_dict = yaml.safe_load(content)
        elif file_path.suffix == '.json':
            config_dict = json.loads(content)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Validate and create GameConfig
        return GameConfig(**config_dict)
    
    @staticmethod
    def load_from_dict(config_dict: Dict[str, Any]) -> GameConfig:
        """
        Load configuration from a dictionary.
        """
        return GameConfig(**config_dict)
    
    @staticmethod
    def load_from_string(config_str: str, format: str = "yaml") -> GameConfig:
        """
        Load configuration from a string.
        
        Args:
            config_str: Configuration string
            format: "yaml" or "json"
        """
        if format.lower() == "yaml":
            config_dict = yaml.safe_load(config_str)
        elif format.lower() == "json":
            config_dict = json.loads(config_str)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return GameConfig(**config_dict)
    
    @staticmethod
    def save_to_file(config: GameConfig, file_path: Union[str, Path]) -> None:
        """
        Save configuration to a YAML or JSON file.
        """
        file_path = Path(file_path)
        
        # Convert to dict
        config_dict = config.dict()
        
        # Write based on extension
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif file_path.suffix == '.json':
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
