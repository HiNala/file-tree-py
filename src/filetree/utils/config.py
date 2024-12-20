import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class FileTreeConfig:
    """Configuration for file tree analysis."""

    def __init__(self, similarity_threshold: float = 0.8, ignore_patterns: List[str] = None, file_annotations: dict = None):
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