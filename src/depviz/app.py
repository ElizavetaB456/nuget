"""Основной сценарий работы приложения."""

import sys

from depviz.cli import ConfigError, parse_args

EXIT_OK = 0
EXIT_CONFIG_ERROR = 2


def print_config(config):
    """Вывести параметры в формате ключ-значение."""
    for key, value in config.as_pairs():
        print(f"{key}={value}")


def main(argv):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"Ошибка параметров: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    print_config(config)
    return EXIT_OK
