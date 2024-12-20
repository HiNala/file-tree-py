"""Parallel processing utilities for file tree operations."""
import os
import psutil
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
    """Handles parallel processing of files with dynamic worker allocation."""

    def __init__(self, max_workers: int = None, min_workers: int = 2):
        """Initialize the processor with dynamic worker allocation.
        
        Args:
            max_workers: Maximum number of worker threads to use
            min_workers: Minimum number of worker threads to maintain
        """
        self.max_workers = max_workers or min(32, os.cpu_count() * 2)
        self.min_workers = min_workers
        self._last_worker_count = None
        logger.debug("Initialized ParallelProcessor with max %d workers", self.max_workers)

    def _get_optimal_workers(self) -> int:
        """Calculate the optimal number of workers based on system load.
        
        Returns:
            int: Optimal number of worker threads
        """
        try:
            # Get CPU metrics
            cpu_count = os.cpu_count() or 4
            cpu_load = psutil.cpu_percent() / 100
            
            # Get memory metrics
            memory = psutil.virtual_memory()
            memory_load = memory.percent / 100
            
            # Calculate optimal workers based on CPU and memory load
            cpu_factor = 1 - cpu_load  # Reduce workers when CPU is busy
            memory_factor = 1 - memory_load  # Reduce workers when memory is low
            
            # Combine factors (weighted average)
            system_factor = (cpu_factor * 0.7) + (memory_factor * 0.3)
            
            # Calculate optimal workers
            optimal_workers = max(
                self.min_workers,
                min(
                    self.max_workers,
                    int(cpu_count * system_factor * 2)  # Up to 2 threads per CPU core
                )
            )
            
            logger.debug(
                "System load - CPU: %.1f%%, Memory: %.1f%%, Workers: %d",
                cpu_load * 100,
                memory_load * 100,
                optimal_workers
            )
            
            return optimal_workers
            
        except Exception as e:
            logger.warning("Error calculating optimal workers: %s", e)
            return self.max_workers  # Fall back to max workers on error

    def _get_current_workers(self) -> int:
        """Get the current optimal number of workers, with hysteresis to prevent rapid changes.
        
        Returns:
            int: Number of worker threads to use
        """
        optimal = self._get_optimal_workers()
        
        # Apply hysteresis: only change if difference is significant
        if self._last_worker_count is None:
            self._last_worker_count = optimal
        elif abs(optimal - self._last_worker_count) >= 2:  # Change if difference >= 2
            self._last_worker_count = optimal
            
        return self._last_worker_count

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
            # Get optimal worker count for this batch
            num_workers = self._get_current_workers()
            logger.debug("Processing %d files with %d workers", len(files), num_workers)
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
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