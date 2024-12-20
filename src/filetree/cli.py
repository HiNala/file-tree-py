import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from .core.scanner import FileScanner
from .visualization.tree_view import FileTreeVisualizer
from .utils.config import FileTreeConfig
import sys

logger = logging.getLogger(__name__)
console = Console()

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

def display_results(duplicates: dict, interactive: bool = False):
    """Display scan results."""
    if not duplicates:
        console.print("[green]No duplicate files found.[/green]")
        return

    duplicate_groups = len(duplicates)
    console.print(f"[yellow]Found {duplicate_groups} group(s) of duplicate files.[/yellow]")
    
    for hash_value, paths in duplicates.items():
        console.print(f"\n[bold]Duplicate group (hash: {hash_value[:8]})[/bold]")
        for path in paths:
            console.print(f"  {path}")

    if not interactive:
        console.print("\n[blue]Tip: Use --interactive (-i) to manage duplicates.[/blue]")

def main(args=None):
    """Main entry point for the file tree analyzer."""
    try:
        if args is None:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(description="Analyze directory structure and find duplicate files.")
        parser.add_argument("directory", help="Directory to analyze")
        parser.add_argument("-w", "--workers", type=int, help="Number of worker threads")
        parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode")
        parser.add_argument("--no-tree", action="store_true", help="Disable tree view")
        parser.add_argument("--export", help="Export results to file")
        parser.add_argument("--config", help="Path to configuration file")

        args = parser.parse_args(args)
        directory = Path(args.directory)

        if not directory.exists():
            console.print(f"[red]Error: Directory '{directory}' does not exist.[/red]")
            return 1

        scanner = FileScanner(args.workers)
        duplicates = scanner.find_duplicates(directory)
        display_results(duplicates)

        if args.interactive:
            interactive_mode(duplicates)

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error("An error occurred", exc_info=True)
        return 1

if __name__ == "__main__":
    main() 