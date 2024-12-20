import os
import logging
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
from ..utils.parallel import ParallelProcessor
from ..utils.config import FileTreeConfig
import fnmatch

logger = logging.getLogger(__name__)

class FileScanner:
    """Scanner for finding duplicate files in a directory."""

    def __init__(self, config: FileTreeConfig = None, num_workers: int = None):
        """Initialize the scanner with configuration."""
        logger.debug("Initializing FileScanner with %s workers", num_workers or "default")
        self.config = config or FileTreeConfig()
        self.processor = ParallelProcessor(num_workers=num_workers)
        self.reset_statistics()
        logger.debug("Scanner configuration: %s", self.config)

    def reset_statistics(self):
        """Reset all statistics counters."""
        self.file_type_stats = {}
        self.large_files = []
        self.max_depth = 0
        self.deep_paths = []
        self.total_size = 0
        self.hidden_files = 0

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on configuration."""
        try:
            # Check if path is hidden
            if path.name.startswith('.') and not self.config.include_hidden:
                logger.debug("Excluding hidden path: %s", path)
                self.hidden_files += 1
                return True

            # Check if path matches ignore patterns
            for pattern in self.config.ignore_patterns:
                if fnmatch.fnmatch(path.name, pattern):
                    logger.debug("Excluding path matching pattern %r: %s", pattern, path)
                    return True

            return False
        except Exception as e:
            logger.error("Error checking path exclusion: %s", e)
            return False

    def _scan_directory(self, directory: Path, max_depth: int = None, current_depth: int = 0) -> Set[Path]:
        """Scan a directory for files, respecting max depth and exclusion patterns."""
        try:
            if max_depth is not None and current_depth > max_depth:
                return set()

            files = set()
            for file_path in directory.iterdir():
                if not self._should_exclude(file_path):
                    if file_path.is_file():
                        files.add(file_path)
                        # Update file type statistics
                        ext = file_path.suffix.lower() or "no_extension"
                        self.file_type_stats[ext] = self.file_type_stats.get(ext, 0) + 1
                        
                        # Track file size statistics
                        try:
                            size = file_path.stat().st_size
                            self.total_size += size
                            if size > 100 * 1024 * 1024:  # 100MB
                                self.large_files.append({
                                    "path": str(file_path),
                                    "size": size
                                })
                        except OSError:
                            logger.warning(f"Could not get size of file: {file_path}")
                            
                    elif file_path.is_dir():
                        # Update depth statistics
                        path_depth = len(file_path.parts)
                        self.max_depth = max(self.max_depth, path_depth)
                        if path_depth > 5:  # Track paths deeper than 5 levels
                            self.deep_paths.append(str(file_path))
                            
                        # Recursively scan subdirectories
                        files.update(self._scan_directory(file_path, max_depth, current_depth + 1))

            return files
        except Exception as e:
            logger.error("Error scanning directory %s: %s", directory, e)
            return set()

    def find_duplicates(self, directory: Path) -> Dict[str, List[Path]]:
        """Find duplicate files in the given directory."""
        try:
            # Reset statistics
            self.reset_statistics()

            logger.debug("Starting duplicate file search in: %s", directory)
            
            # If directory is a Path, scan it; otherwise assume it's a set of files
            if isinstance(directory, Path):
                files = self._scan_directory(directory, self.config.max_depth)
            else:
                files = directory  # Already a set of files
                
            logger.debug("Found %d files in directory %s", len(files), directory)

            if not files:
                return {}

            try:
                # Find duplicates using parallel processing
                duplicates = self.processor.find_duplicates(files)
                logger.debug("Found %d groups of duplicate files", len(duplicates))
                return duplicates
            except Exception as e:
                logger.error("Error in parallel processing: %s", e)
                raise  # Re-raise to maintain error handling behavior

        except Exception as e:
            logger.error("Error finding duplicates: %s", e)
            raise

    def scan_directory(self, directory: Path) -> Set[Path]:
        """Scan directory and return set of files."""
        logger.info(f"Scanning directory: {directory}")
        try:
            # Reset statistics
            self.reset_statistics()

            files = self._scan_directory(directory, self.config.max_depth)
            logger.info(f"Found {len(files)} files")
            return files
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            raise