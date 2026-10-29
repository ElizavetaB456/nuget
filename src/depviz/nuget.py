"""Получение зависимостей пакетов из репозитория NuGet (API v3).

Используются только стандартные HTTP-запросы и разбор XML/JSON:
  * индекс сервиса (index.json) -> ресурс PackageBaseAddress/3.0.0;
  * {base}/{id}/index.json      -> список версий пакета;
  * {base}/{id}/{ver}/{id}.nuspec -> манифест с зависимостями.
"""

import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree
from dataclasses import dataclass

from depviz import versions

TIMEOUT_SECONDS = 30
USER_AGENT = "depviz/1.0 (educational)"
BASE_ADDRESS_TYPE = "PackageBaseAddress/3.0.0"


class RepositoryError(Exception):
    """Ошибка получения данных из репозитория."""


@dataclass
class Dependency:
    """Прямая зависимость пакета."""

    name: str
    range_text: str
    version: str


def http_get(url):
    """Загрузить содержимое по URL и вернуть байты."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read()
    except urllib.error.HTTPError as error:
        raise RepositoryError(f"HTTP {error.code} для {url}") from None
    except (urllib.error.URLError, OSError) as error:
        raise RepositoryError(f"не удалось загрузить {url}: {error}") \
            from None


def _local_name(tag):
    """Имя XML-тега без пространства имён."""
    return tag.rsplit("}", 1)[-1]


def parse_nuspec(xml_text):
    """Извлечь зависимости из .nuspec: список пар (id, диапазон).

    Если зависимости разбиты на группы по целевым платформам,
    берётся объединение групп (первое вхождение id).
    """
    try:
        root = etree.fromstring(xml_text)
    except etree.ParseError as error:
        raise RepositoryError(f"некорректный .nuspec: {error}") from None
    result, seen = [], set()
    for node in root.iter():
        if _local_name(node.tag) != "dependency":
            continue
        dep_id = node.get("id", "").strip()
        if dep_id and dep_id.lower() not in seen:
            seen.add(dep_id.lower())
            result.append((dep_id, node.get("version", "")))
    return result


class NuGetSource:
    """Источник зависимостей — репозиторий NuGet по URL."""

    def __init__(self, url, fetch=http_get):
        """Запомнить URL репозитория и функцию загрузки."""
        self.url = url
        self.fetch = fetch
        self._base = None
        self._versions = {}

    def _json(self, url):
        """Загрузить и разобрать JSON."""
        try:
            return json.loads(self.fetch(url))
        except ValueError:
            raise RepositoryError(f"некорректный JSON: {url}") from None

    def base_address(self):
        """Адрес PackageBaseAddress (flat container)."""
        if self._base is None:
            self._base = self._resolve_base()
        return self._base

    def _resolve_base(self):
        """Найти PackageBaseAddress в индексе сервиса."""
        if not self.url.endswith(".json"):
            return self.url.rstrip("/") + "/"
        for res in self._json(self.url).get("resources", []):
            if res.get("@type") == BASE_ADDRESS_TYPE:
                return res["@id"].rstrip("/") + "/"
        raise RepositoryError(f"в {self.url} нет ресурса {BASE_ADDRESS_TYPE}")

    def list_versions(self, name):
        """Список опубликованных версий пакета."""
        key = name.lower()
        if key not in self._versions:
            url = f"{self.base_address()}{key}/index.json"
            self._versions[key] = self._json(url).get("versions", [])
        return self._versions[key]

    def resolve_version(self, name, range_text):
        """Выбрать версию пакета по диапазону (минимальная подходящая)."""
        try:
            version_range = versions.parse_range(range_text)
        except versions.VersionError as error:
            raise RepositoryError(f"{name}: {error}") from None
        found = versions.lowest_matching(version_range,
                                         self.list_versions(name))
        if found is None:
            raise RepositoryError(
                f"нет версии {name}, подходящей под '{range_text}'")
        return found

    def check_version(self, name, version):
        """Проверить, что версия пакета существует; вернуть её."""
        wanted = versions.normalize(version)
        for known in self.list_versions(name):
            if versions.normalize(known) == wanted:
                return known
        raise RepositoryError(f"версия {version} пакета {name} не найдена")

    def direct_dependencies(self, name, version):
        """Прямые зависимости пакета заданной версии."""
        key, ver = name.lower(), versions.normalize(version).lower()
        url = f"{self.base_address()}{key}/{ver}/{key}.nuspec"
        return [
            Dependency(dep, rng, self.resolve_version(dep, rng))
            for dep, rng in parse_nuspec(self.fetch(url))
        ]
