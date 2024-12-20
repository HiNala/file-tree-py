"""Tests for the command-line interface."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from filetree.cli import main, display_results
from filetree.utils.config import FileTreeConfig
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
        mock_console.print.assert_any_call("\nFound [bold]2[/bold] groups of duplicate files.")

def test_main_invalid_directory(mock_console):
    """Test main with invalid directory."""
    with patch("filetree.cli.console", mock_console):
        with patch("sys.argv", ["filetree", r"\nonexistent"]):
            assert main() == 1
            mock_console.print.assert_called_with(r"[red]Error: Directory '\nonexistent' does not exist.[/red]")

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

@patch('filetree.cli.console')
def test_main_custom_workers(mock_console, test_directory):
    """Test main function with custom worker count."""
    workers = 4
    with patch('sys.argv', ['script.py', str(test_directory), '--workers', str(workers)]):
        with patch('filetree.cli.FileScanner', autospec=True) as mock_scanner_class:
            mock_scanner = mock_scanner_class.return_value
            mock_scanner.find_duplicates.return_value = {}
            main()

            # Verify scanner was initialized with correct worker count
            assert mock_scanner_class.call_count == 1
            assert mock_scanner_class.call_args.kwargs['num_workers'] == workers

@patch('filetree.cli.console')
def test_main_with_config(mock_console, test_directory):
    """Test main function with custom configuration file."""
    config_path = "config.json"
    with patch('sys.argv', ['script.py', str(test_directory), '--config', config_path]):
        with patch('filetree.utils.config.FileTreeConfig.from_file') as mock_config:
            with patch('filetree.core.scanner.FileScanner') as mock_scanner:
                mock_scanner.return_value.find_duplicates.return_value = {}
                main()

                # Verify config was loaded from file
                mock_config.assert_called_once_with(config_path)

@patch('filetree.cli.console')
def test_main_with_export(mock_console, test_directory):
    """Test main function with export option."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        export_path = Path(tmp_dir) / "results.json"
        with patch('sys.argv', ['script.py', str(test_directory), '--export', str(export_path), '--no-tree']):
            with patch('filetree.cli.FileScanner') as mock_scanner:
                mock_scanner.return_value.find_duplicates.return_value = {}
                with patch('filetree.cli.FileTreeVisualizer') as mock_visualizer_class:
                    mock_visualizer = mock_visualizer_class.return_value
                    mock_visualizer.export_results.return_value = None
                    main()
                    # Verify results were exported
                    mock_visualizer.export_results.assert_called_once_with({}, export_path)