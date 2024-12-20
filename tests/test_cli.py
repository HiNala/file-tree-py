"""Tests for the command-line interface."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from filetree.cli import create_parser, main

@pytest.fixture
def test_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Create some test files
        (root / "file1.txt").write_text("content1")
        (root / "file2.txt").write_text("content1")  # Duplicate
        (root / "unique.txt").write_text("unique")
        
        # Create a subdirectory with more files
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content2")
        (subdir / "file4.txt").write_text("content2")  # Duplicate
        
        yield root

def test_parser_creation():
    """Test command line argument parser creation."""
    parser = create_parser()
    
    # Test with minimal arguments
    args = parser.parse_args(["some/path"])
    assert args.directory == "some/path"
    assert not args.interactive
    assert args.workers is None
    
    # Test with all arguments
    args = parser.parse_args([
        "some/path",
        "--interactive",
        "--workers", "4"
    ])
    assert args.directory == "some/path"
    assert args.interactive
    assert args.workers == 4

@patch('filetree.cli.console')
def test_main_no_duplicates(mock_console):
    """Test main function with no duplicates."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a directory with no duplicates
        root = Path(tmp_dir)
        (root / "unique1.txt").write_text("unique1")
        (root / "unique2.txt").write_text("unique2")
        
        with patch('sys.argv', ['script.py', str(root)]):
            main()
            
            # Verify output
            mock_console.print.assert_any_call("[green]No duplicate files found.[/green]")

@patch('filetree.cli.console')
def test_main_with_duplicates(mock_console, test_directory):
    """Test main function with duplicates in non-interactive mode."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        main()
        
        # Verify that duplicate groups were found
        assert any(
            "Duplicate group" in str(call.args[0])
            for call in mock_console.print.call_args_list
        )

@patch('filetree.cli.interactive_mode')
@patch('filetree.cli.console')
def test_main_interactive_mode(mock_console, mock_interactive, test_directory):
    """Test main function in interactive mode."""
    with patch('sys.argv', ['script.py', str(test_directory), '--interactive']):
        main()
        
        # Verify that interactive mode was called
        assert mock_interactive.called

@patch('filetree.cli.console')
def test_main_invalid_directory(mock_console):
    """Test main function with invalid directory."""
    with patch('sys.argv', ['script.py', 'nonexistent/path']):
        with pytest.raises(SystemExit):
            main()
        
        # Verify error message
        mock_console.print.assert_any_call(
            "[red]Error:[/red] nonexistent/path is not a directory"
        )

@patch('filetree.cli.console')
def test_main_keyboard_interrupt(mock_console, test_directory):
    """Test main function with keyboard interrupt."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        with patch('filetree.core.scanner.FileScanner.scan', side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit):
                main()
            
            # Verify interrupt message
            mock_console.print.assert_any_call(
                "\n[yellow]Operation cancelled by user[/yellow]"
            )

@patch('filetree.cli.console')
def test_main_custom_workers(mock_console, test_directory):
    """Test main function with custom worker count."""
    workers = 4
    with patch('sys.argv', ['script.py', str(test_directory), '--workers', str(workers)]):
        with patch('filetree.core.scanner.FileScanner') as mock_scanner:
            main()
            
            # Verify scanner was initialized with correct worker count
            mock_scanner.assert_called_once_with(
                str(test_directory),
                max_workers=workers
            ) 