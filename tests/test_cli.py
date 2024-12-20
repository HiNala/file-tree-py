"""Tests for the command-line interface."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY, call
import pytest
from filetree.cli import main
from filetree.utils.config import Config
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

def test_main_invalid_directory(mock_console):
    """Test main with invalid directory."""
    nonexistent = str(Path("/nonexistent"))
    with patch("filetree.cli.console", mock_console):
        with patch("sys.argv", ["filetree", nonexistent]):
            assert main() == 1
            mock_console.print.assert_called_with(f"[red]Directory not found: {nonexistent}[/red]")

@patch('filetree.cli.console')
def test_main_no_duplicates(mock_console, test_directory):
    """Test main function with no duplicates."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        with patch('filetree.cli.DuplicateFinder') as mock_finder_class:
            mock_finder = MagicMock()
            mock_finder.find_duplicates.return_value = {}
            mock_finder.get_duplicate_stats.return_value = {
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0
            }
            mock_finder_class.return_value = mock_finder
            main()

        # Verify that the correct message was printed
        mock_console.print.assert_any_call(ANY)  # Scanning message
        mock_console.print.assert_any_call(ANY)  # Analysis message
        mock_console.print.assert_any_call(ANY)  # Report with no duplicates

@patch('filetree.cli.console')
def test_main_with_duplicates(mock_console, test_directory):
    """Test main function with duplicates in non-interactive mode."""
    with patch('sys.argv', ['script.py', str(test_directory)]):
        with patch('filetree.cli.DuplicateFinder') as mock_finder_class:
            mock_finder = MagicMock()
            mock_finder.find_duplicates.return_value = {
                'hash1': [Path('file1.txt'), Path('file2.txt')],
                'hash2': [Path('file3.txt'), Path('file4.txt')]
            }
            mock_finder.get_duplicate_stats.return_value = {
                'total_groups': 2,
                'total_duplicates': 2,
                'wasted_space': 1000
            }
            mock_finder_class.return_value = mock_finder
            main()

        # Verify that the correct messages were printed
        mock_console.print.assert_any_call(ANY)  # Scanning message
        mock_console.print.assert_any_call(ANY)  # Analysis message
        mock_console.print.assert_any_call(ANY)  # Report with duplicates

@patch('filetree.cli.console')
def test_main_with_export(mock_console, test_directory):
    """Test main function with export option."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        export_path = Path(tmp_dir) / "results.md"
        with patch('sys.argv', ['script.py', str(test_directory), '--export', str(export_path)]):
            with patch('filetree.cli.DuplicateFinder') as mock_finder_class:
                mock_finder = MagicMock()
                mock_finder.find_duplicates.return_value = {}
                mock_finder.get_duplicate_stats.return_value = {
                    'total_groups': 0,
                    'total_duplicates': 0,
                    'wasted_space': 0
                }
                mock_finder_class.return_value = mock_finder
                main()
                assert export_path.exists()

@patch('filetree.cli.console')
def test_main_with_min_size(mock_console, test_directory):
    """Test main function with minimum file size option."""
    min_size = 1000
    with patch('sys.argv', ['script.py', str(test_directory), '--min-size', str(min_size)]):
        with patch('filetree.cli.DuplicateFinder') as mock_finder_class:
            mock_finder = MagicMock()
            mock_finder.find_duplicates.return_value = {}
            mock_finder.get_duplicate_stats.return_value = {
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0
            }
            mock_finder_class.return_value = mock_finder
            main()
            assert mock_finder_class.call_count == 1
            assert mock_finder_class.call_args[1]['min_size'] == min_size

@patch('filetree.cli.console')
def test_main_with_exclude_patterns(mock_console, test_directory):
    """Test main function with exclude patterns."""
    exclude_patterns = ['*.tmp', '*.log']
    with patch('sys.argv', ['script.py', str(test_directory), '--exclude'] + exclude_patterns):
        with patch('filetree.cli.DuplicateFinder') as mock_finder_class:
            mock_finder = MagicMock()
            mock_finder.find_duplicates.return_value = {}
            mock_finder.get_duplicate_stats.return_value = {
                'total_groups': 0,
                'total_duplicates': 0,
                'wasted_space': 0
            }
            mock_finder_class.return_value = mock_finder
            main()
            mock_console.print.assert_any_call(ANY)