"""Code metrics analyzer for PyBundler"""
import ast
from typing import Dict, Set, NamedTuple
from dataclasses import dataclass

@dataclass
class FunctionMetrics:
    complexity: int
    line_count: int
    parameter_count: int
    return_count: int

class CodeMetricsAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.metrics: Dict[str, FunctionMetrics] = {}
        self.current_function: str = None
        self.return_count: int = 0
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.current_function = node.name
        self.return_count = 0
        
        # Calculate metrics
        complexity = self._calculate_complexity(node)
        line_count = node.end_lineno - node.lineno
        param_count = len([arg for arg in node.args.args])
        
        # Visit function body to count returns
        self.generic_visit(node)
        
        self.metrics[node.name] = FunctionMetrics(
            complexity=complexity,
            line_count=line_count,
            parameter_count=param_count,
            return_count=self.return_count
        )
        
    def visit_Return(self, node: ast.Return):
        if self.current_function:
            self.return_count += 1
            
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
                
        return complexity