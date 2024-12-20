#!/usr/bin/env python3
"""Test runner for the file tree analyzer."""
import os
import sys
import pytest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test.log')
    ]
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests with detailed output."""
    logger.info("Starting test run")
    
    # Get the test directory
    test_dir = Path(__file__).parent / "tests"
    logger.debug(f"Test directory: {test_dir}")
    
    # List all test files
    test_files = sorted(test_dir.glob("test_*.py"))
    logger.info(f"Found {len(test_files)} test files")
    for file in test_files:
        logger.debug(f"Test file: {file.name}")
    
    # Run pytest with verbose output and coverage
    args = [
        "-v",  # verbose output
        "--capture=no",  # show print statements
        "--log-cli-level=DEBUG",  # show debug logs
        "--cov=src/filetree",  # measure coverage
        "--cov-report=term-missing",  # show lines missing coverage
        str(test_dir)  # test directory
    ]
    
    logger.info("Running tests...")
    result = pytest.main(args)
    
    if result == 0:
        logger.info("All tests passed!")
    else:
        logger.error(f"Tests failed with exit code: {result}")
    
    return result

if __name__ == "__main__":
    sys.exit(run_tests()) 