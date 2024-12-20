"""Parallel processing utilities for file tree operations."""
import os
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Callable, Any, Iterator, Tuple, Set, Union
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
    """Handles parallel processing of files."""

    def __init__(self, num_workers: int = None):
        """Initialize the processor with the specified number of workers."""
        self.num_workers = num_workers or min(32, os.cpu_count() * 2)
        logger.debug("Initialized ParallelProcessor with %d workers", self.num_workers)

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()
            logger.debug("Hash computed for %s: %s...", file_path, file_hash[:8])
            return file_hash
        except Exception as e:
            logger.error("Error computing hash for %s: %s", file_path, e)
            return None

    def scan_directory(self, directory: Path) -> Set[Path]:
        """Scan a directory for files."""
        try:
            files = set()
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if file_path.is_file():
                        files.add(file_path)
            return files
        except Exception as e:
            logger.error("Error scanning directory %s: %s", directory, e)
            return set()

    def process_files(self, files: Set[Path]) -> Dict[str, List[Path]]:
        """Process files in parallel to compute their hashes."""
        hash_map = {}
        try:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                # Process files in parallel and collect results
                future_to_file = {
                    executor.submit(self.compute_file_hash, file_path): file_path
                    for file_path in files
                }

                # Collect results as they complete
                for future in future_to_file:
                    file_path = future_to_file[future]
                    try:
                        file_hash = future.result()
                        if file_hash:
                            if file_hash not in hash_map:
                                hash_map[file_hash] = []
                            hash_map[file_hash].append(file_path)
                    except Exception as e:
                        logger.error("Error processing %s: %s", file_path, e)

        except Exception as e:
            logger.error("Error in parallel processing: %s", e)

        return hash_map

    def find_duplicates(self, path_or_files: Union[Path, Set[Path]]) -> Dict[str, List[Path]]:
        """Find duplicate files based on their content hash.

        Args:
            path_or_files: Either a directory path to scan or a set of files to process
        """
        if isinstance(path_or_files, Path):
            files = self.scan_directory(path_or_files)
        else:
            files = path_or_files

        logger.debug("Finding duplicates among %d files", len(files))

        # Process files to get hash map
        hash_map = self.process_files(files)

        # Filter out unique files
        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        return duplicates

    def scan_and_report(self, directory: Path) -> Dict[str, List[Path]]:
        """Scan directory and report duplicate files."""
        try:
            if not directory.exists():
                logger.error("Directory not found: %s", directory)
                return {}

            if not directory.is_dir():
                logger.error("Path is not a directory: %s", directory)
                return {}

            return self.find_duplicates(directory)

        except Exception as e:
            logger.error("Error scanning directory: %s", e)
            return {}