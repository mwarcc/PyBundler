"""Command-line interface for PyBundler"""
import argparse
from .bundler import PyBundler
from .utils.logger import Logger

def main():
    parser = argparse.ArgumentParser(description='Enhanced Python source file bundler')
    parser.add_argument('-p', '--path', required=True, help='Path to the source folder')
    parser.add_argument('-f', '--file', required=True, help='Main Python file')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    logger = Logger(verbose=args.verbose)
    bundler = PyBundler(args.path, args.file, logger)
    bundler.bundle(args.output)

if __name__ == '__main__':
    main()