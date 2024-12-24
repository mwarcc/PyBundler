"""File handling utilities"""
import os
from typing import List, Optional
from .logger import Logger

class FileUtils:
    def __init__(self, logger: Logger):
        self.logger = logger

    def read_file(self, path: str) -> Optional[str]:
        """Read file contents safely"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            return None

    def write_file(self, path: str, content: str) -> bool:
        """Write content to file safely"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {path}: {e}")
            return False

    def find_python_files(self, directory: str) -> List[str]:
        """Find all Python files in directory"""
        python_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files