#!/bin/bash
# Демонстрация всех команд Этапа 4 (ls, cd, date, find) поверх VFS,
# включая обработку ошибки (cd в несуществующую папку в конце скрипта).
python3 src/main.py --vfs-path vfs_examples/nested.csv --prompt student15 \
  --script scripts/stage4_startup.txt
