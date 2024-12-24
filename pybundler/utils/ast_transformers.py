"""AST transformation utilities for PyBundler"""
import ast
from typing import Set

class CodeOptimizer(ast.NodeTransformer):
    """AST transformer for code optimization"""
    def __init__(self):
        self.unused_imports = set()
        self.used_names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        return node

    def optimize(self, tree: ast.AST) -> ast.AST:
        """Apply various optimization techniques"""
        self.visit(tree)
        return tree

class ImportProcessor(ast.NodeTransformer):
    """Enhanced AST transformer for import handling"""
    def __init__(self):
        self.imports = []
        self.from_imports = []

    def visit_Import(self, node):
        self.imports.extend(n.name for n in node.names)
        return None
        
    def visit_ImportFrom(self, node):
        if node.module:
            self.from_imports.append((node.module, [n.name for n in node.names]))
        return None

class ImportRemover(ast.NodeTransformer):
    """Remove import statements from AST"""
    def visit_Import(self, node):
        return None
        
    def visit_ImportFrom(self, node):
        return None