"""Tests for the configuration module."""
import json
import tempfile
from pathlib import Path
import pytest
from filetree.utils.config import Config

@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "ignore_patterns": ["*.tmp", "*.log"],
            "follow_symlinks": True,
            "min_file_size": 1000,
            "max_depth": 5,
            "include_hidden": True,
            "use_color": False,
            "output_format": "json"
        }
        json.dump(config_data, f)
        return Path(f.name)

def test_default_config():
    """Test default configuration values."""
    config = Config()
    
    assert "*.egg" in config.ignore_patterns
    assert "*.pyc" in config.ignore_patterns
    assert not config.follow_symlinks
    assert config.min_file_size == 1
    assert config.max_depth is None
    assert not config.include_hidden
    assert config.use_color
    assert config.output_format == "text"

def test_config_from_file(temp_config_file):
    """Test loading configuration from file."""
    config = Config.from_file(temp_config_file)
    
    assert "*.tmp" in config.ignore_patterns
    assert "*.log" in config.ignore_patterns
    assert config.follow_symlinks
    assert config.min_file_size == 1000
    assert config.max_depth == 5
    assert config.include_hidden
    assert not config.use_color
    assert config.output_format == "json"

def test_config_to_file():
    """Test saving configuration to file."""
    config = Config()
    config.ignore_patterns = ["*.test"]
    config.follow_symlinks = True
    config.min_file_size = 500
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        config_file = Path(f.name)
    
    config.to_file(config_file)
    loaded_config = Config.from_file(config_file)
    
    assert loaded_config.ignore_patterns == ["*.test"]
    assert loaded_config.follow_symlinks
    assert loaded_config.min_file_size == 500

def test_config_update():
    """Test updating configuration values."""
    config = Config()
    config.update(
        follow_symlinks=True,
        min_file_size=2000,
        include_hidden=True
    )
    
    assert config.follow_symlinks
    assert config.min_file_size == 2000
    assert config.include_hidden

def test_config_invalid_update():
    """Test updating with invalid option."""
    config = Config()
    with pytest.raises(ValueError, match="Invalid configuration option: invalid_option"):
        config.update(invalid_option=True)

def test_config_get_ignore_patterns():
    """Test getting ignore patterns with hidden files."""
    config = Config()
    
    # When include_hidden is False
    patterns = config.get_ignore_patterns()
    assert ".*" in patterns
    assert ".*/*" in patterns
    
    # When include_hidden is True
    config.include_hidden = True
    patterns = config.get_ignore_patterns()
    assert ".*" not in patterns
    assert ".*/*" not in patterns