"""Поддельный репозиторий NuGet для тестов без сети."""

import json

from depviz.nuget import RepositoryError

INDEX_URL = "https://nuget.test/v3/index.json"
BASE = "https://nuget.test/flat/"

NUSPEC = """<?xml version="1.0"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>{name}</id>
    <dependencies>{deps}</dependencies>
  </metadata>
</package>"""


def make_nuspec(name, deps):
    """Сформировать .nuspec с одной группой зависимостей."""
    items = "".join(
        f'<dependency id="{dep}" version="{rng}" />' for dep, rng in deps)
    return NUSPEC.format(name=name, deps=f"<group>{items}</group>")


class FakeRepo:
    """Хранит пакеты и отвечает на запросы как сервер NuGet."""

    def __init__(self, packages):
        """packages: {(id, версия): [(зависимость, диапазон), ...]}."""
        self.packages = packages
        self.requests = []

    def _versions(self, key):
        """Все версии пакета с заданным id в нижнем регистре."""
        return [ver for (name, ver) in self.packages if name.lower() == key]

    def _nuspec(self, key, version):
        """Вернуть .nuspec пакета или бросить ошибку 404."""
        for (name, ver), deps in self.packages.items():
            if name.lower() == key and ver == version:
                return make_nuspec(name, deps).encode()
        raise RepositoryError("HTTP 404")

    def __call__(self, url):
        """Ответить на HTTP-запрос по URL."""
        self.requests.append(url)
        if url == INDEX_URL:
            resources = [{"@id": BASE,
                          "@type": "PackageBaseAddress/3.0.0"}]
            return json.dumps({"resources": resources}).encode()
        parts = url[len(BASE):].split("/")
        if parts[-1] == "index.json":
            return json.dumps({"versions": self._versions(parts[0])}).encode()
        return self._nuspec(parts[0], parts[1])
