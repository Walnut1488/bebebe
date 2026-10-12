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


def cmd_cp(args: list, state: ShellState) -> bool:
    """Скопировать файл или папку внутри VFS (целиком в памяти).

    Если конечный путь — существующая папка, копия кладётся внутрь неё
    под именем источника. Иначе конечный путь становится новым именем
    (существующий файл с таким именем будет перезаписан).
    """
    if state.vfs_root is None:
        print("cp: VFS не подключена")
        return False

    paths = [a for a in args if not a.startswith("-")]
    if len(paths) != 2:
        print("cp: требуется два аргумента — источник и назначение")
        return False
    src_path, dst_path = paths

    try:
        src_node = vfs.resolve(state.cwd_stack, src_path)[-1]
    except vfs.VFSError as e:
        print(f"cp: {src_path}: {e}")
        return False

    try:
        dst_parent, dst_name = _cp_destination(state, dst_path, src_node.name)
    except vfs.VFSError as e:
        print(f"cp: {dst_path}: {e}")
        return False

    if _is_inside(src_node, dst_parent):
        print(f"cp: нельзя скопировать '{src_path}' в самого себя")
        return False

    copy_node = _deep_copy(src_node)
    copy_node.name = dst_name
    dst_parent.children[dst_name] = copy_node
    return True


def _cp_destination(state: ShellState, dst_path: str, src_name: str) -> tuple:
    """Определить (родительская папка, имя) для места назначения cp."""
    try:
        dst_stack = vfs.resolve(state.cwd_stack, dst_path)
    except vfs.VFSError:
        parent_path, name = vfs.split_last_component(dst_path)
        parent_node = vfs.resolve(state.cwd_stack, parent_path)[-1]
        if not parent_node.is_dir:
            raise vfs.VFSError(f"'{parent_node.name}' не является директорией")
        if not name:
            raise vfs.VFSError("не указано имя файла назначения")
        return parent_node, name

    dst_node = dst_stack[-1]
    if dst_node.is_dir:
        return dst_node, src_name
    return dst_stack[-2], dst_node.name  # перезаписываем существующий файл


def _is_inside(ancestor, node) -> bool:
    """Проверить, является ли node самим ancestor или его потомком."""
    if node is ancestor:
        return True
    if not ancestor.is_dir:
        return False
    return any(_is_inside(child, node) for child in ancestor.children.values())


def _deep_copy(node):
    """Рекурсивно создать независимую копию узла VFS (для cp)."""
    if node.is_dir:
        copy = vfs.VFSNode(name=node.name, is_dir=True)
        for child_name, child in node.children.items():
            copy.children[child_name] = _deep_copy(child)
        return copy
    return vfs.VFSNode(
        name=node.name, is_dir=False, content=node.content, mtime=node.mtime
    )


def cmd_touch(args: list, state: ShellState) -> bool:
    """Создать пустой файл в VFS или обновить время изменения, если он есть."""
    if state.vfs_root is None:
        print("touch: VFS не подключена")
        return False

    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        print("touch: не указан путь к файлу")
        return False

    return all(_touch_one(state, path) for path in paths)


def _touch_one(state: ShellState, path: str) -> bool:
    """Выполнить touch для одного пути (создать файл или обновить mtime)."""
    try:
        node = vfs.resolve(state.cwd_stack, path)[-1]
    except vfs.VFSError:
        return _touch_create(state, path)

    if node.is_dir:
        print(f"touch: {path}: является директорией")
        return False
    node.mtime = datetime.now()
    return True


def _touch_create(state: ShellState, path: str) -> bool:
    """Создать новый пустой файл по несуществующему пути."""
    parent_path, name = vfs.split_last_component(path)
    try:
        parent_node = vfs.resolve(state.cwd_stack, parent_path)[-1]
    except vfs.VFSError as e:
        print(f"touch: {path}: {e}")
        return False

    if not parent_node.is_dir:
        print(f"touch: {path}: '{parent_node.name}' не является директорией")
        return False
    if not name:
        print(f"touch: {path}: не указано имя файла")
        return False

    parent_node.children[name] = vfs.VFSNode(
        name=name, is_dir=False, mtime=datetime.now()
    )
    return True
