"""Enhanced import analysis with automatic import detection"""
import ast
import pkg_resources
import importlib
import sys
import os
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
from .logger import Logger

@dataclass
class ImportInfo:
    module: str
    names: List[str]
    alias: Optional[str] = None
    is_third_party: bool = False

class ImportAnalyzer:
    def __init__(self, logger: Logger, project_root: str):
        self.logger = logger
        self.project_root = os.path.abspath(project_root)
        self.stdlib_imports: Set[str] = set()
        self.third_party_imports: Set[str] = set()
        self.local_imports: Set[str] = set()
        self.import_info: List[ImportInfo] = []
        self.used_names: Set[str] = set()
        self.module_symbols: Dict[str, Set[str]] = {}
        self.processed_local_modules: Set[str] = set()
        
    def analyze_imports(self, content: str, file_path: str) -> None:
        """Analyze imports and symbol usage in content"""
        try:
            tree = ast.parse(content)
            
            # First pass: collect all imports
            import_collector = ImportCollector()
            import_collector.visit(tree)
            
            # Second pass: collect all used names
            name_collector = NameCollector()
            name_collector.visit(tree)
            
            # Process collected imports and names
            self._process_collected_imports(import_collector.imports, file_path)
            self._process_used_names(name_collector.names)
            
        except Exception as e:
            self.logger.warning(f"Import analysis failed: {e}")

    def _process_collected_imports(self, imports: List[Tuple], current_file: str) -> None:
        """Process collected imports and categorize them"""
        for imp_type, module, names, alias in imports:
            if imp_type == 'import':
                self._handle_import(module, alias, current_file)
            elif imp_type == 'fromimport':
                self._handle_from_import(module, names, current_file)

    def _handle_import(self, module: str, alias: Optional[str], current_file: str) -> None:
        """Handle regular import statements"""
        if self._is_local_module(module, current_file):
            # Skip local imports as they'll be bundled
            return
            
        import_str = f"import {module}"
        if alias:
            import_str += f" as {alias}"
            
        if self._is_stdlib_module(module):
            self.stdlib_imports.add(import_str)
        elif self._is_third_party(module):
            self.third_party_imports.add(import_str)
            
        # Store module symbols for later reference
        self._store_module_symbols(module)

    def _handle_from_import(self, module: str, names: List[Tuple[str, Optional[str]]], current_file: str) -> None:
        """Handle from ... import ... statements"""
        if self._is_local_module(module, current_file):
            # Skip local imports as they'll be bundled
            return
            
        names_str = ", ".join(f"{name}{' as '+alias if alias else ''}" 
                            for name, alias in names)
        import_str = f"from {module} import {names_str}"
        
        if self._is_stdlib_module(module):
            self.stdlib_imports.add(import_str)
        elif self._is_third_party(module):
            self.third_party_imports.add(import_str)
            
        # Store imported symbols
        for name, _ in names:
            self.used_names.add(name)

    def _is_local_module(self, module: str, current_file: str) -> bool:
        """Check if module is local to the project"""
        if module.startswith('.'):
            return True
            
        # Convert module to potential file path
        module_path = module.replace('.', os.sep)
        possible_paths = [
            os.path.join(self.project_root, module_path + '.py'),
            os.path.join(self.project_root, module_path, '__init__.py'),
            os.path.join(os.path.dirname(current_file), module_path + '.py'),
            os.path.join(os.path.dirname(current_file), module_path, '__init__.py')
        ]
        
        return any(os.path.exists(path) for path in possible_paths)

    def _store_module_symbols(self, module_name: str) -> None:
        """Store available symbols from a module"""
        try:
            if not self._is_local_module(module_name, ""):
                module = importlib.import_module(module_name)
                self.module_symbols[module_name] = set(dir(module))
        except ImportError:
            pass

    def _process_used_names(self, names: Set[str]) -> None:
        """Process collected used names and add required imports"""
        for name in names:
            # Check each module's symbols for the name
            for module, symbols in self.module_symbols.items():
                if name in symbols:
                    if self._is_stdlib_module(module):
                        self.stdlib_imports.add(f"from {module} import {name}")
                    elif self._is_third_party(module):
                        self.third_party_imports.add(f"from {module} import {name}")

    def _is_stdlib_module(self, module_name: str) -> bool:
        """Check if module is from standard library"""
        try:
            module_spec = importlib.util.find_spec(module_name.split('.')[0])
            if module_spec is None:
                return False
            return 'site-packages' not in str(module_spec.origin)
        except (ImportError, AttributeError):
            return False

    def _is_third_party(self, module_name: str) -> bool:
        """Check if module is third-party package"""
        try:
            module_spec = importlib.util.find_spec(module_name.split('.')[0])
            if module_spec is None:
                return False
            return 'site-packages' in str(module_spec.origin)
        except (ImportError, AttributeError):
            return False

    def get_formatted_imports(self) -> str:
        """Get formatted import statements"""
        sections = []
        
        if self.stdlib_imports:
            sections.extend([
                "# Standard library imports",
                *sorted(self.stdlib_imports),
                ""
            ])
            
        if self.third_party_imports:
            sections.extend([
                "# Third-party imports",
                *sorted(self.third_party_imports),
                ""
            ])
            
        return "\n".join(sections)

class ImportCollector(ast.NodeVisitor):
    """Collect all import statements from AST"""
    def __init__(self):
        self.imports = []  # [(type, module, names, alias)]

    def visit_Import(self, node):
        """Handle regular imports"""
        for name in node.names:
            self.imports.append(('import', name.name, [], name.asname))

    def visit_ImportFrom(self, node):
        """Handle from imports"""
        if node.module:
            names = [(n.name, n.asname) for n in node.names]
            self.imports.append(('fromimport', node.module, names, None))

class NameCollector(ast.NodeVisitor):
    """Collect all used names from AST"""
    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        """Record used names"""
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)
        self.generic_visit(node)