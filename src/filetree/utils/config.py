import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .env import env_config

@dataclass
class FileTreeConfig:
    """Configuration settings for the file tree analyzer."""
    similarity_threshold: float = 0.8
    ignore_patterns: list[str] = None
    file_annotations: Dict[str, str] = None
    debug_mode: bool = False
    max_depth: int = 10
    include_hidden: bool = False
    output_format: str = 'tree'
    color_output: bool = True
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'FileTreeConfig':
        """Load configuration from a JSON file."""
        try:
            with open(config_path) as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config file ({e}), using defaults")
            return cls()
    
    @classmethod
    def from_env(cls) -> 'FileTreeConfig':
        """Create configuration from environment variables."""
        return cls(
            similarity_threshold=0.8,  # This could be added to env vars if needed
            ignore_patterns=env_config.get_exclude_patterns(),
            file_annotations={
                ".py": "[yellow](Python)[/yellow]",
                ".md": "[green](Markdown)[/green]",
                ".json": "[blue](JSON)[/blue]",
                ".yml": "[blue](YAML)[/blue]",
                ".txt": "[white](Text)[/white]",
            },
            debug_mode=env_config.get_debug_mode(),
            max_depth=env_config.get_max_depth(),
            include_hidden=env_config.get_include_hidden(),
            output_format=env_config.get_output_format(),
            color_output=env_config.get_color_output()
        )
    
    @classmethod
    def default(cls) -> 'FileTreeConfig':
        """Create default configuration."""
        return cls.from_env()  # Now using environment-based configuration by default