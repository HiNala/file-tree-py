import argparse
from pathlib import Path
from typing import Optional, List
from rich.console import Console

from .core.scanner import FileTreeScanner
from .core.duplicates import DuplicateFinder
from .utils.config import Config
from .utils.report import ReportGenerator
from .interactive import DuplicateResolver

console = Console()

def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze directory structure and find duplicate files"
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to analyze",
        nargs="?",
        default="."
    )
    parser.add_argument(
        "--no-tree",
        action="store_true",
        help="Skip directory tree visualization"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode for managing duplicates"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export report to file (markdown format)"
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=1,
        help="Minimum file size to consider (in bytes)"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        help="Patterns to exclude (glob format)"
    )
    return parser.parse_args(args)

def main(args=None) -> int:
    """Main entry point.
    
    Args:
        args: Optional list of command line arguments. If None, sys.argv[1:] will be used.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    args = parse_args(args)
    directory = Path(args.directory)
    
    if not directory.exists():
        console.print(f"[red]Directory not found: {directory}[/red]")
        return 1
    
    try:
        # Initialize components
        config = Config()
        if args.exclude:
            config.ignore_patterns.extend(args.exclude)
        
        scanner = FileTreeScanner(config)
        
        # Scan directory
        console.print("\n[bold cyan]🔍 Scanning directory...[/bold cyan]")
        files = scanner.scan_directory(directory)
        
        # Find duplicates
        console.print("[bold cyan]🔍 Analyzing duplicates...[/bold cyan]")
        duplicate_finder = DuplicateFinder(min_size=args.min_size)
        duplicates = duplicate_finder.find_duplicates(files)
        
        # Generate and display report
        report_gen = ReportGenerator()
        report = report_gen.generate_report(
            directory=directory,
            files=files,
            duplicates=duplicates,
            config=config,
            show_tree=not args.no_tree
        )
        
        try:
            console.print(report)
        except UnicodeEncodeError:
            # Fall back to plain text if terminal doesn't support Unicode
            console.print(report.encode('ascii', 'replace').decode())
        
        # Export report if requested
        if args.export:
            export_path = Path(args.export)
            try:
                export_path.write_text(report, encoding='utf-8')
                console.print(f"\n[green]Report exported to: {export_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error exporting report: {str(e)}[/red]")
                return 1
        
        # Start interactive mode if requested
        if args.interactive and duplicates:
            resolver = DuplicateResolver(duplicates)
            resolver.start_interactive_session()
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    exit(main()) 