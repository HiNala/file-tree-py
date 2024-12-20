import json
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class FileTreeConfig:
    """Configuration for file tree analysis."""

    def __init__(self, 
                 similarity_threshold: float = 0.8,
                 ignore_patterns: List[str] = None,
                 file_annotations: dict = None,
                 num_workers: int = None,
                 max_depth: int = None,
                 debug_mode: bool = False):
        """Initialize configuration with default values."""
        self.similarity_threshold = similarity_threshold
        self.ignore_patterns = ignore_patterns or ["__pycache__", "*.pyc", "*.pyo", "*.pyd"]
        self.file_annotations = file_annotations or {
            ".py": "[yellow](Python)[/yellow]",
            ".js": "[yellow](JavaScript)[/yellow]",
            ".html": "[blue](HTML)[/blue]",
            ".css": "[blue](CSS)[/blue]",
            ".md": "[green](Markdown)[/green]",
            ".json": "[yellow](JSON)[/yellow]",
            ".yml": "[yellow](YAML)[/yellow]",
            ".yaml": "[yellow](YAML)[/yellow]",
        }
        self.num_workers = num_workers if num_workers is not None else os.cpu_count()
        self.max_depth = max_depth  # None means no depth limit
        self.debug_mode = debug_mode

    def __str__(self) -> str:
        """Return a string representation of the configuration."""
        return (
            f"FileTreeConfig(similarity_threshold={self.similarity_threshold}, "
            f"num_workers={self.num_workers}, max_depth={self.max_depth}, "
            f"debug_mode={self.debug_mode})"
        )

    @classmethod
    def default(cls) -> "FileTreeConfig":
        """Create a configuration with default values."""
        return cls()

    @classmethod
    def from_file(cls, config_file: Path) -> "FileTreeConfig":
        """Load configuration from a JSON file."""
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            logger.error(f"Error loading config from {config_file}: {e}")
            return cls.default()