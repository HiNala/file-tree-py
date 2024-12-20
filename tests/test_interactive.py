"""Tests for interactive file operations."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from filetree.interactive.actions import (
    FileAction,
    DuplicateResolver,
    DirectoryManager,
    interactive_mode
)

@pytest.fixture
def test_files():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create test files
        (root / "file1.txt").write_text("content1")
        (root / "file2.txt").write_text("content1")  # Duplicate
        (root / "unique.txt").write_text("unique")
        
        # Create test directories
        src_dir = root / "source"
        src_dir.mkdir()
        (src_dir / "test1.txt").write_text("test1")
        (src_dir / "test2.txt").write_text("test2")
        
        target_dir = root / "target"
        target_dir.mkdir()
        (target_dir / "test3.txt").write_text("test3")
        
        yield root

def test_file_action_confirm(monkeypatch):
    """Test FileAction confirmation."""
    responses = iter(['y'])
    monkeypatch.setattr('builtins.input', lambda *args: next(responses))
    assert FileAction.confirm_action("Test?") is True

    responses = iter(['n'])
    monkeypatch.setattr('builtins.input', lambda *args: next(responses))
    assert FileAction.confirm_action("Test?") is False

def test_file_action_select_option(monkeypatch):
    """Test FileAction option selection."""
    options = ["Option 1", "Option 2", "Option 3"]

    # Test valid selection
    responses = iter(['2'])
    monkeypatch.setattr('builtins.input', lambda *args: next(responses))
    assert FileAction.select_option(options, "Choose:") == "Option 2"

    # Test invalid then valid selection
    responses = iter(['4', '1'])
    monkeypatch.setattr('builtins.input', lambda *args: next(responses))
    assert FileAction.select_option(options, "Choose:") == "Option 1"

@patch('filetree.interactive.actions.console')
def test_duplicate_resolver_show_duplicates(mock_console, test_files):
    """Test displaying duplicate files."""
    duplicates = {
        "hash1": [
            test_files / "file1.txt",
            test_files / "file2.txt"
        ]
    }
    
    resolver = DuplicateResolver(duplicates)
    resolver.show_duplicates()
    
    # Verify that console.print was called with a table
    assert mock_console.print.called

@patch('filetree.interactive.actions.console')
def test_duplicate_resolver_resolve_group(mock_console, test_files):
    """Test resolving a group of duplicate files."""
    paths = [
        test_files / "file1.txt",
        test_files / "file2.txt"
    ]
    
    resolver = DuplicateResolver({})
    
    # Mock user selecting "Keep newest" option
    with patch.object(FileAction, 'select_option', return_value="Keep newest"):
        with patch.object(FileAction, 'confirm_action', return_value=True):
            resolver.resolve_group("hash1", paths)
            
            # Verify that one file was kept
            assert sum(1 for p in paths if p.exists()) == 1

def test_directory_manager_merge(test_files):
    """Test merging directories."""
    source = test_files / "source"
    target = test_files / "target"
    
    manager = DirectoryManager()
    
    # Mock user confirmation
    with patch.object(FileAction, 'confirm_action', return_value=True):
        manager.merge_directories(source, target)
        
        # Verify files were merged
        assert (target / "test1.txt").exists()
        assert (target / "test2.txt").exists()
        assert (target / "test3.txt").exists()
        assert not source.exists()  # Source should be removed

def test_directory_manager_rename(test_files):
    """Test renaming files."""
    file_path = test_files / "file1.txt"
    new_name = "renamed.txt"
    
    manager = DirectoryManager()
    
    # Mock user input and confirmation
    with patch('rich.prompt.Prompt.ask', return_value=new_name):
        with patch.object(FileAction, 'confirm_action', return_value=True):
            manager.rename_interactive(file_path)
            
            # Verify file was renamed
            assert not file_path.exists()
            assert (file_path.parent / new_name).exists()

@patch('filetree.interactive.actions.console')
def test_interactive_mode(mock_console, test_files):
    """Test interactive mode main loop."""
    duplicates = {
        "hash1": [
            test_files / "file1.txt",
            test_files / "file2.txt"
        ]
    }
    
    # Mock user selecting "Exit" option
    with patch.object(FileAction, 'select_option', return_value="Exit"):
        interactive_mode(duplicates)
        
        # Verify welcome and exit messages
        mock_console.print.assert_any_call("[bold blue]Welcome to Interactive Mode[/bold blue]")
        mock_console.print.assert_any_call("[bold blue]Exiting Interactive Mode[/bold blue]")

def test_error_handling(test_files):
    """Test error handling in interactive operations."""
    # Test non-existent source directory
    manager = DirectoryManager()
    with patch.object(FileAction, 'confirm_action', return_value=True):
        manager.merge_directories(
            test_files / "nonexistent",
            test_files / "target"
        )
        # Operation should fail gracefully
        
    # Test renaming to existing file
    file_path = test_files / "file1.txt"
    with patch('rich.prompt.Prompt.ask', return_value="file2.txt"):
        with patch.object(FileAction, 'confirm_action', return_value=False):
            manager.rename_interactive(file_path)
            # Original file should still exist
            assert file_path.exists() 