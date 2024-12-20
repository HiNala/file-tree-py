# File Tree Analysis Tool

A command-line tool for analyzing directory structures, detecting duplicates, and providing organizational insights.

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment configuration:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

## Environment Configuration

The tool uses environment variables for configuration. Create a `.env` file based on `.env.example`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO

# File Tree Configuration
MAX_DEPTH=10
EXCLUDE_PATTERNS=node_modules,__pycache__,.git
INCLUDE_HIDDEN=False

# Visualization Settings
OUTPUT_FORMAT=tree  # Options: tree, json, yaml
COLOR_OUTPUT=True
```

## Usage

### Basic Usage
```bash
python main.py /path/to/directory
```

### Interactive Mode
```bash
python main.py -i /path/to/directory
```

### Custom Worker Count
```bash
python main.py -w 4 /path/to/directory
```

This will scan the directory and show any duplicate files found. Use the `-i` flag to enter interactive mode for managing duplicates and directories.

## Features

Current features:
- Recursive directory scanning with parallel processing
- Duplicate file detection using SHA256 hashing
- Rich console output with colored formatting
- Environment-based configuration
- Customizable visualization options
- Interactive file management:
  - Resolve duplicates
  - Merge directories
  - Rename files/directories

## Configuration Options

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| OPENAI_API_KEY | Your OpenAI API key for AI features | Required |
| DEBUG | Enable debug mode | False |
| LOG_LEVEL | Logging level (INFO, DEBUG, etc.) | INFO |
| MAX_DEPTH | Maximum directory depth to scan | 10 |
| EXCLUDE_PATTERNS | Comma-separated patterns to exclude | node_modules,__pycache__,.git |
| INCLUDE_HIDDEN | Include hidden files and directories | False |
| OUTPUT_FORMAT | Output format (tree, json, yaml) | tree |
| COLOR_OUTPUT | Enable colored output | True |

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
The project follows PEP 8 guidelines. Before committing, ensure your code is properly formatted.