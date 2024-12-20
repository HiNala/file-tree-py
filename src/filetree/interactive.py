"""Interactive mode for managing duplicate files."""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()

def handle_interactive(duplicates: Dict[str, List[str]]) -> None:
    """Handle interactive mode for managing duplicate files.
    
    Args:
        duplicates: Dictionary mapping hash values to lists of duplicate file paths
    """
    if not duplicates:
        console.print("[yellow]No duplicate files to manage.[/yellow]")
        return

    # Show welcome message and instructions
    show_welcome_message()
    
    # Process each group of duplicates
    for hash_value, paths in duplicates.items():
        if len(paths) <= 1:
            continue
            
        # Show group information
        show_group_info(paths)
        
        while True:
            action = get_user_action()
            
            if action == 'skip':
                break
            elif action == 'delete':
                handle_delete(paths)
                break
            elif action == 'symlink':
                handle_symlink(paths)
                break
            elif action == 'help':
                show_help()
            elif action == 'quit':
                console.print("\n[yellow]Exiting interactive mode...[/yellow]")
                return

def show_welcome_message():
    """Display welcome message and basic instructions."""
    welcome = Panel.fit(
        "[bold green]Welcome to Interactive Mode![/bold green]\n\n"
        "Here you can manage duplicate files by:\n"
        "• Deleting redundant copies\n"
        "• Creating symbolic links\n"
        "• Skipping to the next group\n\n"
        "Type [bold cyan]help[/bold cyan] at any prompt for more information.",
        title="File Tree Analyzer",
        border_style="blue"
    )
    console.print(welcome)
    console.print()

def show_group_info(paths: List[str]):
    """Display information about a group of duplicate files."""
    size = Path(paths[0]).stat().st_size
    
    table = Table(title=f"Duplicate Files ({format_size(size)} each)", show_header=True)
    table.add_column("Index", style="cyan", no_wrap=True)
    table.add_column("Path", style="blue")
    table.add_column("Last Modified", style="green")
    
    for i, path in enumerate(paths, 1):
        p = Path(path)
        mtime = p.stat().st_mtime
        mtime_str = format_timestamp(mtime)
        table.add_row(str(i), str(p), mtime_str)
    
    console.print(table)
    console.print()

def get_user_action() -> str:
    """Get the user's desired action for handling duplicates."""
    choices = {
        'd': 'delete',
        's': 'symlink',
        'n': 'skip',
        'h': 'help',
        'q': 'quit'
    }
    
    prompt = (
        "[bold cyan]What would you like to do?[/bold cyan]\n"
        "[d]elete • create [s]ymlink • [n]ext group • [h]elp • [q]uit\n"
        "Choice"
    )
    
    while True:
        choice = Prompt.ask(prompt, choices=list(choices.keys()) + list(choices.values()))
        action = choices.get(choice, choice)
        if action in choices.values():
            return action
        console.print("[red]Invalid choice. Please try again.[/red]")

def handle_delete(paths: List[str]):
    """Handle deletion of duplicate files."""
    console.print("\n[bold]Select files to keep (comma-separated indices):[/bold]")
    console.print("Example: 1,3 (keeps files 1 and 3, deletes others)")
    
    while True:
        indices_str = Prompt.ask("Files to keep")
        try:
            # Parse indices, accounting for both comma and space separation
            indices = [int(i.strip()) for i in indices_str.replace(' ', ',').split(',')]
            if not indices:
                raise ValueError("No indices provided")
            if not all(1 <= i <= len(paths) for i in indices):
                raise ValueError("Invalid indices")
            break
        except ValueError as e:
            console.print(f"[red]Error: {str(e)}. Please try again.[/red]")
    
    # Confirm deletion
    to_delete = [p for i, p in enumerate(paths, 1) if i not in indices]
    if not Confirm.ask(f"\nDelete {len(to_delete)} files?"):
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return
    
    # Perform deletion
    with console.status("[bold green]Deleting files..."):
        for path in to_delete:
            try:
                Path(path).unlink()
                console.print(f"[green]Deleted: {path}[/green]")
            except Exception as e:
                console.print(f"[red]Error deleting {path}: {e}[/red]")

def handle_symlink(paths: List[str]):
    """Handle creation of symbolic links for duplicate files."""
    console.print("\n[bold]Select the source file (index):[/bold]")
    console.print("This file will be kept, others will be replaced with symbolic links")
    
    while True:
        try:
            idx = int(Prompt.ask("Source file index"))
            if not 1 <= idx <= len(paths):
                raise ValueError("Invalid index")
            break
        except ValueError:
            console.print("[red]Invalid index. Please enter a number between "
                         f"1 and {len(paths)}.[/red]")
    
    source = paths[idx - 1]
    to_link = [p for i, p in enumerate(paths) if i != idx - 1]
    
    # Confirm symlink creation
    if not Confirm.ask(f"\nCreate {len(to_link)} symbolic links?"):
        console.print("[yellow]Symlink creation cancelled.[/yellow]")
        return
    
    # Create symbolic links
    with console.status("[bold green]Creating symbolic links..."):
        for path in to_link:
            try:
                target = Path(path)
                target.unlink()
                target.symlink_to(source)
                console.print(f"[green]Created symlink: {path} -> {source}[/green]")
            except Exception as e:
                console.print(f"[red]Error creating symlink for {path}: {e}[/red]")

def show_help():
    """Display help information."""
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

[bold]delete (d)[/bold]
  Delete duplicate files while keeping selected ones.
  You'll be prompted to choose which files to keep.

[bold]symlink (s)[/bold]
  Replace duplicate files with symbolic links to a single source file.
  This saves space while maintaining file access.

[bold]next (n)[/bold]
  Skip to the next group of duplicate files.

[bold]help (h)[/bold]
  Show this help message.

[bold]quit (q)[/bold]
  Exit interactive mode.

[bold cyan]Tips:[/bold cyan]
• Use symbolic links to save space while keeping files accessible
• Always verify your selection before confirming deletions
• Consider file timestamps when choosing which copies to keep
"""
    console.print(Panel(help_text, title="Help", border_style="blue"))

def format_size(size: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def format_timestamp(timestamp: float) -> str:
    """Format timestamp in human readable format."""
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S") 