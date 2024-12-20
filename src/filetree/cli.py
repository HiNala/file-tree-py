import argparse
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
import json

from .core.scanner import FileScanner
from .core.route_analyzer import RouteAnalyzer
from .visualization.tree_view import FileTreeVisualizer
from .utils.config import FileTreeConfig

def setup_logging(debug_mode: bool):
    """Configure logging based on debug mode."""
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def export_results(data: dict, output_file: str):
    """Export results to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze directory structures and detect duplicate files."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to analyze"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--no-tree",
        action="store_true",
        help="Skip tree visualization"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        help="Similarity threshold for route analysis (default: 0.8)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export results to JSON file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    args = parser.parse_args()

    # Load configuration
    config = (FileTreeConfig.from_file(Path(args.config)) 
             if args.config 
             else FileTreeConfig.default())
    
    # Override config with CLI arguments
    if args.similarity_threshold is not None:
        config.similarity_threshold = args.similarity_threshold
    
    if args.debug:
        config.debug_mode = True
    
    # Setup logging
    setup_logging(config.debug_mode)
    
    # Initialize console
    console = Console()

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Error: {directory} is not a valid directory[/red]")
        return 1

    # Scan directory
    console.print(f"\n[bold blue]Scanning directory: {directory}[/bold blue]")
    scanner = FileScanner(directory)
    scanner.scan()
    
    # Analyze routes
    console.print("\n[bold blue]Analyzing directory structure...[/bold blue]")
    route_analyzer = RouteAnalyzer(directory, threshold=config.similarity_threshold)
    route_analyzer.analyze()
    
    # Collect results for potential export
    results = {
        "duplicates": {},
        "similar_routes": [],
        "stats": {
            "total_files": len(scanner.scanned_files),
            "duplicate_files": sum(len(paths) for paths in scanner.get_duplicates().values())
        }
    }
    
    # Show tree visualization
    if not args.no_tree:
        console.print("\n[bold blue]Directory Structure:[/bold blue]")
        visualizer = FileTreeVisualizer(console, config)
        tree = visualizer.create_tree(directory, scanner.get_duplicates())
        console.print(tree)
    
    # Display and collect duplicates
    duplicates = scanner.get_duplicates()
    if duplicates:
        console.print("\n[bold red]Duplicate files found:[/bold red]")
        table = Table(show_header=True)
        table.add_column("Hash", style="dim")
        table.add_column("Duplicate Files", style="red")
        
        for file_hash, paths in duplicates.items():
            table.add_row(
                file_hash[:8] + "...",
                "\n".join(str(p) for p in paths)
            )
            results["duplicates"][file_hash] = [str(p) for p in paths]
        
        console.print(table)
    
    # Display and collect similar routes
    similar_routes = route_analyzer.get_similar_routes()
    if similar_routes:
        console.print("\n[bold yellow]Similar directory structures found:[/bold yellow]")
        table = Table(show_header=True)
        table.add_column("Route 1", style="cyan")
        table.add_column("Route 2", style="cyan")
        table.add_column("Similarity", style="green")
        
        for path1, path2, similarity in similar_routes:
            table.add_row(
                str(path1.relative_to(directory)),
                str(path2.relative_to(directory)),
                f"{similarity:.2%}"
            )
            results["similar_routes"].append({
                "route1": str(path1.relative_to(directory)),
                "route2": str(path2.relative_to(directory)),
                "similarity": similarity
            })
    
    # Export results if requested
    if args.export:
        export_results(results, args.export)
        console.print(f"\n[green]Results exported to {args.export}[/green]")

    return 0

if __name__ == "__main__":
    exit(main()) 