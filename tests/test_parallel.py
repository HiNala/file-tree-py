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
    return ParallelProcessor(max_workers=8, min_workers=1)

@pytest.fixture
def test_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create some test files
        (root / "file1.txt").write_text("content1")
        (root / "file2.txt").write_text("content2")
        (root / "file3.txt").write_text("content3")
        
        yield root

def test_processor_initialization():
    """Test parallel processor initialization."""
    processor = ParallelProcessor(max_workers=4)
    assert processor.max_workers == 4
    assert processor.min_workers == 2  # Default value

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
    files = set()
    for i in range(5):
        file = tmp_path / f"file{i}.txt"
        file.write_text(f"content {i}")
        files.add(file)

    # Process files
    results = processor.process_files(files)
    
    # Verify results
    assert len(results) > 0  # Should have at least one hash
    for hash_value, paths in results.items():
        assert isinstance(hash_value, str)
        assert isinstance(paths, list)
        assert all(isinstance(p, Path) for p in paths)

def test_error_handling(processor):
    """Test error handling in parallel processor."""
    # Test with empty set of files
    results = processor.find_duplicates(set())
    assert results == {}

    # Test with non-existent directory
    results = processor.find_duplicates(Path("nonexistent"))
    assert results == {}

    # Test with invalid file path
    results = processor.process_files({Path("nonexistent.txt")})
    assert results == {}

def test_dynamic_worker_allocation(processor):
    """Test that worker count adjusts based on system load."""
    # Mock system metrics
    with patch('psutil.cpu_percent', return_value=50.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('os.cpu_count', return_value=4):
        
        # Mock memory metrics
        mock_memory.return_value = MagicMock(
            percent=60.0,  # 60% memory usage
        )
        
        # Get worker count
        workers = processor._get_optimal_workers()
        
        # With 50% CPU load and 60% memory usage:
        # CPU factor = 1 - 0.5 = 0.5
        # Memory factor = 1 - 0.6 = 0.4
        # System factor = (0.5 * 0.7) + (0.4 * 0.3) = 0.47
        # Expected workers = min(8, 4 * 0.47 * 2) ≈ 3.76
        assert 3 <= workers <= 4, f"Expected 3-4 workers, got {workers}"

def test_worker_hysteresis(processor):
    """Test that worker count doesn't change for small load variations."""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('os.cpu_count', return_value=4):
        
        # Initial state: moderate load
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(percent=50.0)
        initial_workers = processor._get_current_workers()
        
        # Small load change
        mock_cpu.return_value = 55.0  # Small 5% increase
        mock_memory.return_value = MagicMock(percent=55.0)
        new_workers = processor._get_current_workers()
        
        # Worker count should remain stable
        assert new_workers == initial_workers, "Worker count changed with small load variation"
        
        # Large load change
        mock_cpu.return_value = 90.0  # Large increase
        mock_memory.return_value = MagicMock(percent=90.0)
        new_workers = processor._get_current_workers()
        
        # Worker count should decrease
        assert new_workers <= 2, "Worker count didn't decrease with high load"

def test_minimum_workers(processor):
    """Test that worker count never goes below minimum."""
    with patch('psutil.cpu_percent', return_value=100.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('os.cpu_count', return_value=4):
        
        # Simulate very high system load
        mock_memory.return_value = MagicMock(percent=100.0)
        
        workers = processor._get_optimal_workers()
        assert workers >= processor.min_workers, "Worker count went below minimum"

def test_maximum_workers(processor):
    """Test that worker count never exceeds maximum."""
    with patch('psutil.cpu_percent', return_value=0.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('os.cpu_count', return_value=32):
        
        # Simulate very low system load
        mock_memory.return_value = MagicMock(percent=0.0)
        
        workers = processor._get_optimal_workers()
        assert workers <= processor.max_workers, "Worker count exceeded maximum"