from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import difflib

class RouteAnalyzer:
    """Analyzes directory structures to find similar or duplicate routes."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.routes: Dict[str, List[Path]] = defaultdict(list)
        self.similar_routes: List[Tuple[Path, Path, float]] = []
    
    def analyze(self) -> None:
        """Analyze directory structure for similar routes."""
        # First, collect all directory paths
        for path in self.root_path.rglob('*'):
            if path.is_dir():
                # Get relative path pattern (e.g., "src/utils", "lib/utils")
                relative = path.relative_to(self.root_path)
                pattern = '/'.join(part for part in relative.parts)
                if pattern:
                    self.routes[pattern].append(path)
        
        # Find similar route patterns
        patterns = list(self.routes.keys())
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i+1:]:
                similarity = difflib.SequenceMatcher(None, pattern1, pattern2).ratio()
                if similarity > 0.8:  # Adjust threshold as needed
                    for path1 in self.routes[pattern1]:
                        for path2 in self.routes[pattern2]:
                            self.similar_routes.append((path1, path2, similarity))
    
    def get_duplicate_routes(self) -> List[Tuple[str, List[Path]]]:
        """Get routes that appear multiple times."""
        return [
            (pattern, paths) 
            for pattern, paths in self.routes.items() 
            if len(paths) > 1
        ]
    
    def get_similar_routes(self) -> List[Tuple[Path, Path, float]]:
        """Get routes that have similar patterns."""
        return sorted(self.similar_routes, key=lambda x: x[2], reverse=True) 