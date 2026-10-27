#!/usr/bin/env sh
# Запуск приложения и тестов.
#   ./run.sh [аргументы]   - запустить depviz
#   ./run.sh test          - запустить тесты
cd "$(dirname "$0")" || exit 1
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
if [ "$1" = "test" ]; then
    exec python3 -m unittest discover -s tests -v
fi
exec python3 -m depviz "$@"
