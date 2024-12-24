"""Logging utilities for PyBundler"""
import time
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class Logger:
    """Advanced logging with color support and progress tracking"""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.start_time = time.time()
        self.last_progress = 0

    def _get_timestamp(self) -> str:
        return f"{Colors.BOLD}[{datetime.now().strftime('%H:%M:%S')}]{Colors.RESET}"

    def info(self, message: str):
        print(f"{self._get_timestamp()} {Colors.INFO}INFO{Colors.RESET} {message}")

    def success(self, message: str):
        print(f"{self._get_timestamp()} {Colors.SUCCESS}SUCCESS{Colors.RESET} {message}")

    def warning(self, message: str):
        print(f"{self._get_timestamp()} {Colors.WARNING}WARNING{Colors.RESET} {message}")

    def error(self, message: str):
        print(f"{self._get_timestamp()} {Colors.ERROR}ERROR{Colors.RESET} {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"{self._get_timestamp()} {Colors.HEADER}DEBUG{Colors.RESET} {message}")

    def progress(self, current: int, total: int, prefix: str = ''):
        percentage = int((current / total) * 100)
        if percentage > self.last_progress:
            self.last_progress = percentage
            bar_length = 30
            filled_length = int(bar_length * current / total)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f"\r{prefix} |{bar}| {percentage}%", end='', flush=True)
            if percentage == 100:
                print()