"""Тесты работы с версиями NuGet."""

import unittest

from depviz.versions import (VersionError, lowest_matching, normalize,
                             parse_range, version_key)


class VersionTest(unittest.TestCase):
    """Сравнение, нормализация и диапазоны версий."""

    def test_compare(self):
        """Порядок версий соответствует правилам NuGet."""
        self.assertLess(version_key("1.2"), version_key("1.10"))
        self.assertLess(version_key("1.0.0-beta"), version_key("1.0.0"))
        self.assertEqual(version_key("1.0"), version_key("1.0.0.0"))

    def test_normalize(self):
        """Нормализация: три части, четвёртая только если не 0."""
        self.assertEqual(normalize("1.0"), "1.0.0")
        self.assertEqual(normalize("1.2.3.0"), "1.2.3")
        self.assertEqual(normalize("1.2.3.4"), "1.2.3.4")
        self.assertEqual(normalize("2.0.0-RC1+meta"), "2.0.0-rc1")

    def test_ranges(self):
        """Разбор диапазонов разных видов."""
        self.assertTrue(parse_range("1.0").contains("5.0"))
        self.assertFalse(parse_range("[1.0,2.0)").contains("2.0"))
        self.assertTrue(parse_range("(,2.0]").contains("2.0"))
        self.assertFalse(parse_range("[1.5]").contains("1.6"))
        self.assertTrue(parse_range("").contains("0.1"))

    def test_bad_range(self):
        """Некорректные диапазоны отклоняются."""
        for text in ("[]", "(1.0)", "abc", "[1.0,x]"):
            with self.assertRaises(VersionError):
                parse_range(text)

    def test_lowest(self):
        """Выбирается минимальная подходящая стабильная версия."""
        known = ["1.0.0", "1.1.0-beta", "1.1.0", "2.0.0"]
        self.assertEqual(lowest_matching(parse_range("1.0.1"), known),
                         "1.1.0")
        self.assertEqual(lowest_matching(parse_range("1.1.0-a"), known),
                         "1.1.0-beta")
        self.assertIsNone(lowest_matching(parse_range("3.0"), known))


if __name__ == "__main__":
    unittest.main()
