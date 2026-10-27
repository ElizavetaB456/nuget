"""Порядок загрузки зависимостей: каждый пакет — после своих зависимостей.

Используется алгоритм Кана (топологическая сортировка без рекурсии).
Среди готовых к загрузке пакетов первым берётся меньший по имени,
чтобы результат был детерминированным. Если готовых пакетов нет, а
незагруженные остались, значит есть цикл: он разрывается загрузкой
пакета с наименьшим числом незагруженных зависимостей, и этот пакет
помечается как загруженный раньше части своих зависимостей.
Зависимость пакета от самого себя загрузку не блокирует.
"""

import heapq
from dataclasses import dataclass, field


@dataclass
class LoadOrder:
    """Результат: порядок загрузки и пакеты, на которых разорван цикл."""

    order: list = field(default_factory=list)
    cycle_breaks: list = field(default_factory=list)


def _count_dependencies(graph):
    """Число ещё не загруженных зависимостей и обратные рёбра."""
    pending, dependents = {}, {name: [] for name in graph.nodes}
    for name in graph.nodes:
        deps = set(graph.edges.get(name, [])) - {name}
        pending[name] = len(deps)
        for dep in deps:
            dependents[dep].append(name)
    return pending, dependents


def _break_cycle(pending):
    """Выбрать пакет для разрыва цикла."""
    return min(pending, key=lambda name: (pending[name], name))


def load_order(graph):
    """Вычислить порядок загрузки пакетов графа."""
    pending, dependents = _count_dependencies(graph)
    ready = [name for name, count in pending.items() if count == 0]
    heapq.heapify(ready)
    result = LoadOrder()
    while pending:
        if not ready:
            name = _break_cycle(pending)
            result.cycle_breaks.append(name)
        else:
            name = heapq.heappop(ready)
        del pending[name]
        result.order.append(name)
        for parent in dependents[name]:
            if parent in pending:
                pending[parent] -= 1
                if pending[parent] == 0:
                    heapq.heappush(ready, parent)
    return result
