"""Тесты порядка загрузки зависимостей."""

import unittest

from depviz.graph import DependencyGraph
from depviz.order import load_order


def make_graph(edges):
    """Создать граф по словарю смежности."""
    graph = DependencyGraph(root=next(iter(edges)), max_depth=1)
    graph.nodes = {name: None for name in edges}
    graph.edges = edges
    return graph


class LoadOrderTest(unittest.TestCase):
    """Топологический порядок и обработка циклов."""

    def test_dependencies_first(self):
        """Каждый пакет идёт после всех своих зависимостей."""
        edges = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        result = load_order(make_graph(edges))
        self.assertEqual(result.order, ["D", "B", "C", "A"])
        self.assertEqual(result.cycle_breaks, [])

    def test_cycle_break(self):
        """Цикл разрывается, все пакеты попадают в порядок."""
        edges = {"A": ["B"], "B": ["C"], "C": ["A"]}
        result = load_order(make_graph(edges))
        self.assertEqual(result.order, ["A", "C", "B"])
        self.assertEqual(result.cycle_breaks, ["A"])

    def test_self_loop(self):
        """Петля обрабатывается."""
        result = load_order(make_graph({"A": ["A"]}))
        self.assertEqual(result.order, ["A"])


if __name__ == "__main__":
    unittest.main()
