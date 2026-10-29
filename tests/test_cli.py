"""Тесты разбора параметров командной строки."""

import os
import tempfile
import unittest

from depviz.cli import ConfigError, parse_args

REPO = "https://api.nuget.org/v3/index.json"


class ParseArgsTest(unittest.TestCase):
    """Проверка разбора и валидации параметров."""

    def temp_repo(self):
        """Создать временный файл тестового репозитория.

        Файл удаляется автоматически после завершения теста.
        """
        handle, path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)
        self.addCleanup(os.remove, path)
        return path

    def test_full_config(self):
        """Корректные параметры разбираются без ошибок."""
        config = parse_args(["-p", "Serilog", "-r", REPO, "-v", "4.0.0",
                             "-d", "2", "-f", "Test"])
        self.assertEqual(config.package, "Serilog")
        self.assertEqual(config.max_depth, 2)
        self.assertFalse(config.test_mode)

    def test_test_mode(self):
        """В тестовом режиме версия не обязательна."""
        config = parse_args(["-p", "A", "-r", self.temp_repo(), "-t"])
        self.assertTrue(config.test_mode)
        self.assertEqual(config.version, "")

    def assert_error(self, argv):
        """Убедиться, что параметры вызывают ConfigError."""
        with self.assertRaises(ConfigError):
            parse_args(argv)

    def test_missing_package(self):
        """Имя пакета обязательно."""
        self.assert_error(["-r", REPO, "-v", "1.0.0"])

    def test_bad_package(self):
        """Имя пакета проверяется."""
        self.assert_error(["-p", "bad name", "-r", REPO, "-v", "1.0"])
        self.assert_error(["-p", "abc", "-r", self.temp_repo(), "-t"])

    def test_bad_repo(self):
        """URL и путь к файлу проверяются."""
        self.assert_error(["-p", "X", "-r", "ftp://host", "-v", "1.0"])
        self.assert_error(["-p", "A", "-r", "/no/such/file", "-t"])

    def test_bad_version(self):
        """Версия обязательна и проверяется."""
        self.assert_error(["-p", "X", "-r", REPO])
        self.assert_error(["-p", "X", "-r", REPO, "-v", "one"])

    def test_bad_depth(self):
        """Глубина должна быть положительным целым."""
        self.assert_error(["-p", "X", "-r", REPO, "-v", "1", "-d", "0"])
        self.assert_error(["-p", "X", "-r", REPO, "-v", "1", "-d", "x"])

    def test_bad_filter(self):
        """Фильтр не может исключать сам пакет."""
        self.assert_error(["-p", "Serilog", "-r", REPO, "-v", "1",
                           "-f", "seri"])
        self.assert_error(["-p", "X", "-r", REPO, "-v", "1", "-f", " a"])


if __name__ == "__main__":
    unittest.main()
