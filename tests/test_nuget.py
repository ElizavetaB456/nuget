"""Тесты получения зависимостей из NuGet (без сети)."""

import unittest

from depviz.nuget import NuGetSource, RepositoryError, parse_nuspec
from fake_nuget import BASE, INDEX_URL, FakeRepo

NS = "http://schemas.microsoft.com/packaging/2011/08/nuspec.xsd"
MULTI_GROUP = f"""<package xmlns="{NS}">
<metadata><dependencies>
<group targetFramework=".NETFramework4.6.2">
  <dependency id="A.Core" version="1.0.0" />
</group>
<group targetFramework=".NETStandard2.0">
  <dependency id="a.core" version="1.0.0" />
  <dependency id="B" version="[2.0,3.0)" exclude="Build" />
</group>
</dependencies></metadata></package>"""


class NuGetTest(unittest.TestCase):
    """Разбор .nuspec и обращение к API v3."""

    def setUp(self):
        """Подготовить поддельный репозиторий."""
        self.fake = FakeRepo({
            ("Root", "1.0.0"): [("Lib", "[1.0.0, )"), ("Util", "2.0")],
            ("Lib", "0.9.0"): [],
            ("Lib", "1.0.0"): [],
            ("Lib", "1.5.0"): [],
            ("Util", "2.1.0"): [],
        })
        self.source = NuGetSource(INDEX_URL, fetch=self.fake)

    def test_parse_groups(self):
        """Группы объединяются, дубликаты id убираются."""
        self.assertEqual(parse_nuspec(MULTI_GROUP),
                         [("A.Core", "1.0.0"), ("B", "[2.0,3.0)")])

    def test_service_index(self):
        """Адрес flat container берётся из индекса сервиса."""
        self.assertEqual(self.source.base_address(), BASE)

    def test_direct(self):
        """Версии зависимостей — минимальные подходящие."""
        deps = self.source.direct_dependencies("Root", "1.0")
        got = [(dep.name, dep.version) for dep in deps]
        self.assertEqual(got, [("Lib", "1.0.0"), ("Util", "2.1.0")])

    def test_missing_version(self):
        """Несуществующая версия — ошибка."""
        with self.assertRaises(RepositoryError):
            self.source.check_version("Root", "9.9.9")

    def test_bad_xml(self):
        """Некорректный XML — ошибка репозитория."""
        with self.assertRaises(RepositoryError):
            parse_nuspec("<package>")


if __name__ == "__main__":
    unittest.main()
