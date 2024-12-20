import pytest
from pathlib import Path
import tempfile
import shutil
import json

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_file_tree(temp_dir):
    """Create a mock file tree for testing."""
    # Create directories
    (temp_dir / "src" / "utils").mkdir(parents=True)
    (temp_dir / "lib" / "utils").mkdir(parents=True)
    (temp_dir / "tests").mkdir()
    
    # Create some files
    (temp_dir / "src" / "main.py").write_text("print('main')")
    (temp_dir / "src" / "utils" / "helper.py").write_text("def help(): pass")
    # Duplicate file
    (temp_dir / "lib" / "utils" / "helper.py").write_text("def help(): pass")
    (temp_dir / "README.md").write_text("# Test Project")
    
    # Create a symlink
    (temp_dir / "src" / "utils" / "link.py").symlink_to(temp_dir / "src" / "main.py")
    
    return temp_dir

@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock configuration file."""
    config = {
        "similarity_threshold": 0.9,
        "ignore_patterns": ["*.pyc", "__pycache__"],
        "file_annotations": {
            ".py": "[yellow](Python)[/yellow]",
            ".md": "[green](Markdown)[/green]"
        },
        "debug_mode": True
    }
    
    config_path = temp_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    return config_path 