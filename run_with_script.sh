#!/bin/bash
# Проверка параметров --vfs-path и --script вместе (сценарий без ошибок).
python3 src/main.py --vfs-path "vfs_examples/nested.csv" --prompt "student15" --script "scripts/startup_ok.txt"
