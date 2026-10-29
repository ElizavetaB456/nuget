"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии."""

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Node:
    """Вершина графа: пакет, выбранная версия и глубина от корня."""

    name: str
    version: str
    depth: int


@dataclass
class DependencyGraph:
    """Граф зависимостей с результатами анализа."""

    root: str
    max_depth: int
    nodes: dict = field(default_factory=dict)
    edges: dict = field(default_factory=dict)
    filtered: set = field(default_factory=set)
    unexpanded: set = field(default_factory=set)
    cycles: list = field(default_factory=list)


class NameTable:
    """Приведение имён пакетов NuGet (регистронезависимых) к одному виду."""

    def __init__(self):
        """Создать пустую таблицу имён."""
        self.known = {}

    def canon(self, name):
        """Вернуть первое встреченное написание имени."""
        return self.known.setdefault(name.lower(), name)


def build_graph(source, root, version, max_depth, substring=""):
    """Построить граф зависимостей пакета root (BFS, глубина <= max_depth).

    Пакеты, имя которых содержит substring (без учёта регистра),
    в анализ не включаются. Каждый пакет раскрывается один раз, поэтому
    циклические зависимости не приводят к зацикливанию.
    """
    names, needle = NameTable(), substring.lower()
    graph = DependencyGraph(names.canon(root), max_depth)
    graph.nodes[graph.root] = Node(graph.root, version, 0)
    queue = deque([graph.nodes[graph.root]])
    while queue:
        node = queue.popleft()
        if node.depth >= max_depth:
            graph.unexpanded.add(node.name)
            continue
        graph.edges[node.name] = []
        for dep in source.direct_dependencies(node.name, node.version):
            name = names.canon(dep.name)
            if needle and needle in name.lower():
                graph.filtered.add(name)
                continue
            graph.edges[node.name].append(name)
            if name not in graph.nodes:
                graph.nodes[name] = Node(name, dep.version, node.depth + 1)
                queue.append(graph.nodes[name])
    graph.cycles = find_cycles(graph.edges)
    return graph


def _cycle_from(path, target):
    """Выделить цикл из текущего пути обхода."""
    start = path.index(target)
    return path[start:] + [target]


def find_cycles(edges):
    """Найти циклы (по обратным рёбрам) итеративным обходом в глубину."""
    done, cycles = set(), []
    for start in edges:
        if start in done:
            continue
        path, on_path = [start], {start}
        stack = [iter(edges.get(start, []))]
        while stack:
            nxt = next(stack[-1], None)
            if nxt is None:
                stack.pop()
                done.add(path[-1])
                on_path.discard(path.pop())
            elif nxt in on_path:
                cycles.append(_cycle_from(path, nxt))
            elif nxt not in done:
                path.append(nxt)
                on_path.add(nxt)
                stack.append(iter(edges.get(nxt, [])))
    return cycles
