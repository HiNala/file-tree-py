"""File system scanner module."""
from pathlib import Path
from typing import List, Dict, Set
import os
from fnmatch import fnmatch

from ..utils.config import Config

class FileTreeScanner:
    """Scanner for analyzing directory structure."""

    def __init__(self, config: Config):
        """Initialize scanner with configuration."""
        self.config = config

    def scan_directory(self, directory: Path) -> List[Path]:
        """Scan directory and return list of files."""
        if not directory.exists():
            raise Exception(f"Error scanning directory {directory}: Directory does not exist")
            
        files = []
        try:
            for root, _, filenames in os.walk(directory):
                root_path = Path(root)
                
                # Skip ignored directories
                if any(fnmatch(root_path.name, pattern) for pattern in self.config.ignore_patterns):
                    continue
                
                # Skip hidden directories if configured
                if not self.config.include_hidden and root_path.name.startswith('.'):
                    continue
                
                for filename in filenames:
                    file_path = root_path / filename
                    
                    # Skip ignored files
                    if any(fnmatch(filename, pattern) for pattern in self.config.ignore_patterns):
                        continue
                    
                    # Skip hidden files if configured
                    if not self.config.include_hidden and filename.startswith('.'):
                        continue
                    
                    # Skip symlinks if configured
                    if not self.config.follow_symlinks and file_path.is_symlink():
                        continue
                        
                    try:
                        # Skip files that can't be accessed
                        if not os.access(file_path, os.R_OK):
                            continue
                            
                        files.append(file_path)
                    except (PermissionError, OSError):
                        continue
                        
        except (PermissionError, OSError) as e:
            raise Exception(f"Error scanning directory {directory}: {str(e)}")
            
        return files

    def get_file_stats(self, files: List[Path]) -> Dict[str, int]:
        """Get statistics about files."""
        stats = {
            'total_files': len(files),
            'total_size': 0,
            'min_size': float('inf'),
            'max_size': 0
        }
        
        for file in files:
            try:
                size = os.path.getsize(file)
                stats['total_size'] += size
                stats['min_size'] = min(stats['min_size'], size)
                stats['max_size'] = max(stats['max_size'], size)
            except (OSError, PermissionError):
                continue
                
        if not files:
            stats['min_size'] = 0
            
        return stats

    def get_file_types(self, files: List[Path]) -> Dict[str, int]:
        """Get distribution of file types."""
        extensions = {}
        
        for file in files:
            ext = file.suffix.lower() or '(no extension)'
            extensions[ext] = extensions.get(ext, 0) + 1
            
        return dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True))

    def get_directory_structure(self, directory: Path) -> Dict[str, Set[Path]]:
        """Get structure of directories and their files."""
        structure = {}
        
        for file in self.scan_directory(directory):
            dir_path = str(file.parent.relative_to(directory))
            if dir_path not in structure:
                structure[dir_path] = set()
            structure[dir_path].add(file)
            
        return structure