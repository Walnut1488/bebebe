#!/bin/bash
# Проверка обработки ошибки: в этом CSV у файла нет родительской папки.
# Эмулятор должен напечатать понятную ошибку и продолжить работу без VFS.
python3 src/main.py --vfs-path vfs_examples/broken.csv --prompt student15
