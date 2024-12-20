import sys
import argparse
from pathlib import Path
from rich.console import Console
from .core.scanner import FileScanner
from .interactive.actions import interactive_mode

console = Console()

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Analyze directory structures and manage duplicates."
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to analyze"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enable interactive mode for managing duplicates and directories"
    )
    
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=None,
        help="Number of worker threads for parallel processing"
    )
    
    return parser

def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        directory = Path(args.directory)
        if not directory.is_dir():
            console.print(f"[red]Error:[/red] {directory} is not a directory")
            sys.exit(1)
        
        # Initialize scanner with optional worker count
        scanner = FileScanner(str(directory), max_workers=args.workers)
        
        with console.status("[bold green]Scanning directory..."):
            scanner.scan()
        
        duplicates = scanner.get_duplicates()
        
        if not duplicates:
            console.print("[green]No duplicate files found.[/green]")
            return
        
        console.print(f"\n[yellow]Found {len(duplicates)} groups of duplicate files:[/yellow]")
        
        if args.interactive:
            interactive_mode(duplicates)
        else:
            # Display duplicates in non-interactive mode
            for hash_value, paths in duplicates.items():
                console.print(f"\n[cyan]Duplicate group (hash: {hash_value[:8]}):[/cyan]")
                for path in paths:
                    size = path.stat().st_size
                    console.print(f"  {path} ({size:,} bytes)")
            
            console.print("\n[blue]Tip:[/blue] Use --interactive flag to manage duplicates")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 