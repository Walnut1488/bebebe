"""
Команды эмулятора, работающие поверх VFS: ls, cd, date, find.

На Этапе 1-3 ls и cd были заглушками. Здесь у них появляется настоящая
логика навигации по дереву VFS, плюс две новые команды: date (просто
печатает текущее время реальной ОС) и find (поиск по имени внутри VFS).
"""

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime

import vfs


@dataclass
class ShellState:
    """Состояние REPL между командами: VFS и текущая директория в ней."""

    vfs_root: object = None
    cwd_stack: list = field(default_factory=list)

    def reset_cwd(self) -> None:
        """Поставить текущую директорию в корень загруженной VFS."""
        if self.vfs_root is not None:
            self.cwd_stack = [self.vfs_root]


def cmd_ls(args: list, state: ShellState) -> bool:
    """Показать содержимое директории VFS (текущей или указанной)."""
    if state.vfs_root is None:
        print("ls: VFS не подключена")
        return False

    path_args = [a for a in args if not a.startswith("-")]
    path = path_args[0] if path_args else "."

    try:
        stack = vfs.resolve(state.cwd_stack, path)
    except vfs.VFSError as e:
        print(f"ls: {path}: {e}")
        return False

    node = stack[-1]
    if not node.is_dir:
        print(node.name)
        return True

    for name in sorted(node.children):
        child = node.children[name]
        print(f"{name}/" if child.is_dir else name)
    return True


def cmd_cd(args: list, state: ShellState) -> bool:
    """Сменить текущую директорию в VFS (по умолчанию — в корень)."""
    if state.vfs_root is None:
        print("cd: VFS не подключена")
        return False

    path = args[0] if args else "/"

    try:
        stack = vfs.resolve(state.cwd_stack, path)
    except vfs.VFSError as e:
        print(f"cd: {path}: {e}")
        return False

    if not stack[-1].is_dir:
        print(f"cd: {path}: не является директорией")
        return False

    state.cwd_stack = stack
    return True


def cmd_date(args: list, state: ShellState) -> bool:
    """Показать текущую дату и время реальной ОС (от VFS не зависит)."""
    del args, state
    now = datetime.now()
    print(now.strftime("%a %b %d %H:%M:%S %Y"))
    return True


def cmd_find(args: list, state: ShellState) -> bool:
    """Найти в VFS файлы/папки по шаблону имени: find [путь] -name шаблон."""
    if state.vfs_root is None:
        print("find: VFS не подключена")
        return False

    path, pattern = _parse_find_args(args)

    try:
        stack = vfs.resolve(state.cwd_stack, path)
    except vfs.VFSError as e:
        print(f"find: {path}: {e}")
        return False

    start_node = stack[-1]
    start_path = vfs.stack_to_path(stack)
    matches = _collect_matches(start_node, pattern, start_path)
    for match in matches:
        print(match)
    return True


def _parse_find_args(args: list) -> tuple:
    """Разобрать аргументы find: необязательный путь и шаблон после -name."""
    path = "."
    pattern = "*"
    i = 0
    while i < len(args):
        if args[i] == "-name" and i + 1 < len(args):
            pattern = args[i + 1]
            i += 2
        else:
            path = args[i]
            i += 1
    return path, pattern


def _collect_matches(node, pattern: str, prefix: str) -> list:
    """Рекурсивно собрать пути узлов, чьё имя подходит под шаблон."""
    matches = []
    if fnmatch.fnmatch(node.name, pattern):
        matches.append(prefix)

    if node.is_dir:
        for child_name in sorted(node.children):
            child = node.children[child_name]
            child_prefix = f"{prefix.rstrip('/')}/{child_name}"
            matches.extend(_collect_matches(child, pattern, child_prefix))

    return matches
