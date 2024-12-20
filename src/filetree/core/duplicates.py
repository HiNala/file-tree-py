"""Module for finding duplicate files."""
from pathlib import Path
from typing import Dict, List, Set
import hashlib
import os

class DuplicateFinder:
    """Class for finding duplicate files."""

    def __init__(self, min_size: int = 1):
        """Initialize finder with minimum file size."""
        self.min_size = min_size

    def _get_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (OSError, PermissionError) as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")

    def _get_file_size(self, file_path: Path) -> int:
        """Get size of a file."""
        try:
            return os.path.getsize(file_path)
        except (OSError, PermissionError) as e:
            raise Exception(f"Error getting size of file {file_path}: {str(e)}")

    def find_duplicates(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Find duplicate files in the given list."""
        # Group files by size first
        size_groups: Dict[int, List[Path]] = {}
        for file in files:
            try:
                size = self._get_file_size(file)
                if size >= self.min_size:
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(file)
            except Exception:
                continue

        # For each size group, calculate hashes
        duplicates: Dict[str, List[Path]] = {}
        for size_group in size_groups.values():
            if len(size_group) < 2:
                continue

            # Group files by hash
            hash_groups: Dict[str, List[Path]] = {}
            for file in size_group:
                try:
                    file_hash = self._get_file_hash(file)
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file)
                except Exception:
                    continue

            # Add groups with duplicates to results
            for hash_value, files in hash_groups.items():
                if len(files) > 1:
                    duplicates[hash_value] = files

        return duplicates

    def get_duplicate_stats(self, duplicates: Dict[str, List[Path]]) -> Dict[str, int]:
        """Get statistics about duplicate files."""
        stats = {
            'total_groups': len(duplicates),
            'total_duplicates': 0,
            'wasted_space': 0
        }

        for files in duplicates.values():
            if not files:
                continue
            try:
                file_size = self._get_file_size(files[0])
                num_duplicates = len(files) - 1
                stats['total_duplicates'] += num_duplicates
                stats['wasted_space'] += file_size * num_duplicates
            except Exception:
                continue

        return stats 