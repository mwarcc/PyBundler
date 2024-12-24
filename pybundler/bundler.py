"""Main bundler implementation with advanced features"""
import os
import ast
import sys
import hashlib
from typing import Set, Optional, List, Dict, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .utils.logger import Logger
from .utils.file_ops import FileOps
from .utils.import_analyzer import ImportAnalyzer
from .utils.ast_transformers import CodeOptimizer, ImportProcessor, ImportRemover
from .utils.dependency_graph import DependencyGraph

@dataclass
class BundleStats:
    """Statistics about the bundling process"""
    total_files: int
    total_lines: int
    total_imports: int
    processing_time: float
    file_sizes: Dict[str, int]
    optimization_savings: int

class PyBundler:
    def __init__(self, folder_path: str, main_file: str, logger: Optional[Logger] = None):
        self.folder_path = os.path.abspath(folder_path)
        self.main_file = main_file
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        self.logger = logger or Logger()
        self.file_ops = FileOps(self.logger)
        self.dependency_graph = DependencyGraph()
        self.import_analyzer = ImportAnalyzer(self.logger, self.folder_path)
        self.stats = BundleStats(0, 0, 0, 0.0, {}, 0)
        self.cache: Dict[str, Tuple[str, int]] = {}  # file_path -> (content_hash, line_count)
        
        # Track internal modules and their exports
        self.internal_modules: Dict[str, Set[str]] = {}  # module -> {exported names}
        self.module_aliases: Dict[str, str] = {}  # alias -> full module name
        self.project_root_module = os.path.basename(folder_path)

    def bundle(self, output_file: str):
        """Bundle the project into a single file with advanced features"""
        self.logger.info(f"Starting enhanced bundling process for {self.main_file}")
        start_time = datetime.now()

        main_path = os.path.join(self.folder_path, self.main_file)
        if not os.path.exists(main_path):
            self.logger.error(f"Main file '{main_path}' not found")
            sys.exit(1)

        self.logger.info("Analyzing project structure and dependencies...")
        
        # First pass: collect all internal modules and their exports
        self._collect_internal_modules()
        
        # Initialize statistics
        original_size = 0
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    content = self.file_ops.read_file(file_path)
                    if content:
                        size = len(content.encode('utf-8'))
                        original_size += size
                        self.stats.file_sizes[file_path] = size

        # Process files with parallel execution
        with ThreadPoolExecutor() as executor:
            bundled_content = self._process_files_parallel(main_path, executor)

        self.logger.info("\nDependency analysis complete")
        print(self.dependency_graph.get_visualization())

        # Generate final content
        content = [
            self._generate_bundle_header(),
            self._clean_imports(self.import_analyzer.get_formatted_imports()),
            bundled_content,
            self._generate_bundle_footer()
        ]

        final_content = '\n'.join(content)
        
        # Calculate optimization statistics
        final_size = len(final_content.encode('utf-8'))
        self.stats.optimization_savings = original_size - final_size
        
        if not self.file_ops.write_file(output_file, final_content):
            sys.exit(1)

        self.stats.processing_time = (datetime.now() - start_time).total_seconds()
        self._display_bundle_stats()

    def _collect_internal_modules(self):
        """Collect all internal modules and their exports"""
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(root, self.folder_path)
                    module_path = os.path.join(rel_path, file[:-3]).replace(os.sep, '.')
                    if module_path.startswith('.'):
                        module_path = module_path[1:]
                    
                    # Parse the file to get exports
                    file_path = os.path.join(root, file)
                    content = self.file_ops.read_file(file_path)
                    if content:
                        try:
                            tree = ast.parse(content)
                            exports = set()
                            
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                                    exports.add(node.name)
                                elif isinstance(node, ast.Assign):
                                    for target in node.targets:
                                        if isinstance(target, ast.Name):
                                            exports.add(target.id)
                            
                            self.internal_modules[module_path] = exports
                        except Exception as e:
                            self.logger.warning(f"Failed to parse {file_path}: {e}")

    def _clean_imports(self, imports: str) -> str:
        """Remove internal module imports and deduplicate imports"""
        cleaned_lines = []
        seen_imports = set()
        
        for line in imports.split('\n'):
            # Keep comments and empty lines
            if not line.strip() or line.strip().startswith('#'):
                if line not in seen_imports:
                    seen_imports.add(line)
                    cleaned_lines.append(line)
                continue
            
            # Skip internal module imports
            skip = False
            for module_path in self.internal_modules:
                if module_path in line or self.project_root_module in line:
                    skip = True
                    break
            
            if not skip and line not in seen_imports:
                seen_imports.add(line)
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _fix_internal_references(self, content: str) -> str:
        """Fix internal module references to use direct names"""
        try:
            tree = ast.parse(content)
            
            class InternalRefFixer(ast.NodeTransformer):
                def __init__(self, bundler):
                    self.bundler = bundler
                
                def visit_ImportFrom(self, node):
                    # Remove internal imports
                    if node.module in self.bundler.internal_modules:
                        return None
                    return node
                
                def visit_Attribute(self, node):
                    # Convert module.function to just function for internal modules
                    if isinstance(node.value, ast.Name):
                        module_name = node.value.id
                        for internal_module, exports in self.bundler.internal_modules.items():
                            if module_name in internal_module.split('.'):
                                if node.attr in exports:
                                    return ast.Name(id=node.attr, ctx=node.ctx)
                    return node
            
            fixer = InternalRefFixer(self)
            fixed_tree = fixer.visit(tree)
            return ast.unparse(fixed_tree)
        except Exception as e:
            self.logger.warning(f"Failed to fix internal references: {e}")
            return content

    def _process_files_parallel(self, entry_point: str, executor) -> str:
        """Process files in parallel for better performance"""
        def process_single_file(file_path: str) -> Tuple[str, List[str]]:
            content = self.file_ops.read_file(file_path)
            if not content:
                return "", []
            
            # Calculate file hash for caching
            content_hash = hashlib.md5(content.encode()).hexdigest()
            if file_path in self.cache and self.cache[file_path][0] == content_hash:
                return "", []  # File hasn't changed, skip processing
                
            self.import_analyzer.analyze_imports(content, file_path)
            imported_files = self._get_imports(content, file_path)
            
            # Clean and optimize code
            cleaned_content = self._clean_and_optimize_code(content, file_path)
            
            # Update cache
            self.cache[file_path] = (content_hash, len(content.splitlines()))
            
            return cleaned_content, imported_files

        def process_file_tree(file_path: str) -> str:
            if file_path in self.processed_files:
                return ""

            self.processed_files.add(file_path)
            content, imported_files = process_single_file(file_path)
            
            # Process imported files in parallel
            future_results = [
                executor.submit(process_file_tree, imported_file)
                for imported_file in imported_files
            ]
            
            imported_contents = [
                future.result() for future in future_results
            ]
            
            # Update statistics
            self.stats.total_files += 1
            self.stats.total_lines += self.cache.get(file_path, (None, 0))[1]
            self.stats.total_imports += len(imported_files)

            result = []
            result.extend(imported_contents)
            
            if content:
                rel_path = os.path.relpath(file_path, self.folder_path)
                result.extend([
                    f"\n# {'=' * 78}",
                    f"# Source from: {rel_path}",
                    f"# {'=' * 78}",
                    self._fix_internal_references(content)
                ])

            return "\n".join(result)

        return process_file_tree(entry_point)

    def _get_imports(self, content: str, file_path: str) -> List[str]:
        """Enhanced import processing with advanced filtering"""
        try:
            tree = ast.parse(content)
            processor = ImportProcessor()
            processor.visit(tree)
            
            imported_files = []
            
            # Process standard imports with advanced filtering
            for module_name in processor.imports:
                if self._should_process_import(module_name):
                    module_path = self._resolve_import_path(module_name, file_path)
                    if module_path:
                        imported_files.append(module_path)
                        self.dependency_graph.add_dependency(file_path, module_path)
            
            # Process from imports with advanced filtering
            for module_name, names in processor.from_imports:
                if self._should_process_import(module_name):
                    module_path = self._resolve_import_path(module_name, file_path)
                    if module_path:
                        imported_files.append(module_path)
                        self.dependency_graph.add_dependency(file_path, module_path)
            
            return imported_files
            
        except Exception as e:
            self.logger.warning(f"Failed to process imports in {file_path}: {e}")
            return []

    def _should_process_import(self, module_name: str) -> bool:
        """Determine if an import should be processed"""
        # Skip standard library modules
        stdlib_modules = {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
            'concurrent', 'contextlib', 'copy', 'csv', 'dataclasses',
            'datetime', 'decimal', 'difflib', 'enum', 'functools', 'glob',
            'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'importlib',
            'inspect', 'io', 'itertools', 'json', 'logging', 'math',
            'multiprocessing', 'operator', 'os', 'pathlib', 'pickle',
            'platform', 'pprint', 'queue', 're', 'random', 'shutil',
            'signal', 'socket', 'sqlite3', 'statistics', 'string',
            'subprocess', 'sys', 'tempfile', 'threading', 'time', 'timeit',
            'typing', 'unittest', 'urllib', 'uuid', 'warnings', 'weakref',
            'xml', 'zipfile'
        }
        
        base_module = module_name.split('.')[0]
        return base_module not in stdlib_modules

    def _resolve_import_path(self, module_name: str, current_file: str) -> Optional[str]:
        """Enhanced import path resolution"""
        def check_path(path: str) -> Optional[str]:
            if os.path.isfile(path):
                return path
            return None

        # Try relative to current file
        current_dir = os.path.dirname(current_file)
        relative_paths = [
            os.path.join(current_dir, *module_name.split('.')) + '.py',
            os.path.join(current_dir, *module_name.split('.'), '__init__.py'),
            os.path.join(current_dir, '..', *module_name.split('.')) + '.py',
            os.path.join(current_dir, '..', *module_name.split('.'), '__init__.py')
        ]

        # Try relative to project root
        root_paths = [
            os.path.join(self.folder_path, *module_name.split('.')) + '.py',
            os.path.join(self.folder_path, *module_name.split('.'), '__init__.py')
        ]

        # Check all possible paths
        for path in relative_paths + root_paths:
            normalized_path = os.path.normpath(path)
            if result := check_path(normalized_path):
                return result

        return None

    def _clean_and_optimize_code(self, content: str, file_path: str) -> str:
        """Clean and optimize code with advanced techniques"""
        try:
            # Parse and clean imports
            tree = ast.parse(content)
            remover = ImportRemover()
            cleaned = remover.visit(tree)

            # Apply advanced optimizations
            optimizer = CodeOptimizer()
            optimized = optimizer.optimize(cleaned)

            # Additional optimizations
            optimized = self._apply_advanced_optimizations(optimized)

            return ast.unparse(optimized)
        except Exception as e:
            self.logger.warning(f"Failed to optimize {file_path}: {e}")
            return content

    def _apply_advanced_optimizations(self, tree: ast.AST) -> ast.AST:
        """Apply additional advanced optimizations"""
        class AdvancedOptimizer(ast.NodeTransformer):
            def visit_If(self, node):
                # Optimize if statements with constant conditions
                self.generic_visit(node)
                if isinstance(node.test, ast.Constant):
                    if node.test.value:
                        return node.body
                    else:
                        return node.orelse
                return node

            def visit_BinOp(self, node):
                # Optimize constant binary operations
                self.generic_visit(node)
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                    try:
                        if isinstance(node.op, ast.Add):
                            return ast.Constant(node.left.value + node.right.value)
                        elif isinstance(node.op, ast.Mult):
                            return ast.Constant(node.left.value * node.right.value)
                    except:
                        pass
                return node

        return AdvancedOptimizer().visit(tree)

    def _generate_bundle_header(self) -> str:
        """Generate comprehensive bundle header"""
        return f'''#!/usr/bin/env python3
"""
Generated by PyBundler v2.0
https://github.com/yourusername/pybundler

Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Original Main File: {self.main_file}
Total Files: {self.stats.total_files}
Total Lines: {self.stats.total_lines}

This is a self-contained Python bundle generated from multiple source files.
All imports have been resolved and optimized for better performance.
"""
'''

    def _generate_bundle_footer(self) -> str:
        """Generate bundle footer with execution guard"""
        return '''
### Made with pybundler <3
'''

    def _display_bundle_stats(self):
        """Display comprehensive bundling statistics"""
        self.logger.success(f"\nBundling completed successfully!")
        self.logger.info("\nBundle Statistics:")
        print(f"{'=' * 50}")
        print(f"Total files processed: {self.stats.total_files}")
        print(f"Total lines of code: {self.stats.total_lines}")
        print(f"Total imports resolved: {self.stats.total_imports}")
        print(f"Processing time: {self.stats.processing_time:.2f}s")
        print(f"Size optimization: {self.stats.optimization_savings / 1024:.1f}KB saved")
        print(f"{'=' * 50}")