#!/bin/bash
# Единая точка запуска эмулятора (требование С5 — наличие run.sh).
# Пример: ./run.sh --vfs-path vfs_examples/nested.csv --prompt student15
python3 src/main.py "$@"
