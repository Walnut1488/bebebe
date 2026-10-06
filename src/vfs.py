"""
Загрузка виртуальной файловой системы (VFS) из CSV-файла в память.

Формат CSV (с заголовком в первой строке):

    path,type,content

    path    — абсолютный путь элемента внутри VFS, например "/docs/notes.txt".
              Строка с путём "/" (сам корень) не обязательна и игнорируется.
    type    — "dir" для папки или "file" для файла.
    content — для файлов: содержимое, закодированное в base64
              (используется именно для двоичных данных, но подходит и для
              текста); для папок — пустая строка.

Все родительские папки элемента должны быть описаны в CSV раньше, чем сам
элемент (то есть сначала "/docs", потом "/docs/notes.txt").

Важно: вся VFS хранится только в памяти в виде дерева объектов VFSNode.
Исходный CSV-файл НИКОГДА не изменяется и не распаковывается на диск.
"""

import base64
import csv
from dataclasses import dataclass, field


class VFSError(Exception):
    """Ошибка при загрузке или разборе VFS."""


@dataclass
class VFSNode:
    name: str
    is_dir: bool
    content: bytes = b""                            # только для файлов
    children: dict = field(default_factory=dict)     # только для папок: имя -> VFSNode


def _split_path(path: str) -> list[str]:
    """Разбить абсолютный путь на составляющие, отбросив пустые части."""
    return [part for part in path.strip("/").split("/") if part]


def load_vfs(csv_path: str) -> VFSNode:
    """Загрузить VFS из CSV-файла и вернуть корневой узел дерева.

    Бросает VFSError, если:
      - файл не найден или не читается;
      - у CSV неверный заголовок;
      - встречена строка с неизвестным типом, битым base64, путём без
        существующего родителя или с повторяющимся путём.
    """
    root = VFSNode(name="/", is_dir=True)

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = ["path", "type", "content"]
            if reader.fieldnames != expected:
                raise VFSError(
                    f"неверный заголовок CSV: {reader.fieldnames}, "
                    f"ожидалось {expected}"
                )
            for row_num, row in enumerate(reader, start=2):
                _add_entry(root, row, row_num)
    except FileNotFoundError:
        raise VFSError(f"файл VFS не найден: {csv_path}")
    except csv.Error as e:
        raise VFSError(f"ошибка чтения CSV: {e}")

    return root


def _add_entry(root: VFSNode, row: dict, row_num: int) -> None:
    path = (row.get("path") or "").strip()
    entry_type = (row.get("type") or "").strip()
    content_b64 = row.get("content") or ""

    if path in ("", "/"):
        # Строка описывает сам корень — он уже создан, пропускаем.
        return

    if entry_type not in ("dir", "file"):
        raise VFSError(
            f"строка {row_num}: неизвестный тип '{entry_type}' "
            f"(ожидалось 'dir' или 'file')"
        )

    parts = _split_path(path)
    if not parts:
        raise VFSError(f"строка {row_num}: пустой путь")

    *parent_parts, name = parts
    current = root
    walked: list[str] = []
    for part in parent_parts:
        walked.append(part)
        child = current.children.get(part)
        if child is None:
            raise VFSError(
                f"строка {row_num}: папка '/{'/'.join(walked)}' не найдена — "
                f"родитель для '{path}' должен быть описан раньше в файле"
            )
        if not child.is_dir:
            raise VFSError(
                f"строка {row_num}: '/{'/'.join(walked)}' это файл, а не папка"
            )
        current = child

    if name in current.children:
        raise VFSError(f"строка {row_num}: путь '{path}' определён повторно")

    if entry_type == "dir":
        current.children[name] = VFSNode(name=name, is_dir=True)
    else:
        try:
            content = base64.b64decode(content_b64, validate=True)
        except Exception as e:
            raise VFSError(
                f"строка {row_num}: не удалось декодировать base64 "
                f"для файла '{path}': {e}"
            )
        current.children[name] = VFSNode(name=name, is_dir=False, content=content)


def count_entries(node: VFSNode) -> tuple[int, int]:
    """Посчитать количество папок и файлов в дереве (не считая сам корень)."""
    dirs = files = 0
    for child in node.children.values():
        if child.is_dir:
            dirs += 1
            d, f = count_entries(child)
            dirs += d
            files += f
        else:
            files += 1
    return dirs, files


def render_tree(node: VFSNode, prefix: str = "") -> str:
    """Построить текстовое дерево VFS (для отладочного вывода)."""
    lines = []
    items = sorted(node.children.items())
    for i, (name, child) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        suffix = "/" if child.is_dir else f" ({len(child.content)} байт)"
        lines.append(f"{prefix}{connector}{name}{suffix}")
        if child.is_dir:
            extension = "    " if is_last else "│   "
            subtree = render_tree(child, prefix + extension)
            if subtree:
                lines.append(subtree)
    return "\n".join(lines)
