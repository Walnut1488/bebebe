#!/bin/bash
# Проверка работы с VFS, где папки и файлы вложены минимум на 3 уровня,
# и есть файл с "двоичным" содержимым (base64).
python3 src/main.py --vfs-path vfs_examples/nested.csv --prompt student15
