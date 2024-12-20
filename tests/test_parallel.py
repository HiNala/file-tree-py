"""Tests for parallel processing utilities."""
import os
import tempfile
from pathlib import Path
import pytest
from filetree.utils.parallel import ParallelProcessor, compute_file_hash

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create some test files
        root = Path(tmp_dir)
        
        # Create duplicate files
        content1 = b"test content 1"
        content2 = b"test content 2"
        
        # Create files in root
        (root / "file1.txt").write_bytes(content1)
        (root / "file2.txt").write_bytes(content1)  # Duplicate of file1
        (root / "file3.txt").write_bytes(content2)
        
        # Create subdirectory with more files
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file4.txt").write_bytes(content1)  # Duplicate of file1
        (subdir / "file5.txt").write_bytes(content2)  # Duplicate of file3
        
        # Create hidden files and directories
        (root / ".hidden_file.txt").write_bytes(b"hidden content")
        hidden_dir = root / ".hidden_dir"
        hidden_dir.mkdir()
        (hidden_dir / "file6.txt").write_bytes(b"hidden dir content")
        
        yield root

def test_compute_file_hash(temp_dir):
    """Test file hash computation."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    file3 = temp_dir / "file3.txt"
    
    # Test that identical files have the same hash
    assert compute_file_hash(file1) == compute_file_hash(file2)
    # Test that different files have different hashes
    assert compute_file_hash(file1) != compute_file_hash(file3)

def test_parallel_processor_init():
    """Test ParallelProcessor initialization."""
    # Test default initialization
    processor = ParallelProcessor()
    assert processor.max_workers == os.cpu_count() * 2
    
    # Test custom workers
    custom_workers = 4
    processor = ParallelProcessor(max_workers=custom_workers)
    assert processor.max_workers == custom_workers

def test_scan_directory(temp_dir):
    """Test parallel directory scanning."""
    processor = ParallelProcessor()
    files = processor.scan_directory(temp_dir)
    
    # Convert to set of relative paths for easier comparison
    relative_paths = {str(f.relative_to(temp_dir)) for f in files}
    
    # Check that we found all non-hidden files
    expected_files = {
        "file1.txt",
        "file2.txt",
        "file3.txt",
        "subdir/file4.txt",
        "subdir/file5.txt"
    }
    
    assert relative_paths == expected_files
    
    # Verify hidden files are not included by default
    hidden_files = {".hidden_file.txt", ".hidden_dir/file6.txt"}
    assert not any(hidden in relative_paths for hidden in hidden_files)

def test_find_duplicates(temp_dir):
    """Test parallel duplicate file detection."""
    processor = ParallelProcessor()
    files = processor.scan_directory(temp_dir)
    duplicates = processor.find_duplicates(files)
    
    # We should have two sets of duplicates
    assert len(duplicates) == 2
    
    # Convert paths to relative for easier comparison
    dup_groups = [
        {str(p.relative_to(temp_dir)) for p in paths}
        for paths in duplicates.values()
    ]
    
    # Check that we found both groups of duplicates
    expected_groups = [
        {"file1.txt", "file2.txt", "subdir/file4.txt"},  # content1 duplicates
        {"file3.txt", "subdir/file5.txt"}  # content2 duplicates
    ]
    
    assert all(group in dup_groups for group in expected_groups)

def test_process_files(temp_dir):
    """Test parallel file processing."""
    processor = ParallelProcessor()
    files = list(temp_dir.glob("*.txt"))
    
    # Test with a simple processor function
    def get_file_size(path: Path) -> int:
        return path.stat().st_size
    
    sizes = list(processor.process_files(files, get_file_size))
    assert len(sizes) == len(files)
    assert all(isinstance(size, int) for size in sizes)

def test_error_handling(temp_dir):
    """Test error handling in parallel processing."""
    processor = ParallelProcessor()
    
    # Create a non-existent file
    non_existent = temp_dir / "non_existent.txt"
    
    # Test hash computation of non-existent file
    assert compute_file_hash(non_existent) == ""
    
    # Test processing with failing function
    def failing_processor(path: Path):
        raise Exception("Test error")
    
    files = [temp_dir / "file1.txt"]
    results = list(processor.process_files(files, failing_processor))
    assert len(results) == 0  # All processing should have failed 