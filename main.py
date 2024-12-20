#!/usr/bin/env python3
"""Main entry point for the file tree analyzer."""
import sys
from filetree.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 