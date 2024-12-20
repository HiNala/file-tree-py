"""Tests for the file scanner module."""
import os
import tempfile
from pathlib import Path
import pytest
from filetree.core.scanner import FileScanner
from filetree.utils.config import FileTreeConfig
from unittest.mock import patch, MagicMock

@pytest.fixture
def scanner():
    """Create a scanner instance for testing."""
    config = FileTreeConfig()
    return FileScanner(config, num_workers=2)

def test_scanner_initialization():
    """Test scanner initialization."""
    config = FileTreeConfig()
    scanner = FileScanner(config, num_workers=4)
    assert scanner.config == config
    assert scanner.processor is not None

def test_find_duplicates(scanner, tmp_path):
    """Test finding duplicate files."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("test content")
    file2.write_text("test content")

    # Mock the parallel processor
    mock_processor = MagicMock()
    mock_processor.find_duplicates.return_value = {
        "hash1": [file1, file2]
    }
    scanner.processor = mock_processor

    duplicates = scanner.find_duplicates(tmp_path)
    assert len(duplicates) == 1
    assert len(duplicates["hash1"]) == 2
    
    # The processor's find_duplicates should be called with a set containing both files
    expected_files = {file1, file2}
    mock_processor.find_duplicates.assert_called_once()
    actual_files = mock_processor.find_duplicates.call_args[0][0]
    assert isinstance(actual_files, set)
    assert actual_files == expected_files

def test_scan_directory(scanner, tmp_path):
    """Test scanning directory."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    files = scanner.scan_directory(tmp_path)
    assert len(files) == 2
    assert file1 in files
    assert file2 in files

def test_scanner_error_handling(scanner):
    """Test error handling in scanner."""
    # Test with non-existent directory
    duplicates = scanner.find_duplicates(Path("\\nonexistent"))
    assert duplicates == {}