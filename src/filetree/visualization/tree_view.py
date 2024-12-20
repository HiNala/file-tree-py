from pathlib import Path
from typing import Dict, Optional
from rich.tree import Tree
from rich.console import Console
import logging
from ..utils.config import FileTreeConfig

class FileTreeVisualizer:
    """Visualizes directory structures with annotations for duplicates and issues."""
    
    def __init__(self, console: Optional[Console] = None, config: Optional[FileTreeConfig] = None):
        self.console = console or Console()
        self.config = config or FileTreeConfig.default()
        self.logger = logging.getLogger(__name__)
    
    def create_tree(self, root_path: Path, duplicates: Dict[str, list[Path]] = None) -> Tree:
        """Create a visual tree representation of the directory structure."""
        duplicates = duplicates or {}
        duplicate_lookup = {
            str(path): file_hash
            for file_hash, paths in duplicates.items()
            for path in paths
        }
        
        tree = Tree(f"[bold blue]{root_path}[/bold blue]")
        self._build_tree(root_path, tree, duplicate_lookup)
        return tree
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored based on config patterns."""
        if not self.config.ignore_patterns:
            return False
        
        return any(
            path.match(pattern) 
            for pattern in self.config.ignore_patterns
        )
    
    def _get_file_annotation(self, path: Path, duplicate_hash: Optional[str] = None) -> str:
        """Get annotation string for a file."""
        annotations = []
        
        # Add duplicate annotation if applicable
        if duplicate_hash:
            annotations.append(f"[dim](dup: {duplicate_hash[:8]}...)[/dim]")
        
        # Add file type annotation if configured
        if self.config.file_annotations:
            suffix = path.suffix.lower()
            if suffix in self.config.file_annotations:
                annotations.append(self.config.file_annotations[suffix])
        
        return " ".join(annotations)
    
    def _build_tree(self, path: Path, tree: Tree, duplicate_lookup: Dict[str, str]) -> None:
        """Recursively build the tree structure."""
        try:
            if self._should_ignore(path):
                return
            
            paths = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            
            for item in paths:
                try:
                    if item.is_symlink():
                        target = item.resolve()
                        tree.add(f"[cyan]{item.name}[/cyan] -> [dim]{target}[/dim]")
                        continue
                    
                    if item.is_dir():
                        if not self._should_ignore(item):
                            branch = tree.add(f"[bold cyan]{item.name}/[/bold cyan]")
                            self._build_tree(item, branch, duplicate_lookup)
                    else:
                        item_str = str(item)
                        duplicate_hash = duplicate_lookup.get(item_str)
                        name_style = "[red]" if duplicate_hash else ""
                        annotation = self._get_file_annotation(item, duplicate_hash)
                        
                        tree.add(f"{name_style}{item.name}{annotation}")
                
                except PermissionError:
                    tree.add(f"[red]{item.name} (Permission denied)[/red]")
                except Exception as e:
                    if self.config.debug_mode:
                        self.logger.exception(f"Error processing {item}")
                    tree.add(f"[red]{item.name} (Error: {str(e)})[/red]")
        
        except Exception as e:
            if self.config.debug_mode:
                self.logger.exception(f"Error accessing directory {path}")
            tree.add("[red]Error accessing directory[/red]") 