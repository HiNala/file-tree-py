import os
import hashlib
from typing import Dict, List, Tuple, Set
from pathlib import Path
from ..utils.parallel import ParallelProcessor

class FileScanner:
    """Core file scanning functionality with parallel processing."""
    
    def __init__(self, directory: str, max_workers: int = None):
        """Initialize the file scanner.
        
        Args:
            directory: Root directory to scan.
            max_workers: Maximum number of worker threads for parallel processing.
        """
        self.directory = Path(directory)
        self.processor = ParallelProcessor(max_workers=max_workers)
        self.file_hashes: Dict[str, List[Path]] = {}
        self.scanned_files: Set[Path] = set()
    
    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (IOError, OSError) as e:
            print(f"Warning: Could not read file {filepath}: {e}")
            return ""

    def scan(self) -> Dict[str, List[Path]]:
        """
        Scan directory recursively and identify duplicates using parallel processing.
        Returns a dictionary mapping file hashes to lists of file paths.
        """
        # Use parallel processor to scan directory
        files = self.processor.scan_directory(self.directory)
        self.scanned_files.update(files)
        
        # Find duplicates using parallel processing
        self.file_hashes = self.processor.find_duplicates(files)
        
        return self.file_hashes

    def get_duplicates(self) -> Dict[str, List[Path]]:
        """Return only the files that have duplicates."""
        return {
            file_hash: paths 
            for file_hash, paths in self.file_hashes.items() 
            if len(paths) > 1
        } 