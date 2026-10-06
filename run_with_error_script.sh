#!/bin/bash
# Проверка остановки стартового скрипта на первой ошибке (при подключённой VFS).
python3 src/main.py --vfs-path "vfs_examples/nested.csv" --script "scripts/startup_error.txt"
