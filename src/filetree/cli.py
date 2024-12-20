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

def prompt_for_directory() -> str:
    """Prompt user for directory path."""
    console.print("\n[bold blue]File Tree Analyzer[/bold blue]")
    console.print("Please enter the directory path to analyze.")
    console.print("You can either:")
    console.print("  1. Type '.' for the current directory")
    console.print("  2. Paste a full directory path")
    console.print("  3. Press Ctrl+C to exit\n")
    
    try:
        directory = input("Directory path: ").strip()
        return directory if directory else "."
    except KeyboardInterrupt:
        print()  # Add newline after ^C
        raise

def main(args=None):
    """Main entry point for the file tree analyzer."""
    try:
        if args is None:
            args = sys.argv[1:]
        
        logger.debug("Raw arguments received: %s", args)
        logger.debug("Number of arguments: %d", len(args))

        parser = argparse.ArgumentParser(
            description="Analyze directory structure and find duplicate files.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s .                     # Analyze current directory
  %(prog)s /path/to/dir -v       # Analyze with verbose logging
  %(prog)s . -i                  # Run in interactive mode
  %(prog)s . --export report.txt # Export results to file
            """
        )
        parser.add_argument("directory", nargs="?", help="Directory to analyze (optional, will prompt if not provided)")
        parser.add_argument("-w", "--workers", type=int, help="Number of worker threads")
        parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode")
        parser.add_argument("--no-tree", action="store_true", help="Disable tree view")
        parser.add_argument("--export", help="Export results to file")
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

        try:
            logger.debug("Parsing arguments with argparse")
            parsed_args = parser.parse_args(args)
            logger.debug("Parsed arguments: %s", vars(parsed_args))
        except SystemExit as e:
            # Only show help text for --help
            if e.code == 0:
                return 0
            # For other errors, continue to prompt for directory
            parsed_args = parser.parse_args([])
            parsed_args.directory = None

        # Set up logging early so we can see debug messages
        setup_logging(getattr(parsed_args, 'verbose', False))

        # If no directory specified, prompt for it
        if not parsed_args.directory:
            try:
                parsed_args.directory = prompt_for_directory()
                logger.debug("Directory provided via prompt: %s", parsed_args.directory)
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user[/yellow]")
                return 130

        directory = Path(parsed_args.directory)
        logger.debug("Target directory: %s", directory)
        logger.debug("Directory exists: %s", directory.exists())
        logger.debug("Directory is absolute: %s", directory.is_absolute())

        if not directory.exists():
            error_msg = f"Directory '{directory}' does not exist."
            logger.error(error_msg)
            console.print(f"[red]Error: {error_msg}[/red]")
            return 1

        # Load configuration
        logger.debug("Loading configuration from file: %s", parsed_args.config if parsed_args.config else "default")
        config = FileTreeConfig.from_file(parsed_args.config) if parsed_args.config else FileTreeConfig()
        logger.debug("Configuration loaded: %s", config)
        
        # Initialize scanner with config and optional worker count
        logger.debug("Initializing scanner with %s workers", parsed_args.workers or "default")
        scanner = FileScanner(config=config, num_workers=parsed_args.workers)
        
        console.print(f"\nScanning directory: {directory}")
        
        # Find duplicates
        logger.debug("Starting duplicate file scan")
        duplicates = scanner.find_duplicates(directory)
        logger.debug("Scan complete, found %d duplicate groups", len(duplicates))
        
        # Display results
        display_results(duplicates, parsed_args.interactive)

        # Create visualizer for tree view or export
        logger.debug("Creating file tree visualizer")
        visualizer = FileTreeVisualizer()

        if not parsed_args.no_tree:
            logger.debug("Generating tree view")
            tree = visualizer.create_tree(directory, duplicates)
            console.print(tree)

        if parsed_args.export:
            export_path = Path(parsed_args.export)
            logger.debug("Exporting results to: %s", export_path)
            visualizer.export_results(duplicates, export_path)
            console.print(f"\n[green]Results exported to {export_path}[/green]")

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error("An error occurred", exc_info=True)
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 