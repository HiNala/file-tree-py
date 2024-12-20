"""Interactive mode for managing duplicate files."""
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from .actions import FileAction

console = Console()

class DuplicateResolver:
    """Interactive resolver for duplicate files."""

    def __init__(self, duplicates: Dict[str, List[Path]]):
        """Initialize resolver with duplicate files."""
        self.duplicates = duplicates
        self.action_handler = FileAction()

    def start_interactive_session(self):
        """Start interactive session for managing duplicates."""
        if not self.duplicates:
            console.print("[yellow]No duplicate files to manage.[/yellow]")
            return

        console.print("\n[bold cyan]🔍 Interactive Duplicate Management[/bold cyan]")
        console.print("Review and manage duplicate files.\n")

        for hash_value, files in self.duplicates.items():
            if not files:
                continue

            console.print(f"\n[bold]Group with {len(files)} duplicates[/bold]")
            console.print("Files:")
            for i, file in enumerate(files, 1):
                console.print(f"{i}. {file}")

            while True:
                action = Prompt.ask(
                    "\nChoose action",
                    choices=["keep", "delete", "rename", "skip", "quit"],
                    default="skip"
                )

                if action == "quit":
                    console.print("\n[yellow]Exiting interactive mode[/yellow]")
                    return
                elif action == "skip":
                    break
                elif action == "keep":
                    self._handle_keep_action(files)
                elif action == "delete":
                    self._handle_delete_action(files)
                elif action == "rename":
                    self._handle_rename_action(files)

    def _handle_keep_action(self, files: List[Path]):
        """Handle keep action for duplicate files."""
        console.print("\nSelect file to keep (others will be deleted):")
        for i, file in enumerate(files, 1):
            console.print(f"{i}. {file}")

        choice = Prompt.ask("Enter number", choices=[str(i) for i in range(1, len(files) + 1)])
        keep_index = int(choice) - 1
        keep_file = files[keep_index]

        if Confirm.ask(f"Keep {keep_file} and delete others?"):
            for i, file in enumerate(files):
                if i != keep_index:
                    try:
                        self.action_handler.delete_file(file)
                        console.print(f"[green]Deleted: {file}[/green]")
                    except Exception as e:
                        console.print(f"[red]Error deleting {file}: {e}[/red]")

    def _handle_delete_action(self, files: List[Path]):
        """Handle delete action for duplicate files."""
        console.print("\nSelect files to delete (comma-separated numbers, or 'all'):")
        for i, file in enumerate(files, 1):
            console.print(f"{i}. {file}")

        choice = Prompt.ask("Enter numbers or 'all'")
        if choice.lower() == "all":
            indices = range(len(files))
        else:
            indices = [int(i) - 1 for i in choice.split(",")]

        for index in indices:
            try:
                self.action_handler.delete_file(files[index])
                console.print(f"[green]Deleted: {files[index]}[/green]")
            except Exception as e:
                console.print(f"[red]Error deleting {files[index]}: {e}[/red]")

    def _handle_rename_action(self, files: List[Path]):
        """Handle rename action for duplicate files."""
        console.print("\nSelect file to rename:")
        for i, file in enumerate(files, 1):
            console.print(f"{i}. {file}")

        choice = Prompt.ask("Enter number", choices=[str(i) for i in range(1, len(files) + 1)])
        file_index = int(choice) - 1
        file = files[file_index]

        new_name = Prompt.ask("Enter new name")
        try:
            new_path = file.parent / new_name
            self.action_handler.rename_file(file, new_path)
            console.print(f"[green]Renamed {file} to {new_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error renaming file: {e}[/red]")

__all__ = ['DuplicateResolver'] 