import logging
from pathlib import Path
from typing import Dict, List
from ..utils.config import FileTreeConfig
from ..utils.parallel import ParallelProcessor

logger = logging.getLogger(__name__)

class FileScanner:
    """Scan directory structure and find duplicate files."""

    def __init__(self, num_workers=None):
        """Initialize scanner with optional worker count."""
        self.processor = ParallelProcessor(num_workers)
        logger.debug(f"Initialized FileScanner with {self.processor.num_workers} workers")

    def find_duplicates(self, directory: Path) -> Dict[str, List[Path]]:
        """Find duplicate files in the given directory."""
        logger.info(f"Scanning directory: {directory}")
        try:
            duplicates = self.processor.find_duplicates(directory)
            num_groups = len(duplicates)
            total_files = sum(len(files) for files in duplicates.values())
            logger.info(f"Found {num_groups} duplicate groups with {total_files} total files")
            return duplicates
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
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