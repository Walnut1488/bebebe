"""
Вспомогательный скрипт: генерирует тестовые CSV-файлы VFS в папку
vfs_examples/. Не часть самого эмулятора — запускается один раз вручную,
чтобы не писать base64-строки руками.

Запуск:
    python3 build_vfs_examples.py
"""

import base64
import csv
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "vfs_examples")


def b64(text_or_bytes) -> str:
    data = text_or_bytes.encode("utf-8") if isinstance(text_or_bytes, str) else text_or_bytes
    return base64.b64encode(data).decode("ascii")


def write_csv(filename: str, rows: list[tuple[str, str, str]]) -> None:
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "type", "content"])
        writer.writerows(rows)
    print(f"создан {path}")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Минимальная VFS: корень + один файл.
    write_csv("minimal.csv", [
        ("/hello.txt", "file", b64("Привет! Это минимальная VFS.")),
    ])

    # 2) Несколько файлов на одном уровне (без вложенности).
    write_csv("several_files.csv", [
        ("/a.txt", "file", b64("Файл A")),
        ("/b.txt", "file", b64("Файл B")),
        ("/c.txt", "file", b64("Файл C")),
    ])

    # 3) Вложенность минимум 3 уровня + пример двоичных данных (base64).
    fake_png_bytes = b"\x89PNG\r\n\x1a\n" + bytes(range(32))  # условные "двоичные" данные
    write_csv("nested.csv", [
        ("/docs", "dir", ""),
        ("/docs/readme.txt", "file", b64("Документация проекта")),
        ("/docs/images", "dir", ""),                       # уровень 2
        ("/docs/images/logo.png", "file", b64(fake_png_bytes)),  # уровень 3 (файл)
        ("/docs/images/icons", "dir", ""),                 # уровень 3 (папка)
        ("/docs/images/icons/star.png", "file", b64(fake_png_bytes)),  # уровень 4
    ])

    # 4) Специально сломанный файл — для демонстрации обработки ошибок:
    #    у файла указана несуществующая родительская папка "/missing".
    write_csv("broken.csv", [
        ("/missing/orphan.txt", "file", b64("У этого файла нет папки-родителя")),
    ])


if __name__ == "__main__":
    main()
