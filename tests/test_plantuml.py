"""Тесты формирования диаграммы PlantUML."""

import os
import tempfile
import unittest
import zlib
from unittest import mock

from depviz import plantuml
from depviz.graph import build_graph
from test_graph import DictSource

MAX = 10


def decode(code):
    """Обратное преобразование для encode (для проверки)."""
    bits = "".join(f"{plantuml.ALPHABET.index(ch):06b}" for ch in code)
    data = int(bits, 2).to_bytes(len(bits) // 8, "big")
    return zlib.decompressobj(-zlib.MAX_WBITS).decompress(data).decode()


def sample_text():
    """PlantUML-текст графа с циклом, фильтром и ограничением глубины."""
    src = DictSource("A: B XC\nB: A D\nD: E\nE:")
    return plantuml.to_plantuml(build_graph(src, "A", "", 2, "X"))


class PlantUmlTest(unittest.TestCase):
    """Текст диаграммы, кодирование и получение изображения."""

    def test_text(self):
        """Вершины, рёбра, цикл и легенда присутствуют."""
        self.assertTrue(sample_text().startswith("@startuml"))
        self.assertIn('rectangle "A" as n0 #LightSkyBlue', sample_text())
        self.assertIn("n0 -[#red,bold]-> n1", sample_text())
        self.assertIn("n1 --> n2", sample_text())
        self.assertIn("Исключены фильтром: XC", sample_text())
        self.assertNotIn('"E"', sample_text())

    def test_unexpanded_style(self):
        """Нераскрытые вершины рисуются пунктиром."""
        self.assertIn('"D" as n2 #WhiteSmoke;line.dashed', sample_text())

    def test_known_encoding(self):
        """Кодирование совпадает с примером из документации PlantUML."""
        self.assertEqual(plantuml.encode("Bob -> Alice : hello"),
                         "SyfFKj2rKt3CoKnELR1Io4ZDoSa70000")

    def test_roundtrip(self):
        """Закодированный текст декодируется обратно."""
        self.assertEqual(decode(plantuml.encode(sample_text())), sample_text())

    def test_render_fallback(self):
        """Без локального PlantUML возвращается URL сервера."""
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(plantuml.shutil, "which",
                                  return_value=None):
            path = os.path.join(tmp, "out", "g.puml")
            target = plantuml.render(sample_text(), path)
            self.assertTrue(os.path.isfile(path))
        self.assertTrue(target.startswith(plantuml.SERVER_URL))


if __name__ == "__main__":
    unittest.main()
