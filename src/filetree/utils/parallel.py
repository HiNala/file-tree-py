"""Parallel processing utilities for file tree operations."""
import os
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Callable, Any, Iterator, Tuple
from .env import env_config
from collections import defaultdict

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file in chunks."""
    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return ""

    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        hash_value = sha256_hash.hexdigest()
        logger.debug(f"Hash computed for {file_path}: {hash_value[:8]}...")
        return hash_value
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

class ParallelProcessor:
    """Process files in parallel using a thread pool."""

    def __init__(self, num_workers: int = None):
        """Initialize processor with number of worker threads."""
        self.num_workers = num_workers or (4)  # Default to 4 workers
        logger.debug(f"Initialized ParallelProcessor with {self.num_workers} workers")

    def process_files(self, files: List[Path], process_func: Callable[[Path], Any]) -> Iterator[Any]:
        """Process files in parallel using the provided function."""
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            yield from executor.map(process_func, files)

    def find_duplicates(self, directory: Path) -> Dict[str, List[Path]]:
        """Find duplicate files in directory."""
        files = list(self.scan_directory(directory))
        logger.debug(f"Looking for duplicates in {len(files)} files")

        # Group files by hash
        hash_map: Dict[str, List[Path]] = {}
        for file_path in files:
            file_hash = compute_file_hash(file_path)
            if file_hash:
                if file_hash not in hash_map:
                    hash_map[file_hash] = []
                hash_map[file_hash].append(file_path)

        # Filter out unique files
        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        logger.debug(f"Found {len(duplicates)} groups of duplicates")
        return duplicates

    def scan_directory(self, directory: Path) -> List[Path]:
        """Scan directory for files."""
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []

        try:
            files = []
            for item in directory.rglob("*"):
                if item.is_file():
                    files.append(item)
            return files
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return []