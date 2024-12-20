import pytest
from pathlib import Path
from rich.tree import Tree
from filetree.visualization.tree_view import FileTreeVisualizer

@pytest.fixture
def visualizer():
    """Create a tree visualizer instance for testing."""
    return FileTreeVisualizer()

def test_create_tree(visualizer, tmp_path):
    """Test creating a tree visualization."""
    # Create test files and directories
    file1 = tmp_path / "file1.txt"
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.txt"
    
    file1.write_text("content1")
    file2.write_text("content2")
    
    tree = visualizer.create_tree(tmp_path)
    assert isinstance(tree, Tree)
    assert tree.label == f"[bold blue]{tmp_path.name}[/bold blue]"

def test_tree_with_duplicates(visualizer, tmp_path):
    """Test tree visualization with duplicate files."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("test content")
    file2.write_text("test content")
    
    duplicates = {
        "hash1": [file1, file2]
    }
    
    tree = visualizer.create_tree(tmp_path, duplicates)
    assert isinstance(tree, Tree)
    # Verify that duplicate files are marked in red
    assert any("[red]" in str(node.label) for node in tree.children)

def test_tree_with_symlinks(visualizer, tmp_path):
    """Test tree visualization with symlinks."""
    # Create test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("test content")
    link1 = tmp_path / "link1.txt"
    
    try:
        link1.symlink_to(file1)
        tree = visualizer.create_tree(tmp_path)
        assert isinstance(tree, Tree)
        # Verify that symlinks are marked in cyan
        assert any("[cyan]" in str(node.label) for node in tree.children)
    except OSError:
        pytest.skip("Symlink creation not supported or requires elevated privileges")

def test_tree_with_permission_error(visualizer, tmp_path):
    """Test tree visualization with permission error."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    
    def mock_iterdir(*args):
        raise PermissionError("Access denied")
    
    # Mock the iterdir method to raise PermissionError
    with pytest.MonkeyPatch().context() as m:
        m.setattr(Path, "iterdir", mock_iterdir)
        tree = visualizer.create_tree(tmp_path)
        assert isinstance(tree, Tree)
        # Verify that permission error is shown in yellow
        assert any("[yellow]Permission denied[/yellow]" in str(node.label) for node in tree.children)