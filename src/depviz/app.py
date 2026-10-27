"""Основной сценарий работы приложения."""

import sys

from depviz.cli import ConfigError, parse_args
from depviz.nuget import NuGetSource, RepositoryError

EXIT_OK = 0
EXIT_REPO_ERROR = 1
EXIT_CONFIG_ERROR = 2


def print_direct(config, source):
    """Вывести прямые зависимости заданного пакета."""
    version = source.check_version(config.package, config.version)
    deps = source.direct_dependencies(config.package, version)
    print(f"Прямые зависимости {config.package} {version}:")
    if not deps:
        print("  (нет)")
    for dep in deps:
        print(f"  {dep.name} {dep.range_text or '*'} -> {dep.version}")


def main(argv):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"Ошибка параметров: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if config.test_mode:
        print("Тестовый режим будет поддержан на этапе 3.")
        return EXIT_OK
    try:
        print_direct(config, NuGetSource(config.repo))
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_REPO_ERROR
    return EXIT_OK
