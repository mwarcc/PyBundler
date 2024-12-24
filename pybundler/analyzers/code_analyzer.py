"""Code analysis utilities for PyBundler"""
import ast
from typing import Dict, List, Set

class CodeAnalyzer:
    def __init__(self):
        self.imports: Set[str] = set()
        self.functions: Set[str] = set()
        self.classes: Set[str] = set()
        self.complexity: Dict[str, int] = {}

    def analyze_file(self, content: str) -> Dict:
        """Analyze Python code and return metrics"""
        tree = ast.parse(content)
        self._collect_metrics(tree)
        
        return {
            'imports': list(self.imports),
            'functions': list(self.functions),
            'classes': list(self.classes),
            'complexity': self.complexity
        }

    def _collect_metrics(self, tree: ast.AST):
        """Collect various code metrics"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.imports.update(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports.add(node.module)
            elif isinstance(node, ast.FunctionDef):
                self.functions.add(node.name)
                self.complexity[node.name] = self._calculate_complexity(node)
            elif isinstance(node, ast.ClassDef):
                self.classes.add(node.name)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity