"""Enhanced dependency analysis"""
import ast
from typing import Dict, Set, List
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class DependencyInfo:
    direct: Set[str]
    indirect: Set[str]
    circular: List[List[str]]
    
class DependencyAnalyzer:
    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.visited: Set[str] = set()
        
    def analyze(self, entry_point: str) -> DependencyInfo:
        """Analyze dependencies starting from entry point"""
        self._build_graph(entry_point)
        
        return DependencyInfo(
            direct=self.graph[entry_point],
            indirect=self._find_indirect_deps(entry_point),
            circular=self._find_circular_deps()
        )
        
    def _build_graph(self, file_path: str):
        """Build dependency graph"""
        if file_path in self.visited:
            return
            
        self.visited.add(file_path)
        
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        self.graph[file_path].add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.graph[file_path].add(node.module)
                        
            # Recursively process dependencies
            for dep in self.graph[file_path]:
                self._build_graph(dep)
                
        except Exception:
            pass
            
    def _find_indirect_deps(self, start: str) -> Set[str]:
        """Find all indirect dependencies"""
        indirect = set()
        
        def visit(node: str):
            for dep in self.graph[node]:
                if dep != start and dep not in self.graph[start]:
                    indirect.add(dep)
                    visit(dep)
                    
        visit(start)
        return indirect
        
    def _find_circular_deps(self) -> List[List[str]]:
        """Detect circular dependencies"""
        circular = []
        path = []
        
        def visit(node: str):
            if node in path:
                cycle = path[path.index(node):]
                if cycle not in circular:
                    circular.append(cycle)
                return
                
            path.append(node)
            for dep in self.graph[node]:
                visit(dep)
            path.pop()
            
        for node in self.graph:
            visit(node)
            
        return circular