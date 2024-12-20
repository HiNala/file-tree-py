from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import difflib

class RouteAnalyzer:
    """Analyze directory routes for similarity."""

    def __init__(self, root_path: Path, similarity_threshold: float = 0.8):
        """Initialize the route analyzer."""
        self.root_path = root_path
        self.similarity_threshold = similarity_threshold
        self.routes = []

    def find_similar_routes(self) -> List[Tuple[str, str, float]]:
        """Find similar directory routes based on path similarity."""
        self.routes = [
            str(p.relative_to(self.root_path))
            for p in self.root_path.rglob("*")
            if p.is_dir()
        ]

        similar_routes = []
        for i, route1 in enumerate(self.routes):
            for route2 in self.routes[i + 1:]:
                similarity = self._compute_similarity(route1, route2)
                if similarity >= self.similarity_threshold:
                    similar_routes.append((route1, route2, similarity))

        return similar_routes

    def _compute_similarity(self, path1: str, path2: str) -> float:
        """Compute similarity between two paths using Levenshtein distance."""
        if not path1 or not path2:
            return 0.0

        # Convert Windows path separators to Unix style for consistency
        path1 = path1.replace("\\", "/")
        path2 = path2.replace("\\", "/")

        # Split paths into components
        parts1 = path1.split("/")
        parts2 = path2.split("/")

        # Compare path components
        matches = sum(1 for a, b in zip(parts1, parts2) if a == b)
        total = max(len(parts1), len(parts2))

        return matches / total if total > 0 else 0.0