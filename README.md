# PyBundler

A basic Python source code bundler that combines multiple Python files into a single executable file.

⚠️ **Important Note**: This is a basic implementation with limitations. It may not work with complex project structures or certain import patterns.

## Overview

PyBundler is a simple tool that helps you bundle multiple Python files into a single file. It's particularly useful for basic projects with straightforward import structures.

### Supported Project Structure Example

```
ProjectRoot/
    ├── models/
    │   ├── user.py
    │   └── product.py
    ├── services/
    │   ├── auth.py
    │   └── data.py
    ├── utils/
    │   └── helpers.py
    └── main.py
```

## Features

- ✨ Combines multiple Python files into a single file
- 📊 Provides basic dependency analysis
- 🔍 Handles simple import structures
- 📝 Generates bundle statistics
- 🎨 Maintains code readability with section headers

## Limitations

- Does not support complex circular dependencies
- May not handle all import patterns correctly
- Limited support for certain Python features
- Not recommended for production use with complex projects
- May not work with dynamic imports or complex package structures

## Installation

```bash
pip install pybundler
```

## Usage

Basic usage example:

```bash
python -m pybundler -p ./project_folder -f main.py -o bundled_output.py
```

### Arguments

- `-p, --path`: Path to the source folder containing your Python files
- `-f, --file`: Main Python file (entry point)
- `-o, --output`: Output file path for the bundled code
- `-v, --verbose`: Enable verbose logging (optional)

### Example

```bash
python -m pybundler -p ./MyProject/src/ -f main.py -o ./dist/bundle.py
```

## Output

The bundler will generate a single Python file that:
- Contains all the necessary code from your project
- Preserves imports from standard library and third-party packages
- Includes section headers for better code organization
- Provides statistics about the bundling process

## Development

This project is in early stages and contributions are welcome. Feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details.

## Disclaimer

This is a basic implementation intended for simple use cases. For production applications or complex projects, consider using more robust packaging solutions like PyInstaller or cx_Freeze.

---
Made with ❤️ by Steven
