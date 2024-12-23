import argparse
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .core.scanner import FileTreeScanner
from .core.duplicates import DuplicateFinder
from .utils.config import Config
from .utils.report import ReportGenerator
from .interactive import DuplicateResolver

console = Console()

def parse_args(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze file/directory structure and find duplicate files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  filetree                           # Run interactive prompt
  filetree path/to/directory         # Analyze specific directory
  filetree path/to/file.txt          # Analyze specific file
  filetree --interactive             # Enable interactive mode for duplicates
  filetree --export report.md        # Export report to markdown file
  filetree --min-size 1024           # Only consider files >= 1KB
  filetree --exclude "*.tmp" "*.log" # Exclude specific file patterns
        """
    )
    parser.add_argument(
        "path",
        type=str,
        help="File or directory path to analyze (if not provided, will prompt)",
        nargs="?",
        default=None
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

def get_path_from_user() -> Path:
    """Prompt user for a file or directory path."""
    while True:
        path_str = Prompt.ask(
            "\nEnter path to analyze",
            default="."
        )
        path = Path(path_str)
        
        if not path.exists():
            console.print(f"[red]Path not found: {path}[/red]")
            if not Prompt.ask("Would you like to try again?", default="y").lower().startswith("y"):
                raise KeyboardInterrupt()
            continue
            
        return path.resolve()

def main(args=None) -> int:
    """Main entry point.
    
    Args:
        args: Optional list of command line arguments. If None, sys.argv[1:] will be used.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    args = parse_args(args)
    
    try:
        # Get path from command line or prompt user
        path = Path(args.path) if args.path else get_path_from_user()
        
        if not path.exists():
            console.print(f"[red]Path not found: {path}[/red]")
            return 1
        
        # Initialize components
        config = Config()
        if args.exclude:
            config.ignore_patterns.extend(args.exclude)
        
        scanner = FileTreeScanner(config)
        
        # Create progress for operations
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True
        )
        
        with progress:
            # Scan path
            scan_task = progress.add_task(
                f"[cyan]🔍 Scanning {path.name}...",
                total=None
            )
            files = [path] if path.is_file() else scanner.scan_directory(path)
            progress.update(scan_task, completed=True)
            
            # Find duplicates
            duplicate_task = progress.add_task(
                "[cyan]🔍 Analyzing duplicates...",
                total=None
            )
            duplicate_finder = DuplicateFinder(min_size=args.min_size)
            duplicates = duplicate_finder.find_duplicates(files)
            progress.update(duplicate_task, completed=True)
            
            # Generate report
            report_task = progress.add_task(
                "[cyan]📊 Generating report...",
                total=None
            )
            report_gen = ReportGenerator()
            report = report_gen.generate_report(
                directory=path.parent if path.is_file() else path,
                files=files,
                duplicates=duplicates,
                config=config,
                show_tree=not args.no_tree
            )
            progress.update(report_task, completed=True)
        
        # Display report
        try:
            console.print(report)
        except UnicodeEncodeError:
            # Fall back to plain text if terminal doesn't support Unicode
            console.print(report.encode('ascii', 'replace').decode())
        
        # Export report if requested
        if args.export:
            export_path = Path(args.export)
            with progress:
                export_task = progress.add_task(
                    "[cyan]📝 Exporting report...",
                    total=None
                )
                try:
                    export_path.write_text(report, encoding='utf-8')
                    progress.update(export_task, completed=True)
                    console.print(f"\n[green]Report exported to: {export_path}[/green]")
                except Exception as e:
                    progress.update(export_task, completed=True)
                    console.print(f"[red]Error exporting report: {str(e)}[/red]")
                    return 1
        
        # Start interactive mode if requested
        if args.interactive and duplicates:
            resolver = DuplicateResolver(duplicates)
            resolver.start_interactive_session()
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    exit(main()) 