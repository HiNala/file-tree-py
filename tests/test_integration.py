"""Integration tests for the file tree analyzer."""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
from filetree.cli import main

@pytest.fixture
def mock_file_tree():
    """Create a mock file tree for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create some test files
        (root / "file1.txt").write_text("content1")
        (root / "file2.txt").write_text("content1")  # Duplicate
        
        # Create subdirectory with more files
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content2")
        (subdir / "file4.txt").write_text("content2")  # Duplicate
        
        yield root

@pytest.fixture
def mock_config_file(mock_file_tree):
    """Create a mock configuration file."""
    config_file = mock_file_tree / "config.json"
    config_data = {
        "ignore_patterns": ["*.tmp", "*.log"],
        "follow_symlinks": True,
        "min_file_size": 1000,
        "max_depth": 5,
        "include_hidden": True,
        "use_color": False,
        "output_format": "json"
    }
    config_file.write_text(json.dumps(config_data))
    return config_file

def test_cli_basic_scan(mock_file_tree):
    """Test basic file tree scanning."""
    with patch('sys.argv', ['script.py', str(mock_file_tree), '--no-tree']):
        assert main() == 0

def test_cli_with_duplicates(mock_file_tree):
    """Test scanning with duplicate files."""
    with patch('sys.argv', ['script.py', str(mock_file_tree), '--no-tree']):
        assert main() == 0

def test_cli_export(mock_file_tree):
    """Test export functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        export_path = Path(tmp_dir) / "report.md"
        with patch('sys.argv', ['script.py', str(mock_file_tree), '--export', str(export_path)]):
            assert main() == 0
            assert export_path.exists()

def test_cli_min_size(mock_file_tree):
    """Test minimum file size option."""
    with patch('sys.argv', ['script.py', str(mock_file_tree), '--min-size', '1000']):
        assert main() == 0

def test_cli_exclude_patterns(mock_file_tree):
    """Test exclude patterns option."""
    with patch('sys.argv', ['script.py', str(mock_file_tree), '--exclude', '*.tmp', '*.log']):
        assert main() == 0

def test_cli_invalid_directory():
    """Test handling of invalid directory."""
    nonexistent = str(Path("/nonexistent"))
    with patch('sys.argv', ['script.py', nonexistent]):
        assert main() == 1