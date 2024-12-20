"""Parallel processing utilities for file tree operations."""
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Callable, Any, Iterator
from .env import env_config

def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file in chunks to handle large files efficiently."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        print(f"Warning: Could not hash file {file_path}: {e}")
        return ""

class ParallelProcessor:
    """Handles parallel processing of file tree operations."""
    
    def __init__(self, max_workers: int = None):
        """Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of worker threads. Defaults to number of CPUs * 2.
        """
        self.max_workers = max_workers or (os.cpu_count() * 2)
    
    def process_files(self, 
                     files: List[Path], 
                     processor_func: Callable[[Path], Any],
                     chunk_size: int = 100) -> Iterator[Any]:
        """Process files in parallel using a thread pool.
        
        Args:
            files: List of file paths to process.
            processor_func: Function to apply to each file.
            chunk_size: Number of files to process in each chunk.
            
        Yields:
            Results from the processor function for each file.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Process files in chunks to avoid memory issues with large directories
            for i in range(0, len(files), chunk_size):
                chunk = files[i:i + chunk_size]
                futures = {
                    executor.submit(processor_func, file_path): file_path 
                    for file_path in chunk
                }
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        yield result
                    except Exception as e:
                        file_path = futures[future]
                        print(f"Error processing {file_path}: {e}")
    
    def find_duplicates(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Find duplicate files using parallel hash computation.
        
        Args:
            files: List of file paths to check for duplicates.
            
        Returns:
            Dictionary mapping file hashes to lists of duplicate file paths.
        """
        hash_map: Dict[str, List[Path]] = {}
        
        for file_hash in self.process_files(files, compute_file_hash):
            if file_hash and file_hash in hash_map:
                hash_map[file_hash].append(file_hash)
            elif file_hash:
                hash_map[file_hash] = [file_hash]
        
        # Filter out unique files
        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    
    def scan_directory(self, root_path: Path) -> List[Path]:
        """Scan a directory for files in parallel.
        
        Args:
            root_path: Root directory to scan.
            
        Returns:
            List of file paths found.
        """
        max_depth = env_config.get_max_depth()
        exclude_patterns = env_config.get_exclude_patterns()
        include_hidden = env_config.get_include_hidden()
        
        def should_process(path: Path) -> bool:
            """Check if a path should be processed based on configuration."""
            if not include_hidden and path.name.startswith('.'):
                return False
            return not any(pattern in str(path) for pattern in exclude_patterns)
        
        def scan_subdir(path: Path, current_depth: int = 0) -> List[Path]:
            """Recursively scan a subdirectory."""
            if current_depth > max_depth:
                return []
            
            try:
                files = []
                for item in path.iterdir():
                    if not should_process(item):
                        continue
                    if item.is_file():
                        files.append(item)
                    elif item.is_dir():
                        files.extend(scan_subdir(item, current_depth + 1))
                return files
            except (PermissionError, OSError) as e:
                print(f"Error scanning {path}: {e}")
                return []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            subdirs = [d for d in root_path.iterdir() if d.is_dir() and should_process(d)]
            futures = {
                executor.submit(scan_subdir, subdir): subdir 
                for subdir in subdirs
            }
            
            all_files = []
            for future in as_completed(futures):
                try:
                    files = future.result()
                    all_files.extend(files)
                except Exception as e:
                    subdir = futures[future]
                    print(f"Error scanning directory {subdir}: {e}")
            
            # Add files in root directory
            all_files.extend([
                f for f in root_path.iterdir() 
                if f.is_file() and should_process(f)
            ])
            
            return all_files 