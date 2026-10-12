#!/bin/bash
# Демонстрация команд Этапа 5 (cp, touch) поверх VFS, включая обработку
# ошибки (cp несуществующего файла в конце скрипта).
python3 src/main.py --vfs-path vfs_examples/nested.csv --prompt student15 \
  --script scripts/stage5_startup.txt
