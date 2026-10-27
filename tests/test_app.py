"""Сквозные тесты приложения на тестовых репозиториях."""

import contextlib
import io
import os
import unittest

from depviz.app import EXIT_CONFIG_ERROR, EXIT_OK, EXIT_REPO_ERROR, main

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def run_app(*argv):
    """Запустить приложение, вернуть код и стандартный вывод."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue() + err.getvalue()


def example(name):
    """Путь к файлу тестового репозитория."""
    return os.path.join(EXAMPLES, name)


class AppTest(unittest.TestCase):
    """Режимы работы приложения."""

    def test_graph(self):
        """Вывод графа по умолчанию."""
        code, out = run_app("-p", "A", "-r", example("cycle.txt"), "-t")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Циклическая зависимость: A -> B -> C -> A", out)

    def test_load_order(self):
        """Режим порядка загрузки."""
        code, out = run_app("-p", "APP", "-r", example("diamond.txt"),
                            "-t", "-l")
        self.assertEqual(code, EXIT_OK)
        self.assertLess(out.index("CORE"), out.index("LOG"))

    def test_errors(self):
        """Коды завершения при ошибках."""
        code, _ = run_app("-p", "A", "-r", example("broken.txt"), "-t")
        self.assertEqual(code, EXIT_REPO_ERROR)
        code, _ = run_app("-p", "A")
        self.assertEqual(code, EXIT_CONFIG_ERROR)


if __name__ == "__main__":
    unittest.main()
