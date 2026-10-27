"""Разбор и проверка параметров командной строки."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

MIN_DEPTH = 1
DEFAULT_DEPTH = 3
URL_SCHEMES = ("http", "https")
NUGET_ID_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")
TEST_ID_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}(-[0-9A-Za-z.\-]+)?(\+\S+)?$")


class ConfigError(Exception):
    """Ошибка в параметрах, заданных пользователем."""


@dataclass
class Config:
    """Параметры работы приложения, заданные пользователем."""

    package: str
    repo: str
    test_mode: bool
    version: str
    max_depth: int
    filter: str

    def as_pairs(self):
        """Вернуть параметры в виде списка пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("test_mode", self.test_mode),
            ("version", self.version),
            ("max_depth", self.max_depth),
            ("filter", self.filter),
        ]


def positive_int(text):
    """Преобразовать строку в целое число не меньше MIN_DEPTH."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"ожидалось целое число, получено '{text}'") from None
    if value < MIN_DEPTH:
        raise argparse.ArgumentTypeError(
            f"значение должно быть не меньше {MIN_DEPTH}, получено {value}")
    return value


class _Parser(argparse.ArgumentParser):
    """Парсер, сообщающий об ошибках исключением ConfigError."""

    def error(self, message):
        """Превратить ошибку argparse в ConfigError."""
        raise ConfigError(message)


def build_parser():
    """Создать парсер аргументов командной строки."""
    parser = _Parser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов NuGet.")
    parser.add_argument("-p", "--package", required=True,
                        help="имя анализируемого пакета")
    parser.add_argument("-r", "--repo", required=True,
                        help="URL репозитория NuGet или путь к файлу "
                             "тестового репозитория")
    parser.add_argument("-t", "--test-mode", action="store_true",
                        help="режим работы с тестовым репозиторием")
    parser.add_argument("-v", "--version", default="",
                        help="версия пакета (обязательна вне тестового "
                             "режима)")
    parser.add_argument("-d", "--max-depth", type=positive_int,
                        default=DEFAULT_DEPTH,
                        help="максимальная глубина анализа зависимостей "
                             f"(по умолчанию {DEFAULT_DEPTH})")
    parser.add_argument("-f", "--filter", default="",
                        help="подстрока: пакеты, содержащие её в имени, "
                             "не анализируются")
    return parser


def _check_package(config):
    """Проверить имя пакета с учётом режима работы."""
    if config.test_mode:
        if not TEST_ID_RE.match(config.package):
            raise ConfigError(
                "в тестовом режиме имя пакета состоит из больших "
                f"латинских букв: '{config.package}'")
    elif not NUGET_ID_RE.match(config.package):
        raise ConfigError(f"некорректное имя пакета: '{config.package}'")


def _check_repo(config):
    """Проверить URL репозитория или путь к тестовому файлу."""
    if config.test_mode:
        if not os.path.isfile(config.repo):
            raise ConfigError(
                f"файл тестового репозитория не найден: '{config.repo}'")
        return
    parts = urlparse(config.repo)
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        raise ConfigError(
            f"некорректный URL репозитория: '{config.repo}' "
            "(ожидается http:// или https://)")


def _check_version(config):
    """Проверить версию пакета."""
    if not config.version:
        if not config.test_mode:
            raise ConfigError("не задана версия пакета (--version)")
        return
    if not VERSION_RE.match(config.version):
        raise ConfigError(f"некорректная версия пакета: '{config.version}'")


def _check_filter(config):
    """Проверить подстроку фильтрации."""
    if config.filter != config.filter.strip():
        raise ConfigError("подстрока фильтра содержит пробелы по краям")
    if config.filter and config.filter.lower() in config.package.lower():
        raise ConfigError(
            f"фильтр '{config.filter}' исключает сам анализируемый пакет")


def validate(config):
    """Проверить согласованность параметров. Бросает ConfigError."""
    _check_package(config)
    _check_repo(config)
    _check_version(config)
    _check_filter(config)
    return config


def parse_args(argv):
    """Разобрать список аргументов и вернуть проверенный Config."""
    args = build_parser().parse_args(argv)
    config = Config(
        package=args.package.strip(),
        repo=args.repo.strip(),
        test_mode=args.test_mode,
        version=args.version.strip(),
        max_depth=args.max_depth,
        filter=args.filter,
    )
    return validate(config)
