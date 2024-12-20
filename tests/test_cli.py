"""Tests for the command-line interface."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from filetree.cli import main, display_results
from rich.console import Console

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

@pytest.fixture
def mock_console():
    return MagicMock(spec=Console)

def test_display_results_no_duplicates(mock_console):
    """Test display_results with no duplicates."""
    with patch("filetree.cli.console", mock_console):
        display_results({})
        mock_console.print.assert_called_once_with("[green]No duplicate files found.[/green]")

def test_display_results_with_duplicates(mock_console):
    """Test display_results with duplicates."""
    duplicates = {
        "hash1": [Path("file1.txt"), Path("file2.txt")],
        "hash2": [Path("file3.txt"), Path("file4.txt")]
    }
    with patch("filetree.cli.console", mock_console):
        display_results(duplicates)
        assert mock_console.print.call_count >= 3

def test_main_invalid_directory(mock_console):
    """Test main with invalid directory."""
    with patch("filetree.cli.console", mock_console):
        with patch("sys.argv", ["filetree", r"\nonexistent"]):
            assert main() == 1
            mock_console.print.assert_called_with(r"[red]Error: Directory '\nonexistent' does not exist.[/red]")

def test_main_with_duplicates(mock_console):
    """Test main with duplicates found."""
    mock_scanner = MagicMock()
    mock_scanner.find_duplicates.return_value = {
        "hash1": [Path("file1.txt"), Path("file2.txt")]
    }
    
    with patch("filetree.cli.console", mock_console), \
         patch("filetree.cli.FileScanner", return_value=mock_scanner), \
         patch("filetree.cli.FileTreeVisualizer"), \
         patch("sys.argv", ["filetree", "."]):
        assert main() == 0
        mock_scanner.find_duplicates.assert_called_once()

def test_main_with_error(mock_console):
    """Test main with error during scanning."""
    mock_scanner = MagicMock()
    mock_scanner.find_duplicates.side_effect = Exception("Test error")
    
    with patch("filetree.cli.console", mock_console), \
         patch("filetree.cli.FileScanner", return_value=mock_scanner), \
         patch("sys.argv", ["filetree", "."]):
        assert main() == 1
        mock_console.print.assert_called_with("[red]Error: Test error[/red]")

@patch('filetree.cli.console')
def test_main_no_duplicates(mock_console):
    """Test main function with no duplicates."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a directory with no duplicates
        root = Path(tmp_dir)
        (root / "unique1.txt").write_text("unique1")
        (root / "unique2.txt").write_text("unique2")

        with patch('sys.argv', ['script.py', str(root)]):
            with patch('filetree.core.scanner.FileScanner') as mock_scanner:
                mock_scanner.return_value.find_duplicates.return_value = {}
                main()

        # Verify that the correct message was printed
        mock_console.print.assert_any_call("[green]No duplicate files found.[/green]")

@patch('filetree.cli.console')
def test_main_with_duplicates(mock_console, test_directory):
    """Test main function with duplicates in non-interactive mode."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        with patch('filetree.core.scanner.FileScanner') as mock_scanner:
            mock_scanner.return_value.find_duplicates.return_value = {
                'hash1': [Path('file1.txt'), Path('file2.txt')],
                'hash2': [Path('file3.txt'), Path('file4.txt')]
            }
            main()

    # Verify that the correct messages were printed
    mock_console.print.assert_any_call("\nFound [bold]2[/bold] groups of duplicate files.")
    mock_console.print.assert_any_call("\n[blue]Tip: Use --interactive (-i) to manage duplicates.[/blue]")

@patch('filetree.cli.interactive_mode')
@patch('filetree.cli.console')
def test_main_interactive_mode(mock_console, mock_interactive, test_directory):
    """Test main function in interactive mode."""
    with patch('sys.argv', ['script.py', str(test_directory), '--interactive']):
        main()
        
        # Verify that interactive mode was called
        assert mock_interactive.called

@patch('filetree.cli.console')
def test_main_keyboard_interrupt(mock_console, test_directory):
    """Test main function with keyboard interrupt."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        with patch('filetree.core.scanner.FileScanner.scan', side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 130  # Standard exit code for SIGINT

        # Verify interrupt message
        mock_console.print.assert_called_with("\n[yellow]Operation cancelled by user[/yellow]")

@patch('filetree.cli.console')
def test_main_custom_workers(mock_console, test_directory):
    """Test main function with custom worker count."""
    workers = 4
    with patch('sys.argv', ['script.py', str(test_directory), '--workers', str(workers)]):
        with patch('filetree.core.scanner.FileScanner') as mock_scanner:
            mock_scanner.return_value.find_duplicates.return_value = {}
            main()

            # Verify scanner was initialized with correct worker count
            mock_scanner.assert_called_once_with(workers) 