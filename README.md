# File Tree Analysis Tool

A command-line tool for analyzing directory structures, detecting duplicates, and providing organizational insights.

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

Basic usage:
```bash
python -m filetree.cli /path/to/directory
```

This will scan the directory and show any duplicate files found.

## Features

Current features:
- Recursive directory scanning
- Duplicate file detection using SHA256 hashing
- Rich console output with colored formatting

Coming soon:
- Directory structure visualization
- Duplicate route detection
- Context-specific suggestions
- Configuration file support
- Export to JSON/YAML 