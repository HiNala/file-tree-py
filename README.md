# File Tree Analyzer

A Python tool for analyzing directory structures, finding duplicate files, and managing file organization.

## Features

- Find duplicate files based on content hash
- Interactive mode for managing duplicates
- Tree view visualization of directory structure
- Export results to file
- Configurable worker threads for parallel processing

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/file-tree-py.git
   cd file-tree-py
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

## Usage

There are two ways to use the File Tree Analyzer:

### 1. Interactive Mode (Recommended for New Users)

Simply run the program without arguments:
```bash
python main.py
```

The program will prompt you to enter a directory path. You can:
1. Type '.' for the current directory
2. Paste a full directory path
3. Press Ctrl+C to exit

### 2. Command Line Arguments

For more advanced usage, you can provide arguments directly:

```bash
python main.py [directory] [options]
```

Options:
- `-w, --workers N`: Set number of worker threads
- `-i, --interactive`: Enable interactive mode for managing duplicates
- `--no-tree`: Disable tree view visualization
- `--export FILE`: Export results to specified file
- `--config FILE`: Use custom configuration file
- `-v, --verbose`: Enable verbose logging
- `-h, --help`: Show help message

Examples:
```bash
# Analyze current directory
python main.py .

# Analyze specific directory with verbose logging
python main.py /path/to/directory -v

# Enable interactive mode
python main.py . -i

# Export results to file
python main.py . --export report.txt
```

## Configuration

You can customize the behavior by creating a JSON configuration file:

```json
{
  "similarity_threshold": 0.8,
  "exclude_patterns": ["__pycache__", "*.pyc"],
  "max_depth": 5,
  "include_hidden": false,
  "num_workers": 4
}
```

Use the config file with:
```bash
python main.py . --config myconfig.json
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.