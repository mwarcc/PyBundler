"""Code optimization utilities"""
import ast
from typing import Set, Dict

class DeadCodeEliminator(ast.NodeTransformer):
    """Remove unreachable and unused code"""
    def __init__(self):
        self.used_names: Set[str] = set()
        self.defined_names: Dict[str, ast.AST] = {}
        
    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        return node
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name not in self.used_names and not node.name.startswith('_'):
            return None
        return node

class ConstantFolder(ast.NodeTransformer):
    """Fold constant expressions"""
    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            try:
                if isinstance(node.op, ast.Add):
                    return ast.Constant(node.left.value + node.right.value)
                elif isinstance(node.op, ast.Mult):
                    return ast.Constant(node.left.value * node.right.value)
            except Exception:
                pass
                
        return node

class CodeOptimizer:
    """Apply various code optimizations"""
    def __init__(self):
        self.optimizers = [
            DeadCodeEliminator(),
            ConstantFolder()
        ]
        
    def optimize(self, tree: ast.AST) -> ast.AST:
        """Apply all optimizations"""
        for optimizer in self.optimizers:
            tree = optimizer.visit(tree)
        return tree