import json
import logging
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration for file tree analysis."""

    # File patterns to ignore
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "*.egg",
        "*.egg-info",
        "*.pyc",
        "__pycache__",
        "*.git",
        "*.svn",
        "*.hg",
        "*.DS_Store",
        "node_modules",
        "venv",
        ".env",
        ".venv",
        "build",
        "dist",
        "*.tmp",
        "*.temp",
        "*.swp",
        "*.bak",
        "Thumbs.db"
    ])

    # Whether to follow symbolic links
    follow_symlinks: bool = False

    # Minimum file size to consider (in bytes)
    min_file_size: int = 1

    # Maximum depth for directory traversal (None for unlimited)
    max_depth: int = None

    # Whether to include hidden files
    include_hidden: bool = False

    # Whether to use color output
    use_color: bool = True

    # Output format (text, json, or markdown)
    output_format: str = "text"

    @classmethod
    def from_file(cls, config_file: Path) -> "Config":
        """Load configuration from a JSON file."""
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            raise Exception(f"Error loading configuration from {config_file}: {str(e)}")

    def to_file(self, config_file: Path) -> None:
        """Save configuration to a JSON file."""
        try:
            config_data = {
                "ignore_patterns": self.ignore_patterns,
                "follow_symlinks": self.follow_symlinks,
                "min_file_size": self.min_file_size,
                "max_depth": self.max_depth,
                "include_hidden": self.include_hidden,
                "use_color": self.use_color,
                "output_format": self.output_format
            }
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            raise Exception(f"Error saving configuration to {config_file}: {str(e)}")

    def update(self, **kwargs) -> None:
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid configuration option: {key}")

    def get_ignore_patterns(self) -> List[str]:
        """Get list of ignore patterns."""
        patterns = self.ignore_patterns.copy()
        if not self.include_hidden:
            patterns.extend([".*", ".*/*"])
        return patterns