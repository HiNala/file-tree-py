import pytest
from pathlib import Path
from rich.tree import Tree
from filetree.visualization.tree_view import FileTreeVisualizer
from filetree.utils.config import FileTreeConfig

def test_tree_creation(mock_file_tree):
    """Test basic tree creation."""
    visualizer = FileTreeVisualizer()
    tree = visualizer.create_tree(mock_file_tree)
    
    assert isinstance(tree, Tree)
    assert str(mock_file_tree) in tree.label

def test_duplicate_highlighting(mock_file_tree):
    """Test that duplicates are properly highlighted."""
    # Create a duplicate mapping
    duplicates = {
        "test_hash": [
            mock_file_tree / "src" / "utils" / "helper.py",
            mock_file_tree / "lib" / "utils" / "helper.py"
        ]
    }
    
    visualizer = FileTreeVisualizer()
    tree = visualizer.create_tree(mock_file_tree, duplicates)
    tree_str = str(tree)
    
    # Check that both duplicate files are marked in red
    assert "[red]helper.py[/red]" in tree_str
    assert "(dup: test_has)" in tree_str

def test_ignore_patterns(mock_file_tree):
    """Test that ignored patterns are not included in the tree."""
    # Create a __pycache__ directory that should be ignored
    pycache_dir = mock_file_tree / "src" / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "main.cpython-39.pyc").touch()
    
    config = FileTreeConfig.default()
    visualizer = FileTreeVisualizer(config=config)
    tree = visualizer.create_tree(mock_file_tree)
    tree_str = str(tree)
    
    assert "__pycache__" not in tree_str
    assert "main.cpython-39.pyc" not in tree_str

def test_symlink_handling(mock_file_tree):
    """Test that symlinks are properly displayed."""
    visualizer = FileTreeVisualizer()
    tree = visualizer.create_tree(mock_file_tree)
    tree_str = str(tree)
    
    assert "[cyan]link.py[/cyan]" in tree_str
    assert "-> " in tree_str  # Check for symlink indicator 