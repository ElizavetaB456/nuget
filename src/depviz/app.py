"""Основной сценарий работы приложения."""

import sys

from depviz.cli import ConfigError, parse_args
from depviz.graph import build_graph
from depviz.nuget import NuGetSource, RepositoryError
from depviz.order import load_order
from depviz.testrepo import TestRepoSource

EXIT_OK = 0
EXIT_REPO_ERROR = 1
EXIT_CONFIG_ERROR = 2


def make_source(config):
    """Создать источник зависимостей в зависимости от режима."""
    if config.test_mode:
        return TestRepoSource(config.repo)
    return NuGetSource(config.repo)


def _label(node):
    """Подпись вершины: имя и версия (если есть)."""
    return f"{node.name} {node.version}".strip()


def print_graph(graph):
    """Вывести граф зависимостей в виде списков смежности."""
    print(f"Граф зависимостей {graph.root} "
          f"(максимальная глубина {graph.max_depth}):")
    for name, node in graph.nodes.items():
        if name in graph.unexpanded:
            print(f"  [{node.depth}] {_label(node)} -> ... "
                  "(не раскрыт: достигнута максимальная глубина)")
            continue
        deps = ", ".join(graph.edges.get(name, [])) or "(нет)"
        print(f"  [{node.depth}] {_label(node)} -> {deps}")
    if graph.filtered:
        print("Исключены фильтром: " + ", ".join(sorted(graph.filtered)))
    for cycle in graph.cycles:
        print("Циклическая зависимость: " + " -> ".join(cycle))


def print_load_order(graph):
    """Вывести порядок загрузки зависимостей."""
    result = load_order(graph)
    print(f"Порядок загрузки зависимостей для {graph.root}:")
    for number, name in enumerate(result.order, 1):
        mark = " (разрыв цикла)" if name in result.cycle_breaks else ""
        print(f"  {number}. {_label(graph.nodes[name])}{mark}")


def run(config):
    """Выполнить анализ согласно параметрам."""
    source = make_source(config)
    version = source.check_version(config.package, config.version)
    graph = build_graph(source, config.package, version,
                        config.max_depth, config.filter)
    if config.load_order:
        print_load_order(graph)
    else:
        print_graph(graph)


def main(argv):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"Ошибка параметров: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    try:
        run(config)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_REPO_ERROR
    return EXIT_OK
