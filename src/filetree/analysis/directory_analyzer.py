"""Directory analysis and visualization module."""
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import graphviz
from rich.tree import Tree
from rich.filesize import decimal_prefix

@dataclass
class DirectoryMetrics:
    """Metrics for directory organization analysis."""
    mixed_content_types: bool = False  # Different file types in same dir
    deep_nesting: bool = False         # Deeply nested directories
    inconsistent_naming: bool = False  # Inconsistent file naming
    large_directory: bool = False      # Too many files in one dir
    empty_directory: bool = False      # Directory with no files
    size: int = 0                      # Total size in bytes
    file_count: int = 0               # Number of files
    subdir_count: int = 0             # Number of subdirectories

class DirectoryAnalyzer:
    """Analyzer for directory structure and organization."""

    def __init__(self, 
                 max_files_per_dir: int = 100,
                 max_nesting_level: int = 5,
                 large_file_threshold: int = 100 * 1024 * 1024  # 100MB
                ):
        """Initialize analyzer with thresholds."""
        self.max_files_per_dir = max_files_per_dir
        self.max_nesting_level = max_nesting_level
        self.large_file_threshold = large_file_threshold
        self.diagrams_dir = Path("Diagrams")

    def analyze_directory(self, path: Path) -> Dict[Path, DirectoryMetrics]:
        """Analyze directory structure and return metrics for each directory."""
        metrics: Dict[Path, DirectoryMetrics] = {}
        
        for root, dirs, files in os.walk(path):
            root_path = Path(root)
            current_metrics = DirectoryMetrics()
            
            # Calculate basic metrics
            current_metrics.file_count = len(files)
            current_metrics.subdir_count = len(dirs)
            
            # Check file sizes and calculate total
            for file in files:
                file_path = root_path / file
                try:
                    size = file_path.stat().st_size
                    current_metrics.size += size
                except OSError:
                    continue
            
            # Check organization issues
            current_metrics.large_directory = len(files) > self.max_files_per_dir
            current_metrics.empty_directory = len(files) == 0 and len(dirs) == 0
            current_metrics.deep_nesting = len(root_path.parts) > self.max_nesting_level
            
            # Check for mixed content
            extensions = {Path(f).suffix.lower() for f in files if Path(f).suffix}
            current_metrics.mixed_content_types = len(extensions) > 3
            
            # Check naming consistency
            name_patterns = {self._get_name_pattern(f) for f in files}
            current_metrics.inconsistent_naming = len(name_patterns) > 2
            
            metrics[root_path] = current_metrics
        
        return metrics

    def find_large_files(self, path: Path, min_size: int = None) -> List[Tuple[Path, int]]:
        """Find all large files above the threshold."""
        min_size = min_size or self.large_file_threshold
        large_files = []
        
        for root, _, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                try:
                    size = file_path.stat().st_size
                    if size >= min_size:
                        large_files.append((file_path, size))
                except OSError:
                    continue
        
        return sorted(large_files, key=lambda x: x[1], reverse=True)

    def get_directory_sizes(self, path: Path) -> Dict[Path, int]:
        """Calculate sizes for all directories."""
        dir_sizes: Dict[Path, int] = {}
        
        for root, _, files in os.walk(path):
            root_path = Path(root)
            size = 0
            
            for file in files:
                try:
                    size += (root_path / file).stat().st_size
                except OSError:
                    continue
            
            dir_sizes[root_path] = size
            
            # Add size to all parent directories
            parent = root_path.parent
            while parent >= path:
                dir_sizes[parent] = dir_sizes.get(parent, 0) + size
                parent = parent.parent
        
        return dir_sizes

    def generate_relationship_diagram(self, path: Path) -> Path:
        """Generate a directory relationship diagram using graphviz."""
        # Create diagrams directory if it doesn't exist
        diagram_subdir = self.diagrams_dir / path.name
        diagram_subdir.mkdir(parents=True, exist_ok=True)
        
        # Create a new directed graph
        dot = graphviz.Digraph(
            comment=f'Directory Structure: {path.name}',
            format='png'
        )
        dot.attr(rankdir='LR')  # Left to right layout
        
        # Add nodes and edges
        added_nodes: Set[str] = set()
        dir_sizes = self.get_directory_sizes(path)
        
        for current_path, size in dir_sizes.items():
            if current_path < path:
                continue
                
            # Create node for current path
            node_id = str(current_path)
            if node_id not in added_nodes:
                label = f"{current_path.name}\\n{decimal_prefix(size)}"
                dot.node(node_id, label)
                added_nodes.add(node_id)
            
            # Create edge to parent
            parent = current_path.parent
            if parent >= path:
                dot.edge(str(parent), node_id)
        
        # Save the diagram
        timestamp = path.stat().st_mtime
        diagram_path = diagram_subdir / f"relationship_diagram_{int(timestamp)}.png"
        dot.render(diagram_path.with_suffix(''), cleanup=True)
        
        return diagram_path

    def _get_name_pattern(self, filename: str) -> str:
        """Get a simplified pattern for filename."""
        parts = []
        for char in filename:
            if char.isupper():
                parts.append('A')
            elif char.islower():
                parts.append('a')
            elif char.isdigit():
                parts.append('0')
            else:
                parts.append(char)
        return ''.join(parts)

    def get_organization_score(self, metrics: DirectoryMetrics) -> float:
        """Calculate an organization score (0-100) for a directory."""
        score = 100.0
        
        if metrics.mixed_content_types:
            score -= 20
        if metrics.deep_nesting:
            score -= 15
        if metrics.inconsistent_naming:
            score -= 20
        if metrics.large_directory:
            score -= 25
        if metrics.empty_directory:
            score -= 10
            
        return max(0, score) 