"""File operations utilities"""
import os
from typing import Optional
from .logger import Logger

class FileOps:
    def __init__(self, logger: Logger):
        self.logger = logger

    def read_file(self, path: str) -> Optional[str]:
        """Read file contents safely"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            return None

    def write_file(self, path: str, content: str) -> bool:
        """Write content to file safely"""
        try:
            # Ensure path is not empty
            if not path:
                raise ValueError("Output path cannot be empty")
                
            # Convert to absolute path
            abs_path = os.path.abspath(path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Write the file
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {path}: {e}")
            return False