"""Tests for parallel processing utilities."""
import os
import tempfile
from pathlib import Path
import pytest
from filetree.utils.parallel import ParallelProcessor, compute_file_hash
from unittest.mock import patch, MagicMock

@pytest.fixture
def processor():
    """Create a parallel processor instance for testing."""
    return ParallelProcessor(num_workers=2)

def test_processor_initialization():
    """Test parallel processor initialization."""
    processor = ParallelProcessor(num_workers=4)
    assert processor.num_workers == 4

def test_compute_file_hash(tmp_path):
    """Test computing file hash."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    hash_value = compute_file_hash(test_file)
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 hash length

def test_find_duplicates(processor, tmp_path):
    """Test finding duplicate files."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"
    
    file1.write_text("test content")
    file2.write_text("test content")  # Duplicate of file1
    file3.write_text("different content")
    
    duplicates = processor.find_duplicates(tmp_path)
    assert len(duplicates) == 1  # One group of duplicates
    
    # Get the hash and files for the duplicate group
    hash_value = next(iter(duplicates))
    duplicate_files = duplicates[hash_value]
    
    assert len(duplicate_files) == 2
    assert file1 in duplicate_files
    assert file2 in duplicate_files
    assert file3 not in duplicate_files

def test_scan_directory(processor, tmp_path):
    """Test scanning directory."""
    # Create test files and directories
    file1 = tmp_path / "file1.txt"
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.txt"
    
    file1.write_text("content1")
    file2.write_text("content2")
    
    files = processor.scan_directory(tmp_path)
    assert len(files) == 2
    assert file1 in files
    assert file2 in files

def test_process_files(processor, tmp_path):
    """Test processing files in parallel."""
    # Create test files
    files = []
    for i in range(5):
        file = tmp_path / f"file{i}.txt"
        file.write_text(f"content {i}")
        files.append(file)
    
    def process_func(file):
        return file.name
    
    results = list(processor.process_files(files, process_func))
    assert len(results) == 5
    assert all(f"file{i}.txt" in results for i in range(5))

def test_error_handling(processor):
    """Test error handling in parallel processor."""
    with pytest.raises(Exception):
        processor.find_duplicates(Path("/nonexistent"))