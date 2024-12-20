import pytest
from pathlib import Path
import json
from filetree.cli import main

def test_cli_basic_scan(mock_file_tree, capsys):
    """Test basic CLI functionality."""
    args = ["--no-tree", str(mock_file_tree)]
    exit_code = main(args)
    
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Scanning directory" in captured.out
    assert "helper.py" in captured.out  # Should mention duplicate file

def test_cli_export(mock_file_tree, temp_dir):
    """Test export functionality."""
    export_file = temp_dir / "results.json"
    args = [
        "--no-tree",
        "--export", str(export_file),
        str(mock_file_tree)
    ]
    
    exit_code = main(args)
    assert exit_code == 0
    assert export_file.exists()
    
    # Verify export contents
    with open(export_file) as f:
        results = json.load(f)
    
    # Check for summary information
    assert "summary" in results
    assert "total_groups" in results["summary"]
    assert "total_duplicates" in results["summary"]
    assert "total_wasted_space" in results["summary"]
    
    # Check for at least one hash key (representing duplicates)
    assert any(key != "summary" for key in results.keys())

def test_cli_with_config(mock_file_tree, mock_config_file):
    """Test CLI with configuration file."""
    args = [
        "--no-tree",
        "--config", str(mock_config_file),
        str(mock_file_tree)
    ]
    
    exit_code = main(args)
    assert exit_code == 0

def test_cli_invalid_directory(temp_dir):
    """Test CLI behavior with invalid directory."""
    invalid_dir = temp_dir / "nonexistent"
    args = [str(invalid_dir)]
    
    exit_code = main(args)
    assert exit_code == 1  # Should exit with error 