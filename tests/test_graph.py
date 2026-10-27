"""Тесты построения графа и тестового репозитория."""

import unittest

from depviz.graph import build_graph, find_cycles
from depviz.nuget import NuGetSource, RepositoryError
from depviz.testrepo import parse_graph
from fake_nuget import INDEX_URL, FakeRepo

MAX = 10


class DictSource:
    """Источник зависимостей на основе словаря (тестовый репозиторий)."""

    def __init__(self, text):
        """Разобрать описание графа."""
        self.graph = parse_graph(text)
        self.calls = []

    def direct_dependencies(self, name, version):
        """Вернуть зависимости и запомнить вызов."""
        self.calls.append(name)
        return [type("D", (), {"name": dep, "version": ""})
                for dep in self.graph.get(name, [])]


class GraphTest(unittest.TestCase):
    """BFS, глубина, фильтр, циклы."""

    def test_bfs_order(self):
        """Вершины добавляются в порядке обхода в ширину."""
        src = DictSource("A: B C\nB: D\nC: E\nD:\nE:")
        graph = build_graph(src, "A", "", MAX)
        self.assertEqual(list(graph.nodes), ["A", "B", "C", "D", "E"])
        self.assertEqual(graph.nodes["E"].depth, 2)

    def test_depth(self):
        """Вершины на максимальной глубине не раскрываются."""
        graph = build_graph(DictSource("A: B\nB: C\nC: D"), "A", "", 1)
        self.assertEqual(set(graph.nodes), {"A", "B"})
        self.assertEqual(graph.unexpanded, {"B"})

    def test_filter(self):
        """Пакеты с подстрокой в имени исключаются вместе с поддеревом."""
        src = DictSource("A: B XB\nXB: C\nB:")
        graph = build_graph(src, "A", "", MAX, "x")
        self.assertEqual(set(graph.nodes), {"A", "B"})
        self.assertEqual(graph.filtered, {"XB"})

    def test_cycle(self):
        """Цикл обнаруживается, каждый пакет запрашивается один раз."""
        src = DictSource("A: B\nB: C\nC: A B")
        graph = build_graph(src, "A", "", MAX)
        self.assertEqual(src.calls, ["A", "B", "C"])
        self.assertEqual(graph.cycles,
                         [["A", "B", "C", "A"], ["B", "C", "B"]])

    def test_self_loop(self):
        """Петля — тоже цикл."""
        self.assertEqual(find_cycles({"A": ["A"]}), [["A", "A"]])

    def test_nuget_graph(self):
        """Граф строится и по репозиторию NuGet."""
        fake = FakeRepo({("App", "1.0.0"): [("Lib", "1.0")],
                         ("Lib", "1.0.0"): [("app", "1.0")]})
        graph = build_graph(NuGetSource(INDEX_URL, fake), "App",
                            "1.0.0", MAX)
        self.assertEqual(graph.cycles, [["App", "Lib", "App"]])


class TestRepoFormatTest(unittest.TestCase):
    """Разбор файла тестового репозитория."""

    def test_comments(self):
        """Комментарии и пустые строки пропускаются."""
        self.assertEqual(parse_graph("# x\n\nA: B # c\n"), {"A": ["B"]})

    def test_errors(self):
        """Ошибки формата сообщаются с номером строки."""
        for text in ("A B", "a: B", "A: B\nA: C"):
            with self.assertRaises(RepositoryError):
                parse_graph(text)


if __name__ == "__main__":
    unittest.main()
