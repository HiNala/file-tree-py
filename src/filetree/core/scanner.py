import os
import logging
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
from ..utils.parallel import ParallelProcessor
from ..utils.config import FileTreeConfig

logger = logging.getLogger(__name__)

class FileScanner:
    """Scanner for finding duplicate files in a directory."""

    def __init__(self, config: FileTreeConfig = None, num_workers: int = None):
        """Initialize the scanner with configuration."""
        logger.debug("Initializing FileScanner with %s workers", num_workers or "default")
        self.config = config or FileTreeConfig()
        self.processor = ParallelProcessor(num_workers=num_workers)
        logger.debug("Scanner configuration: %s", self.config)

    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on configuration."""
        if not self.config.include_hidden and path.name.startswith('.'):
            logger.debug("Excluding hidden path: %s", path)
            return True

        for pattern in self.config.exclude_patterns:
            if pattern in str(path):
                logger.debug("Excluding path matching pattern '%s': %s", pattern, path)
                return True

        return False

    def _scan_directory(self, directory: Path, max_depth: int = None) -> Set[Path]:
        """Recursively scan a directory for files."""
        logger.debug("Scanning directory: %s (max_depth=%s)", directory, max_depth)
        files = set()
        current_depth = 0

        try:
            for root, dirs, filenames in os.walk(directory):
                current_depth = len(Path(root).relative_to(directory).parts)
                
                if max_depth is not None and current_depth > max_depth:
                    logger.debug("Reached max depth at: %s", root)
                    continue

                # Process files in current directory
                for filename in filenames:
                    file_path = Path(root) / filename
                    if not self._should_exclude(file_path):
                        logger.debug("Found file: %s", file_path)
                        files.add(file_path)

                # Filter directories based on exclusion patterns
                dirs[:] = [d for d in dirs if not self._should_exclude(Path(root) / d)]

        except Exception as e:
            logger.error("Error scanning directory %s: %s", directory, e, exc_info=True)
            raise

        logger.debug("Found %d files in directory %s", len(files), directory)
        return files

    def find_duplicates(self, directory: Path) -> Dict[str, List[Path]]:
        """Find duplicate files in the given directory."""
        logger.debug("Starting duplicate file search in: %s", directory)
        
        try:
            # Scan directory for files
            files = self._scan_directory(directory, self.config.max_depth)
            logger.debug("Found %d total files to process", len(files))

            # Process files in parallel to find duplicates
            duplicates = self.processor.find_duplicates(files)
            logger.debug("Found %d groups of duplicate files", len(duplicates))

            return duplicates

        except Exception as e:
            logger.error("Error finding duplicates: %s", e, exc_info=True)
            raise

    def scan_directory(self, directory: Path) -> List[Path]:
        """Scan directory and return list of files."""
        logger.info(f"Scanning directory: {directory}")
        try:
            files = self.processor.scan_directory(directory)
            logger.info(f"Found {len(files)} files")
            return files
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            raise