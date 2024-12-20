"""Tests for the file scanner module."""
import os
import tempfile
from pathlib import Path
import pytest
from filetree.core.scanner import FileScanner

@pytest.fixture
def test_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test directory structure
        root = Path(tmp_dir)
        
        # Create some test files with duplicate content
        content1 = b"test content 1"
        content2 = b"test content 2"
        unique_content = b"unique content"
        
        # Create files in root
        (root / "file1.txt").write_bytes(content1)
        (root / "file2.txt").write_bytes(content1)  # Duplicate
        (root / "unique.txt").write_bytes(unique_content)
        
        # Create nested directory structure
        subdir1 = root / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file3.txt").write_bytes(content2)
        
        subdir2 = root / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file4.txt").write_bytes(content2)  # Duplicate
        
        # Create some hidden files
        (root / ".hidden").write_bytes(b"hidden content")
        
        yield root

def test_scanner_initialization():
    """Test scanner initialization."""
    scanner = FileScanner("dummy/path")
    assert scanner.directory == Path("dummy/path")
    assert isinstance(scanner.file_hashes, dict)
    assert isinstance(scanner.scanned_files, set)

def test_parallel_scanning(test_directory):
    """Test parallel file scanning functionality."""
    scanner = FileScanner(str(test_directory))
    result = scanner.scan()
    
    # Check that all files were scanned
    expected_files = {
        "file1.txt",
        "file2.txt",
        "unique.txt",
        "subdir1/file3.txt",
        "subdir2/file4.txt"
    }
    
    scanned_files = {
        str(f.relative_to(test_directory))
        for f in scanner.scanned_files
    }
    
    assert scanned_files == expected_files

def test_duplicate_detection(test_directory):
    """Test duplicate file detection."""
    scanner = FileScanner(str(test_directory))
    scanner.scan()
    duplicates = scanner.get_duplicates()
    
    # We should have two groups of duplicates
    assert len(duplicates) == 2
    
    # Convert paths to relative for easier comparison
    duplicate_groups = [
        {str(p.relative_to(test_directory)) for p in paths}
        for paths in duplicates.values()
    ]
    
    # Check both groups of duplicates
    expected_groups = [
        {"file1.txt", "file2.txt"},  # content1 duplicates
        {"subdir1/file3.txt", "subdir2/file4.txt"}  # content2 duplicates
    ]
    
    assert all(group in duplicate_groups for group in expected_groups)

def test_custom_workers():
    """Test scanner with custom number of workers."""
    custom_workers = 4
    scanner = FileScanner("dummy/path", max_workers=custom_workers)
    assert scanner.processor.max_workers == custom_workers

def test_empty_directory():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        scanner = FileScanner(tmp_dir)
        result = scanner.scan()
        assert len(result) == 0
        assert len(scanner.scanned_files) == 0

def test_error_handling():
    """Test error handling for non-existent directory."""
    scanner = FileScanner("non/existent/path")
    result = scanner.scan()
    assert len(result) == 0
    assert len(scanner.scanned_files) == 0

def test_large_directory_structure(tmp_path):
    """Test scanning a large directory structure."""
    # Create a larger directory structure
    for i in range(5):
        subdir = tmp_path / f"dir{i}"
        subdir.mkdir()
        for j in range(10):
            (subdir / f"file{j}.txt").write_text(f"content {i}{j}")
    
    # Add some duplicates
    duplicate_content = "duplicate content"
    (tmp_path / "dir0/dup1.txt").write_text(duplicate_content)
    (tmp_path / "dir1/dup2.txt").write_text(duplicate_content)
    (tmp_path / "dir2/dup3.txt").write_text(duplicate_content)
    
    scanner = FileScanner(str(tmp_path))
    result = scanner.scan()
    
    # Verify total number of scanned files
    assert len(scanner.scanned_files) == 53  # 50 unique + 3 duplicates
    
    # Verify duplicates were found
    duplicates = scanner.get_duplicates()
    assert len(duplicates) >= 1  # At least one group of duplicates 