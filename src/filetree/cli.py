import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from .core.scanner import FileScanner
from .visualization.tree_view import FileTreeVisualizer
from .utils.config import FileTreeConfig
from .utils.report import AnalysisReport
import sys
from typing import Dict, List
from .interactive import interactive_mode
from datetime import datetime

logger = logging.getLogger(__name__)
console = Console()

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                log_time_format="%H:%M:%S",
                show_path=False,
                omit_repeated_times=True
            )
        ]
    )
    logger.debug("[bold blue]File Tree Analyzer Started[/bold blue]")

def display_results(duplicates: Dict[str, List[str]], interactive: bool = False):
    """Display the results of the file analysis."""
    if not duplicates:
        console.print("[green]No duplicate files found.[/green]")
        return

    total_groups = len(duplicates)
    total_duplicates = sum(len(paths) - 1 for paths in duplicates.values())
    
    # Calculate total size safely
    total_size = 0
    for paths in duplicates.values():
        try:
            if paths:  # Check if there are any paths
                file_size = Path(paths[0]).stat().st_size
                total_size += file_size * (len(paths) - 1)
        except (OSError, FileNotFoundError):
            # Skip files that can't be accessed
            continue

    # Display summary
    console.print("\n[bold cyan]📊 Analysis Summary[/bold cyan]")
    console.print(f"\nFound [bold]{total_groups}[/bold] groups of duplicate files")
    console.print(f"Total duplicate files: {total_duplicates}")
    console.print(f"[cyan]Wasted space: {format_size(total_size)}[/cyan]\n")

    if interactive:
        console.print("[bold yellow]🔍 Interactive Mode[/bold yellow]")
        console.print("Review each group of duplicates and choose actions.\n")
        interactive_mode(duplicates)
    else:
        # Show preview of duplicates
        console.print("[bold green]🗂️  Duplicate File Groups Preview[/bold green]")
        console.print("Showing first 5 groups (use -i for interactive mode)\n")
        
        for i, (hash_value, paths) in enumerate(list(duplicates.items())[:5]):
            try:
                size = Path(paths[0]).stat().st_size if paths else 0
                console.print(f"[bold]Group {i+1}[/bold] ({format_size(size)} each):")
                for path in paths:
                    console.print(f"  • {path}")
                console.print()
            except (OSError, FileNotFoundError):
                # Skip groups where files can't be accessed
                continue

        if len(duplicates) > 5:
            remaining = len(duplicates) - 5
            console.print(f"[dim]... and {remaining} more groups[/dim]")

        # Show tip for interactive mode
        console.print("\n[yellow]💡 Tip: Use --interactive (-i) flag to manage duplicate files[/yellow]")
        console.print("[yellow]    Example: python main.py . -i[/yellow]")

def calculate_wasted_space(duplicates: dict) -> str:
    """Calculate total wasted space from duplicates."""
    total_bytes = 0
    for paths in duplicates.values():
        if len(paths) > 1:  # Only count actual duplicates
            file_size = Path(paths[0]).stat().st_size
            total_bytes += file_size * (len(paths) - 1)  # Count space wasted by duplicates
    return format_size(total_bytes)

def format_size(size_in_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

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
        parser.add_argument("--report", help="Generate detailed analysis report (markdown format)")

        try:
            parsed_args = parser.parse_args(args)
            logger.debug("Parsed arguments: %s", vars(parsed_args))
        except SystemExit as e:
            if e.code == 0:
                return 0
            parsed_args = parser.parse_args([])
            parsed_args.directory = None

        setup_logging(getattr(parsed_args, 'verbose', False))

        if not parsed_args.directory:
            try:
                parsed_args.directory = prompt_for_directory()
                logger.debug("Directory provided via prompt: %s", parsed_args.directory)
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user[/yellow]")
                return 130

        directory = Path(parsed_args.directory)
        if not directory.exists():
            error_msg = f"Directory '{directory}' does not exist."
            logger.error(error_msg)
            console.print(f"[red]Error: {error_msg}[/red]")
            return 1

        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate report filename with timestamp and directory name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = directory.name or "root"
        report_filename = f"report_{dir_name}_{timestamp}.md"
        report_path = reports_dir / report_filename

        # Initialize report
        report = AnalysisReport(directory)
        
        # Load configuration
        config = FileTreeConfig.from_file(parsed_args.config) if parsed_args.config else FileTreeConfig()
        logger.debug("Configuration loaded: %s", config)
        
        # Initialize scanner
        scanner = FileScanner(config=config, num_workers=parsed_args.workers)
        
        console.print(f"\nScanning directory: {directory}")
        
        # Find duplicates and collect statistics
        duplicates = scanner.find_duplicates(directory)
        
        # Update report statistics
        total_size = sum(Path(path).stat().st_size for paths in duplicates.values() for path in paths)
        wasted_space = sum((len(paths) - 1) * Path(paths[0]).stat().st_size for paths in duplicates.values())
        
        report.update_statistics({
            "total_files": sum(len(paths) for paths in duplicates.values()),
            "total_size": total_size,
            "duplicate_groups": len(duplicates),
            "wasted_space": wasted_space
        })

        # Add findings for duplicate groups
        for hash_value, paths in duplicates.items():
            if len(paths) > 1:
                size = Path(paths[0]).stat().st_size
                report.add_finding(
                    "Duplicates",
                    f"Found {len(paths)} duplicate files of size {format_size(size)}",
                    "warning" if size > 1024*1024 else "info"  # Warn for files over 1MB
                )

        # Check for large files
        for paths in duplicates.values():
            for path in paths:
                size = Path(path).stat().st_size
                if size > 100 * 1024 * 1024:  # 100MB
                    report.statistics["large_files"].append({
                        "path": str(path),
                        "size": size
                    })

        # Add recommendations
        if duplicates:
            report.add_recommendation("Use interactive mode (-i) to manage duplicate files")
            report.add_recommendation("Consider using symbolic links for duplicate files")
            if any(len(p) > 1 for p in duplicates.values()):
                report.add_recommendation("Review duplicate files to free up disk space")

        # Initialize visualizer
        visualizer = FileTreeVisualizer()

        # Display results
        display_results(duplicates, parsed_args.interactive)

        # Generate tree view
        if not parsed_args.no_tree:
            tree = visualizer.create_tree(directory, duplicates)
            console.print(tree)

        # Export results if requested
        if parsed_args.export:
            export_path = Path(parsed_args.export)
            visualizer.export_results(duplicates, export_path)
            console.print(f"\n[green]Results exported to {export_path}[/green]")

        # Always generate report
        report.generate_markdown(report_path)
        console.print(f"\n[blue]Analysis report generated: {report_path}[/blue]")

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 130
    except Exception as e:
        logger.error("An error occurred", exc_info=True)
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 