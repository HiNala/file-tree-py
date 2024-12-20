"""Module for configuring logging with colors and better formatting."""
import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console
from datetime import datetime

# Create console for rich output
console = Console()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'

    def format(self, record):
        """Format the log record with colors."""
        # Add color if the level is in our color map
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            if record.msg:
                record.msg = f"{self.COLORS[record.levelname.strip(self.RESET)]}{record.msg}{self.RESET}"
        return super().format(record)

def setup_logging(verbose: bool = False, log_file: str = None):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"filetree_{timestamp}.log"
    
    log_path = logs_dir / log_file
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with rich formatting
    console_handler = RichHandler(
        console=console,
        show_path=False,
        enable_link_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        log_time_format="[%X]"
    )
    console_handler.setLevel(level)
    console_format = "%(message)s"
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)

    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    file_format = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    root_logger.addHandler(file_handler)

    # Log initial setup information
    logging.debug("Logging initialized (Level: %s)", "DEBUG" if verbose else "INFO")
    logging.debug("Log file: %s", log_path.absolute()) 