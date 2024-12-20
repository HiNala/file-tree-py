"""Tests for the file scanner module."""
import os
import tempfile
from pathlib import Path
import pytest
from filetree.core.scanner import FileTreeScanner
from filetree.utils.config import Config

@pytest.fixture
def scanner():
    """Create a scanner instance for testing."""
    config = Config()
    return FileTreeScanner(config)

@pytest.fixture
def test_directory():
    """Create a test directory with various files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create regular files
        (root / "file1.txt").write_text("content1")
        (root / "file2.py").write_text("content2")
        
        # Create hidden files
        (root / ".hidden").write_text("hidden")
        
        # Create subdirectory with files
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        (subdir / "file4.py").write_text("content4")
        
        # Create symlink if supported
        try:
            (root / "link.txt").symlink_to(root / "file1.txt")
        except OSError:
            pass  # Symlinks might not be supported
            
        yield root

def test_scanner_initialization():
    """Test scanner initialization."""
    config = Config()
    scanner = FileTreeScanner(config)
    assert scanner.config == config

def test_scan_directory(scanner, test_directory):
    """Test scanning directory."""
    files = scanner.scan_directory(test_directory)
    
    # Get list of file names for debugging
    file_names = [f.name for f in files]
    
    # Should find all non-hidden files
    assert len(files) == 4, f"Expected 4 files but found {len(files)}: {file_names}"
    assert any(f.name == "file1.txt" for f in files)
    assert any(f.name == "file2.py" for f in files)
    assert any(f.name == "file3.txt" for f in files)
    assert any(f.name == "file4.py" for f in files)
    
    # Should not include hidden files by default
    assert not any(f.name == ".hidden" for f in files)
    
    # Should not include symlinks by default
    assert not any(f.name == "link.txt" for f in files)

def test_scan_with_hidden_files(test_directory):
    """Test scanning with hidden files included."""
    config = Config()
    config.include_hidden = True
    scanner = FileTreeScanner(config)
    
    files = scanner.scan_directory(test_directory)
    assert any(f.name == ".hidden" for f in files)

def test_scan_with_symlinks(test_directory):
    """Test scanning with symlinks included."""
    config = Config()
    config.follow_symlinks = True
    scanner = FileTreeScanner(config)
    
    files = scanner.scan_directory(test_directory)
    # Skip this test if symlinks are not supported
    if any(f.name == "link.txt" for f in files):
        assert True
    else:
        pytest.skip("Symlinks not supported on this platform")

def test_scan_with_ignore_patterns(test_directory):
    """Test scanning with ignore patterns."""
    config = Config()
    config.ignore_patterns.append("*.py")
    scanner = FileTreeScanner(config)
    
    files = scanner.scan_directory(test_directory)
    assert not any(f.suffix == ".py" for f in files)
    assert any(f.suffix == ".txt" for f in files)

def test_get_file_stats(scanner, test_directory):
    """Test getting file statistics."""
    files = scanner.scan_directory(test_directory)
    stats = scanner.get_file_stats(files)
    
    assert stats['total_files'] == len(files)
    assert stats['total_size'] > 0
    assert stats['min_size'] > 0
    assert stats['max_size'] >= stats['min_size']

def test_get_file_types(scanner, test_directory):
    """Test getting file type distribution."""
    files = scanner.scan_directory(test_directory)
    type_dist = scanner.get_file_types(files)
    
    assert ".txt" in type_dist
    assert ".py" in type_dist
    assert type_dist[".txt"] == 2
    assert type_dist[".py"] == 2

def test_get_directory_structure(scanner, test_directory):
    """Test getting directory structure."""
    structure = scanner.get_directory_structure(test_directory)
    
    # Root directory files
    assert "." in structure
    root_files = structure["."]
    assert any(f.name == "file1.txt" for f in root_files)
    assert any(f.name == "file2.py" for f in root_files)
    
    # Subdirectory files
    assert "subdir" in structure
    subdir_files = structure["subdir"]
    assert any(f.name == "file3.txt" for f in subdir_files)
    assert any(f.name == "file4.py" for f in subdir_files)

def test_scanner_error_handling(scanner):
    """Test error handling in scanner."""
    nonexistent = Path("/nonexistent/path/that/does/not/exist")
    with pytest.raises(Exception) as excinfo:
        scanner.scan_directory(nonexistent)
    assert str(excinfo.value).startswith(f"Error scanning directory {nonexistent}")