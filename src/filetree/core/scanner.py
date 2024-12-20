import os
import hashlib
from typing import Dict, List, Tuple, Set
from pathlib import Path

class FileScanner:
    """Core file scanning functionality."""
    
    def __init__(self, directory: str):
        self.directory = Path(directory)
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
        Scan directory recursively and identify duplicates.
        Returns a dictionary mapping file hashes to lists of file paths.
        """
        for filepath in self.directory.rglob('*'):
            if filepath.is_file():
                file_hash = self.compute_file_hash(filepath)
                if file_hash:  # Only process if hash computation succeeded
                    self.file_hashes.setdefault(file_hash, []).append(filepath)
                    self.scanned_files.add(filepath)
        
        return self.file_hashes

    def get_duplicates(self) -> Dict[str, List[Path]]:
        """Return only the files that have duplicates."""
        return {
            file_hash: paths 
            for file_hash, paths in self.file_hashes.items() 
            if len(paths) > 1
        } 