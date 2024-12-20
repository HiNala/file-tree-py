from pathlib import Path
from typing import Dict, List, Set
from rich.tree import Tree
from rich.style import Style
import json

class FileTreeVisualizer:
    """Visualize file tree structure."""

    def __init__(self):
        """Initialize visualizer."""
        self.duplicate_style = Style(color="red")
        self.symlink_style = Style(color="cyan")
        self.directory_style = Style(color="blue", bold=True)

    def export_results(self, duplicates: Dict[str, List[Path]], export_path: Path) -> None:
        """Export duplicate file information to JSON.
        
        Args:
            duplicates: Dictionary mapping hash values to lists of duplicate file paths
            export_path: Path to export the results to
        """
        # Convert Path objects to strings for JSON serialization
        export_data = {
            hash_value: [str(path) for path in paths]
            for hash_value, paths in duplicates.items()
        }
        
        # Add summary information
        export_data["summary"] = {
            "total_groups": len(duplicates),
            "total_duplicates": sum(len(paths) - 1 for paths in duplicates.values()),
            "total_wasted_space": sum(Path(paths[0]).stat().st_size * (len(paths) - 1) 
                                    for paths in duplicates.values() if paths)
        }
        
        # Write to file
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def create_tree(self, root_path: Path, duplicates: Dict[str, List[Path]] = None) -> Tree:
        """Create a tree visualization of the directory structure."""
        duplicates = duplicates or {}
        duplicate_paths: Set[Path] = {
            path for paths in duplicates.values() for path in paths
        }
        tree = Tree(f"[bold blue]{root_path.name}[/bold blue]")
        self._add_directory(tree, root_path, duplicate_paths)
        return tree

    def _add_directory(self, tree: Tree, directory: Path, duplicate_paths: Set[Path]) -> None:
        """Add directory contents to tree."""
        try:
            paths = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            for path in paths:
                if path.is_dir():
                    branch = tree.add(f"[bold blue]{path.name}[/bold blue]")
                    self._add_directory(branch, path, duplicate_paths)
                else:
                    style = self._get_style(path, duplicate_paths)
                    name = path.name
                    if style == self.duplicate_style:
                        name = f"[red]{name}[/red]"
                    elif style == self.symlink_style:
                        name = f"[cyan]{name}[/cyan]"
                    tree.add(name)
        except PermissionError:
            tree.add("[yellow]Permission denied[/yellow]")

    def _get_style(self, path: Path, duplicate_paths: Set[Path]) -> Style:
        """Get style for file based on its properties."""
        if path in duplicate_paths:
            return self.duplicate_style
        if path.is_symlink():
            return self.symlink_style
        return Style()