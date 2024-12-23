import argparse
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from .core.scanner import FileTreeScanner
from .core.duplicates import DuplicateFinder
from .utils.config import Config
from .utils.report import ReportGenerator
from .interactive import DuplicateResolver
from .analysis.directory_analyzer import DirectoryAnalyzer

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
    parser.add_argument(
        "--no-diagram",
        action="store_true",
        help="Skip generating directory relationship diagram"
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

def display_directory_analysis(analyzer: DirectoryAnalyzer, path: Path, metrics: dict):
    """Display directory analysis results."""
    # Create table for poorly organized directories
    poor_org_table = Table(title="📁 Poorly Organized Directories")
    poor_org_table.add_column("Directory")
    poor_org_table.add_column("Issues")
    poor_org_table.add_column("Score")
    
    for dir_path, dir_metrics in metrics.items():
        score = analyzer.get_organization_score(dir_metrics)
        if score < 70:  # Show directories with poor organization
            issues = []
            if dir_metrics.mixed_content_types:
                issues.append("Mixed content")
            if dir_metrics.deep_nesting:
                issues.append("Deep nesting")
            if dir_metrics.inconsistent_naming:
                issues.append("Inconsistent naming")
            if dir_metrics.large_directory:
                issues.append("Too many files")
            if dir_metrics.empty_directory:
                issues.append("Empty")
            
            poor_org_table.add_row(
                str(dir_path.relative_to(path)),
                ", ".join(issues),
                f"{score:.0f}/100"
            )
    
    console.print(poor_org_table)
    
    # Display large files
    large_files = analyzer.find_large_files(path)
    if large_files:
        large_files_table = Table(title="📦 Large Files")
        large_files_table.add_column("File")
        large_files_table.add_column("Size")
        
        for file_path, size in large_files[:10]:  # Show top 10 largest files
            large_files_table.add_row(
                str(file_path.relative_to(path)),
                f"{size / (1024*1024):.1f} MB"
            )
        
        console.print("\n", large_files_table)
    
    # Display directory sizes
    dir_sizes = analyzer.get_directory_sizes(path)
    size_table = Table(title="📊 Directory Sizes")
    size_table.add_column("Directory")
    size_table.add_column("Size")
    size_table.add_column("Files")
    
    # Sort directories by size
    sorted_dirs = sorted(
        ((p, s) for p, s in dir_sizes.items() if p != path),
        key=lambda x: x[1],
        reverse=True
    )
    
    for dir_path, size in sorted_dirs[:10]:  # Show top 10 largest directories
        metrics = metrics.get(dir_path)
        size_table.add_row(
            str(dir_path.relative_to(path)),
            f"{size / (1024*1024):.1f} MB",
            str(metrics.file_count) if metrics else "N/A"
        )
    
    console.print("\n", size_table)

def main(args=None) -> int:
    """Main entry point."""
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
        analyzer = DirectoryAnalyzer()
        
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
            
            # Analyze directory structure
            if not path.is_file():
                analysis_task = progress.add_task(
                    "[cyan]📊 Analyzing directory structure...",
                    total=None
                )
                metrics = analyzer.analyze_directory(path)
                progress.update(analysis_task, completed=True)
                
                # Generate relationship diagram
                if not args.no_diagram:
                    diagram_task = progress.add_task(
                        "[cyan]📐 Generating directory diagram...",
                        total=None
                    )
                    diagram_path = analyzer.generate_relationship_diagram(path)
                    progress.update(diagram_task, completed=True)
            
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
        
        # Display analysis results
        if not path.is_file():
            display_directory_analysis(analyzer, path, metrics)
            if not args.no_diagram:
                console.print(f"\n[green]Directory diagram saved to: {diagram_path}[/green]")
        
        # Display report
        try:
            console.print("\n", report)
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