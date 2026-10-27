"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла (пакеты — большие латинские буквы):

    # комментарий
    A: B C
    B: C
    C:

Пакет, упомянутый только как зависимость, считается пакетом без
зависимостей.
"""

import re

from depviz.nuget import Dependency, RepositoryError

NAME_RE = re.compile(r"^[A-Z]+$")


def _parse_line(line, number):
    """Разобрать строку 'A: B C' в пару (пакет, список зависимостей)."""
    if ":" not in line:
        raise RepositoryError(f"строка {number}: ожидается 'ПАКЕТ: ЗАВ ...'")
    head, tail = line.split(":", 1)
    names = [head.strip()] + tail.split()
    for name in names:
        if not NAME_RE.match(name):
            raise RepositoryError(
                f"строка {number}: некорректное имя пакета '{name}'")
    return names[0], names[1:]


def parse_graph(text):
    """Разобрать описание тестового репозитория в словарь смежности."""
    graph = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, deps = _parse_line(line, number)
        if name in graph:
            raise RepositoryError(
                f"строка {number}: пакет {name} описан повторно")
        graph[name] = deps
    return graph


class TestRepoSource:
    """Источник зависимостей — файл тестового репозитория."""

    def __init__(self, path):
        """Прочитать и разобрать файл тестового репозитория."""
        try:
            with open(path, encoding="utf-8") as handle:
                self.graph = parse_graph(handle.read())
        except OSError as error:
            raise RepositoryError(f"не удалось прочитать {path}: {error}") \
                from None

    def _known(self, name):
        """Проверить, что пакет есть в репозитории."""
        mentioned = any(name in deps for deps in self.graph.values())
        if name not in self.graph and not mentioned:
            raise RepositoryError(f"пакет {name} не найден в репозитории")

    def check_version(self, name, version):
        """Версии в тестовом режиме не используются."""
        self._known(name)
        return version

    def direct_dependencies(self, name, version):
        """Прямые зависимости пакета из файла."""
        self._known(name)
        return [Dependency(dep, "", "") for dep in self.graph.get(name, [])]
