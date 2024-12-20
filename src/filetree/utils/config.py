import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FileTreeConfig:
    """Configuration settings for the file tree analyzer."""
    similarity_threshold: float = 0.8
    ignore_patterns: list[str] = None
    file_annotations: Dict[str, str] = None
    debug_mode: bool = False
    
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
    def default(cls) -> 'FileTreeConfig':
        """Create default configuration."""
        return cls(
            similarity_threshold=0.8,
            ignore_patterns=[
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
            ],
            file_annotations={
                ".py": "[yellow](Python)[/yellow]",
                ".md": "[green](Markdown)[/green]",
                ".json": "[blue](JSON)[/blue]",
                ".yml": "[blue](YAML)[/blue]",
                ".txt": "[white](Text)[/white]",
            },
            debug_mode=False
        ) 