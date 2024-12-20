"""Environment configuration module for the file tree application."""
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('filetree.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
logger.debug(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

class EnvironmentConfig:
    """Environment configuration handler."""
    
    @staticmethod
    def get_openai_api_key() -> str:
        """Get OpenAI API key from environment."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error('OPENAI_API_KEY environment variable is not set')
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        logger.debug('OpenAI API key loaded')
        return api_key

    @staticmethod
    def get_debug_mode() -> bool:
        """Get debug mode setting."""
        debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        logger.debug(f'Debug mode: {debug_mode}')
        return debug_mode

    @staticmethod
    def get_log_level() -> str:
        """Get logging level."""
        level = os.getenv('LOG_LEVEL', 'INFO')
        logger.debug(f'Log level: {level}')
        return level

    @staticmethod
    def get_max_depth() -> int:
        """Get maximum depth for file tree traversal."""
        depth = int(os.getenv('MAX_DEPTH', '10'))
        logger.debug(f'Max depth: {depth}')
        return depth

    @staticmethod
    def get_exclude_patterns() -> list[str]:
        """Get patterns to exclude from file tree."""
        patterns = os.getenv('EXCLUDE_PATTERNS', '')
        result = [p.strip() for p in patterns.split(',') if p.strip()]
        logger.debug(f'Exclude patterns: {result}')
        return result

    @staticmethod
    def get_include_hidden() -> bool:
        """Get whether to include hidden files."""
        include_hidden = os.getenv('INCLUDE_HIDDEN', 'False').lower() == 'true'
        logger.debug(f'Include hidden: {include_hidden}')
        return include_hidden

    @staticmethod
    def get_output_format() -> str:
        """Get output format for visualization."""
        format = os.getenv('OUTPUT_FORMAT', 'tree')
        logger.debug(f'Output format: {format}')
        return format

    @staticmethod
    def get_color_output() -> bool:
        """Get whether to use color in output."""
        color = os.getenv('COLOR_OUTPUT', 'True').lower() == 'true'
        logger.debug(f'Color output: {color}')
        return color

# Create a singleton instance
env_config = EnvironmentConfig() 