"""Визуализация графа зависимостей на языке диаграмм PlantUML."""

import os
import shutil
import subprocess
import webbrowser
import zlib
from pathlib import Path

SERVER_URL = "https://www.plantuml.com/plantuml/png/"
ALPHABET = ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz-_")
BITS_PER_CHAR = 6
CHARS_PER_CHUNK = 4
CHUNK_BYTES = 3
SIX_BITS = 0x3F
RENDER_TIMEOUT = 120

ROOT_STYLE = "#LightSkyBlue"
LEAF_STYLE = "#WhiteSmoke;line.dashed"
CYCLE_EDGE = "-[#red,bold]->"
NORMAL_EDGE = "-->"


def _alias(index):
    """Короткий идентификатор вершины в диаграмме."""
    return f"n{index}"


def _node_line(node, alias, graph):
    """Строка объявления вершины."""
    label = node.name if not node.version else \
        f"{node.name}\\n{node.version}"
    style = ""
    if node.name == graph.root:
        style = " " + ROOT_STYLE
    elif node.name in graph.unexpanded:
        style = " " + LEAF_STYLE
    return f'rectangle "{label}" as {alias}{style}'


def _cycle_edges(graph):
    """Множество рёбер (откуда, куда), лежащих на циклах."""
    result = set()
    for cycle in graph.cycles:
        result.update(zip(cycle, cycle[1:]))
    return result


def to_plantuml(graph):
    """Сформировать текст диаграммы PlantUML для графа."""
    aliases = {name: _alias(i) for i, name in enumerate(graph.nodes)}
    lines = ["@startuml", f"title Зависимости {graph.root}",
             "skinparam defaultTextAlignment center",
             "skinparam shadowing false"]
    for name, node in graph.nodes.items():
        lines.append(_node_line(node, aliases[name], graph))
    on_cycle = _cycle_edges(graph)
    for name, deps in graph.edges.items():
        for dep in deps:
            arrow = CYCLE_EDGE if (name, dep) in on_cycle else NORMAL_EDGE
            lines.append(f"{aliases[name]} {arrow} {aliases[dep]}")
    if graph.filtered:
        hidden = ", ".join(sorted(graph.filtered))
        lines.append(f"legend right\nИсключены фильтром: {hidden}\n"
                     "endlegend")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def encode(text):
    """Закодировать текст для URL сервера PlantUML (deflate + base64)."""
    compressor = zlib.compressobj(level=9, wbits=-zlib.MAX_WBITS)
    data = compressor.compress(text.encode("utf-8")) + compressor.flush()
    data += b"\0" * (-len(data) % CHUNK_BYTES)
    chars = []
    for start in range(0, len(data), CHUNK_BYTES):
        chunk = int.from_bytes(data[start:start + CHUNK_BYTES], "big")
        for shift in reversed(range(CHARS_PER_CHUNK)):
            chars.append(ALPHABET[(chunk >> shift * BITS_PER_CHAR)
                                  & SIX_BITS])
    return "".join(chars)


def _render_command(puml_path):
    """Команда локального рендеринга PlantUML или None."""
    if shutil.which("plantuml"):
        return ["plantuml", "-tpng", str(puml_path)]
    jar = os.environ.get("PLANTUML_JAR")
    if jar and shutil.which("java") and os.path.isfile(jar):
        return ["java", "-jar", jar, "-tpng", str(puml_path)]
    return None


def render(text, puml_path):
    """Сохранить .puml и получить изображение.

    Возвращает путь к PNG (если доступен локальный PlantUML) или URL
    изображения на сервере PlantUML.
    """
    puml_path = Path(puml_path)
    puml_path.parent.mkdir(parents=True, exist_ok=True)
    puml_path.write_text(text, encoding="utf-8")
    command = _render_command(puml_path)
    if command:
        try:
            subprocess.run(command, check=True, timeout=RENDER_TIMEOUT)
            return str(puml_path.with_suffix(".png"))
        except (OSError, subprocess.SubprocessError):
            pass
    return SERVER_URL + encode(text)


def show(target):
    """Открыть изображение (файл или URL) в программе просмотра."""
    if target.startswith("http"):
        return webbrowser.open(target)
    return webbrowser.open(Path(target).resolve().as_uri())
