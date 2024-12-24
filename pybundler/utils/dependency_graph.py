"""Dependency graph management for PyBundler"""
from typing import Dict, Set

class DependencyGraph:
    """Track and visualize module dependencies"""
    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        
    def add_dependency(self, source: str, target: str):
        if source not in self.graph:
            self.graph[source] = set()
        self.graph[source].add(target)

    def get_visualization(self) -> str:
        """Return ASCII visualization of the dependency graph"""
        result = ["\033[1mDependency Graph:\033[0m"]
        for source, targets in self.graph.items():
            source_name = source.split('/')[-1]
            result.append(f"├── {source_name}")
            for target in targets:
                target_name = target.split('/')[-1]
                result.append(f"│   └── {target_name}")
        return "\n".join(result)