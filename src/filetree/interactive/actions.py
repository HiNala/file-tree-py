"""Interactive actions for managing files and directories."""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

class FileAction:
    """Base class for file actions."""
    
    @staticmethod
    def confirm_action(message: str) -> bool:
        """Ask for user confirmation before proceeding with an action."""
        return Confirm.ask(message)
    
    @staticmethod
    def select_option(options: List[str], prompt: str) -> Optional[str]:
        """Let user select from a list of options."""
        if not options:
            return None
            
        console.print("\n[bold]Available options:[/bold]")
        for i, option in enumerate(options, 1):
            console.print(f"{i}. {option}")
        
        choice = Prompt.ask(
            prompt,
            choices=[str(i) for i in range(1, len(options) + 1)],
            show_choices=False
        )
        return options[int(choice) - 1]

class DuplicateResolver(FileAction):
    """Handles resolution of duplicate files."""
    
    def __init__(self, duplicates: Dict[str, List[Path]]):
        """Initialize with dictionary of duplicate files."""
        self.duplicates = duplicates
    
    def show_duplicates(self):
        """Display duplicate files in a formatted table."""
        table = Table(title="Duplicate Files Found")
        table.add_column("Group", justify="right", style="cyan")
        table.add_column("Files", style="green")
        table.add_column("Size", justify="right", style="magenta")
        
        for idx, (_, paths) in enumerate(self.duplicates.items(), 1):
            size = paths[0].stat().st_size
            file_list = "\n".join(str(p) for p in paths)
            table.add_row(
                f"Group {idx}",
                file_list,
                f"{size:,} bytes"
            )
        
        console.print(table)
    
    def resolve_group(self, hash_value: str, paths: List[Path]):
        """Resolve a group of duplicate files."""
        console.print(f"\n[bold]Resolving duplicate group:[/bold]")
        for i, path in enumerate(paths, 1):
            console.print(f"{i}. {path}")
        
        actions = [
            "Keep newest",
            "Keep oldest",
            "Keep specific file",
            "Delete all except one",
            "Skip"
        ]
        
        action = self.select_option(actions, "Choose action")
        if not action or action == "Skip":
            return
        
        if action == "Keep newest":
            newest = max(paths, key=lambda p: p.stat().st_mtime)
            self._delete_except(paths, [newest])
        
        elif action == "Keep oldest":
            oldest = min(paths, key=lambda p: p.stat().st_mtime)
            self._delete_except(paths, [oldest])
        
        elif action == "Keep specific file":
            to_keep = self.select_option([str(p) for p in paths], "Select file to keep")
            if to_keep:
                keep_path = next(p for p in paths if str(p) == to_keep)
                self._delete_except(paths, [keep_path])
        
        elif action == "Delete all except one":
            to_keep = paths[0]  # Keep the first one by default
            self._delete_except(paths, [to_keep])
    
    def _delete_except(self, paths: List[Path], keep: List[Path]):
        """Delete all paths except the ones to keep."""
        for path in paths:
            if path not in keep:
                try:
                    if self.confirm_action(f"Delete {path}?"):
                        path.unlink()
                        console.print(f"[red]Deleted[/red] {path}")
                except OSError as e:
                    console.print(f"[red]Error[/red] deleting {path}: {e}")

class DirectoryManager(FileAction):
    """Handles directory operations like merging and renaming."""
    
    def merge_directories(self, source: Path, target: Path):
        """Merge source directory into target directory."""
        if not source.is_dir() or not target.is_dir():
            console.print("[red]Both paths must be directories[/red]")
            return
        
        if not self.confirm_action(f"Merge {source} into {target}?"):
            return
        
        try:
            # Create target directory if it doesn't exist
            target.mkdir(parents=True, exist_ok=True)
            
            # Move all contents from source to target
            for item in source.iterdir():
                dest = target / item.name
                if dest.exists():
                    if item.is_dir():
                        self.merge_directories(item, dest)
                    else:
                        if self.confirm_action(
                            f"{dest} already exists. Overwrite?"
                        ):
                            shutil.move(str(item), str(dest))
                else:
                    shutil.move(str(item), str(dest))
            
            # Remove empty source directory
            if not any(source.iterdir()):
                source.rmdir()
                console.print(f"[green]Successfully merged[/green] {source} into {target}")
        
        except OSError as e:
            console.print(f"[red]Error[/red] during merge: {e}")
    
    def rename_interactive(self, path: Path):
        """Rename a file or directory interactively."""
        if not path.exists():
            console.print("[red]Path does not exist[/red]")
            return
        
        new_name = Prompt.ask(
            "Enter new name",
            default=path.name
        )
        
        if not new_name or new_name == path.name:
            return
        
        try:
            new_path = path.parent / new_name
            if new_path.exists():
                if not self.confirm_action(
                    f"{new_path} already exists. Overwrite?"
                ):
                    return
            
            path.rename(new_path)
            console.print(
                f"[green]Successfully renamed[/green] {path.name} to {new_name}"
            )
        
        except OSError as e:
            console.print(f"[red]Error[/red] renaming {path}: {e}")

def interactive_mode(duplicates: Dict[str, List[Path]]):
    """Main interactive mode entry point."""
    console.print("[bold blue]Welcome to Interactive Mode[/bold blue]")
    
    while True:
        actions = [
            "Resolve duplicates",
            "Merge directories",
            "Rename files/directories",
            "Exit"
        ]
        
        action = FileAction.select_option(actions, "Choose action")
        if not action or action == "Exit":
            break
        
        if action == "Resolve duplicates":
            resolver = DuplicateResolver(duplicates)
            resolver.show_duplicates()
            for hash_value, paths in duplicates.items():
                resolver.resolve_group(hash_value, paths)
        
        elif action == "Merge directories":
            source = Prompt.ask("Enter source directory path")
            target = Prompt.ask("Enter target directory path")
            manager = DirectoryManager()
            manager.merge_directories(Path(source), Path(target))
        
        elif action == "Rename files/directories":
            path = Prompt.ask("Enter path to rename")
            manager = DirectoryManager()
            manager.rename_interactive(Path(path))
    
    console.print("[bold blue]Exiting Interactive Mode[/bold blue]") 