"""Environment configuration module for the file tree application."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class EnvironmentConfig:
    """Environment configuration handler."""
    
    @staticmethod
    def get_openai_api_key() -> str:
        """Get OpenAI API key from environment."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        return api_key

    @staticmethod
    def get_debug_mode() -> bool:
        """Get debug mode setting."""
        return os.getenv('DEBUG', 'False').lower() == 'true'

    @staticmethod
    def get_log_level() -> str:
        """Get logging level."""
        return os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def get_max_depth() -> int:
        """Get maximum depth for file tree traversal."""
        return int(os.getenv('MAX_DEPTH', '10'))

    @staticmethod
    def get_exclude_patterns() -> list[str]:
        """Get patterns to exclude from file tree."""
        patterns = os.getenv('EXCLUDE_PATTERNS', '')
        return [p.strip() for p in patterns.split(',') if p.strip()]

    @staticmethod
    def get_include_hidden() -> bool:
        """Get whether to include hidden files."""
        return os.getenv('INCLUDE_HIDDEN', 'False').lower() == 'true'

    @staticmethod
    def get_output_format() -> str:
        """Get output format for visualization."""
        return os.getenv('OUTPUT_FORMAT', 'tree')

    @staticmethod
    def get_color_output() -> bool:
        """Get whether to use color in output."""
        return os.getenv('COLOR_OUTPUT', 'True').lower() == 'true'

# Create a singleton instance
env_config = EnvironmentConfig() 