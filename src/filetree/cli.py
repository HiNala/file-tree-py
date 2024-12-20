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
    logger.debug("Logging initialized with level: %s", level)

def display_results(duplicates: dict, interactive: bool = False):
    """Display scan results."""
    logger.debug("Displaying results (interactive=%s)", interactive)
    if not duplicates:
        logger.debug("No duplicates found")
        console.print("[green]No duplicate files found.[/green]")
        return

    num_groups = len(duplicates)
    logger.debug("Found %d groups of duplicate files", num_groups)
    console.print(f"\nFound [bold]{num_groups}[/bold] groups of duplicate files.")
    
    for hash_value, paths in duplicates.items():
        logger.debug("Duplicate group (hash: %s) contains %d files", hash_value[:8], len(paths))
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

        logger.debug("Parsing command line arguments: %s", args)
        parser = argparse.ArgumentParser(description="Analyze directory structure and find duplicate files.")
        parser.add_argument("directory", help="Directory to analyze")
        parser.add_argument("-w", "--workers", type=int, help="Number of worker threads")
        parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode")
        parser.add_argument("--no-tree", action="store_true", help="Disable tree view")
        parser.add_argument("--export", help="Export results to file")
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

        args = parser.parse_args(args)
        setup_logging(args.verbose)
        directory = Path(args.directory)
        logger.debug("Target directory: %s", directory)

        if not directory.exists():
            logger.error("Directory does not exist: %s", directory)
            console.print(f"[red]Error: Directory '{directory}' does not exist.[/red]")
            return 1

        # Load configuration
        logger.debug("Loading configuration from file: %s", args.config if args.config else "default")
        config = FileTreeConfig.from_file(args.config) if args.config else FileTreeConfig()
        
        # Initialize scanner with config and optional worker count
        logger.debug("Initializing scanner with %s workers", args.workers or "default")
        scanner = FileScanner(config=config, num_workers=args.workers)
        
        console.print(f"Scanning directory: {directory}")
        
        # Find duplicates
        logger.debug("Starting duplicate file scan")
        duplicates = scanner.find_duplicates(directory)
        logger.debug("Scan complete, found %d duplicate groups", len(duplicates))
        
        # Display results
        display_results(duplicates, args.interactive)

        # Create visualizer for tree view or export
        logger.debug("Creating file tree visualizer")
        visualizer = FileTreeVisualizer()

        if not args.no_tree:
            logger.debug("Generating tree view")
            tree = visualizer.create_tree(directory, duplicates)
            console.print(tree)

        if args.export:
            export_path = Path(args.export)
            logger.debug("Exporting results to: %s", export_path)
            visualizer.export_results(duplicates, export_path)
            console.print(f"\n[green]Results exported to {export_path}[/green]")

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.error("An error occurred", exc_info=True)
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 