import pytest
from pathlib import Path
from filetree.utils.config import FileTreeConfig

def test_default_config():
    """Test default configuration values."""
    config = FileTreeConfig.default()
    
    assert config.similarity_threshold == 0.8
    assert "__pycache__" in config.ignore_patterns
    assert ".py" in config.file_annotations
    assert not config.debug_mode

def test_config_from_file(mock_config_file):
    """Test loading configuration from file."""
    config = FileTreeConfig.from_file(mock_config_file)
    
    assert config.similarity_threshold == 0.9
    assert "*.pyc" in config.ignore_patterns
    assert config.file_annotations[".py"] == "[yellow](Python)[/yellow]"
    assert config.debug_mode

def test_config_invalid_file(temp_dir):
    """Test handling of invalid configuration file."""
    invalid_file = temp_dir / "invalid.json"
    invalid_file.write_text("invalid json")
    
    config = FileTreeConfig.from_file(invalid_file)
    # Should fall back to defaults
    assert config.similarity_threshold == 0.8 