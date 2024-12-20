"""Report generation module."""
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import track

from ..core.duplicates import DuplicateFinder
from ..core.scanner import FileTreeScanner
from .config import Config

class ReportGenerator:
    """Generator for file tree analysis reports."""

    def __init__(self):
        """Initialize report generator."""
        self.console = Console()

    def _format_size(self, size: int) -> str:
        """Format size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _generate_ascii_bar(self, value: int, max_value: int, width: int = 20) -> str:
        """Generate ASCII progress bar."""
        filled = int(width * (value / max_value)) if max_value > 0 else 0
        return f"[{'=' * filled}{' ' * (width - filled)}]"

    def _generate_summary(self, files: List[Path], duplicates: Dict[str, List[Path]]) -> str:
        """Generate summary section of the report."""
        total_files = len(files)
        total_size = sum(p.stat().st_size for p in files if p.exists())
        duplicate_stats = DuplicateFinder().get_duplicate_stats(duplicates)

        summary = [
            "# 📊 File Tree Analysis Report",
            "\n## 📈 Summary",
            f"\n- Total Files: {total_files:,}",
            f"- Total Size: {self._format_size(total_size)}",
            f"- Duplicate Groups: {duplicate_stats['total_groups']:,}",
            f"- Total Duplicates: {duplicate_stats['total_duplicates']:,}",
            f"- Wasted Space: {self._format_size(duplicate_stats['wasted_space'])}"
        ]
        return "\n".join(summary)

    def _generate_file_type_distribution(self, files: List[Path]) -> str:
        """Generate file type distribution section."""
        scanner = FileTreeScanner(Config())
        type_dist = scanner.get_file_types(files)
        
        if not type_dist:
            return "\n## 📁 File Type Distribution\n\nNo files found."
            
        total_files = sum(type_dist.values())
        max_count = max(type_dist.values())
        
        distribution = ["\n## 📁 File Type Distribution\n"]
        for ext, count in type_dist.items():
            percentage = (count / total_files) * 100
            bar = self._generate_ascii_bar(count, max_count)
            distribution.append(
                f"- {ext:<15} {count:>4} files {bar} {percentage:>5.1f}%"
            )
            
        return "\n".join(distribution)

    def _generate_duplicate_findings(self, duplicates: Dict[str, List[Path]]) -> str:
        """Generate duplicate files section."""
        if not duplicates:
            return "\n## 🔍 Duplicate Files\n\nNo duplicate files found."
            
        findings = ["\n## 🔍 Duplicate Files\n"]
        for hash_value, files in duplicates.items():
            if not files:
                continue
                
            try:
                size = files[0].stat().st_size
                findings.append(f"\n### Group ({self._format_size(size)} each)")
                for file in files:
                    findings.append(f"- {file}")
            except OSError:
                continue
                
        return "\n".join(findings)

    def _generate_recommendations(self, duplicates: Dict[str, List[Path]]) -> str:
        """Generate recommendations section."""
        if not duplicates:
            return "\n## 💡 Recommendations\n\nNo issues found. Your file structure looks good!"
            
        recommendations = [
            "\n## 💡 Recommendations",
            "\nHere are some suggestions to optimize your file structure:",
            "\n1. **Review Duplicate Files**",
            "   - Use interactive mode (`--interactive`) to manage duplicates",
            "   - Consider using symbolic links for frequently accessed duplicates",
            "   - Backup important files before deletion",
            "\n2. **Storage Optimization**",
            "   - Remove unnecessary duplicate files",
            "   - Consider archiving rarely accessed files",
            "   - Use version control instead of keeping multiple copies",
            "\n3. **Best Practices**",
            "   - Implement a consistent file naming convention",
            "   - Organize files into logical directories",
            "   - Use version control for tracking changes",
            "   - Regular cleanup of temporary and cache files"
        ]
        return "\n".join(recommendations)

    def generate_report(
        self,
        directory: Path,
        files: List[Path],
        duplicates: Dict[str, List[Path]],
        config: Config,
        show_tree: bool = True
    ) -> str:
        """Generate complete analysis report."""
        sections = [
            self._generate_summary(files, duplicates),
            self._generate_file_type_distribution(files),
            self._generate_duplicate_findings(duplicates),
            self._generate_recommendations(duplicates),
            "\n## ⚙️ Configuration Used",
            f"\n- Ignore Patterns: {', '.join(config.ignore_patterns)}",
            f"- Follow Symlinks: {config.follow_symlinks}",
            f"- Include Hidden: {config.include_hidden}",
            f"- Min File Size: {self._format_size(config.min_file_size)}",
            f"- Max Depth: {'Unlimited' if config.max_depth is None else config.max_depth}"
        ]
        
        return "\n".join(sections) 