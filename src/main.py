"""
Эмулятор командной строки UNIX-подобной ОС.
Этап 4: основные команды.

К Этапу 3 (VFS) добавлено:
  - настоящая логика ls и cd (вместо заглушек с Этапа 1), работающая
    поверх дерева VFS, загруженного в память;
  - новые команды date (текущее время реальной ОС) и find (поиск по
    имени внутри VFS).

Вся логика самих команд вынесена в commands.py — здесь только REPL,
разбор параметров и загрузка VFS.
"""

import argparse
import sys

import commands
import vfs


def parse_input(line: str) -> tuple[str, list[str]]:
    """Разбить введённую строку на команду и список аргументов."""
    parts = line.strip().split()
    if not parts:
        return "", []
    command, *args = parts
    return command, args


COMMANDS = {
    "ls": commands.cmd_ls,
    "cd": commands.cmd_cd,
    "date": commands.cmd_date,
    "find": commands.cmd_find,
}


def execute_line(line: str, state: commands.ShellState) -> bool:
    """Выполнить одну строку ввода.

    Возвращает True, если строка выполнена без ошибки (или была пустой),
    и False при ошибке (неизвестная команда или ошибка самой команды) —
    это и есть "ошибка" для остановки стартового скрипта.
    """
    command, args = parse_input(line)

    if command == "":
        return True

    if command == "exit":
        sys.exit(0)

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"{command}: команда не найдена")
        return False

    return handler(args, state)


def run_script(path: str, prompt: str, state: commands.ShellState) -> None:
    """Прочитать стартовый скрипт и выполнить его команды по очереди.

    Каждая строка сначала печатается вместе с приглашением (имитация
    того, что её "ввёл" пользователь), затем выполняется и печатается
    результат. При первой ошибке выполнение скрипта останавливается.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"Не удалось открыть стартовый скрипт '{path}': {e}")
        return

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        print(f"{prompt}> {line}")          # имитация ввода пользователя
        ok = execute_line(line, state)       # выполнение + вывод результата
        if not ok:
            print("Стартовый скрипт остановлен из-за ошибки.")
            break


def run_repl(prompt: str, state: commands.ShellState) -> None:
    """Обычный интерактивный цикл REPL (как на Этапе 1)."""
    while True:
        try:
            line = input(f"{prompt}> ")
        except EOFError:
            print()
            break
        execute_line(line, state)


def parse_args() -> argparse.Namespace:
    """Разобрать параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор командной строки UNIX-подобной ОС"
    )
    parser.add_argument(
        "--vfs-path", dest="vfs_path", default=None,
        help="Путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--prompt", dest="prompt", default="myvfs",
        help="Пользовательское приглашение к вводу (по умолчанию: myvfs)",
    )
    parser.add_argument(
        "--script", dest="script", default=None,
        help="Путь к стартовому скрипту с командами эмулятора",
    )
    return parser.parse_args()


def print_debug_info(args: argparse.Namespace) -> None:
    """Отладочный вывод всех заданных параметров запуска (требование Этапа 2)."""
    print("=== Параметры запуска эмулятора ===")
    print(f"  Путь к VFS:        {args.vfs_path}")
    print(f"  Приглашение:       {args.prompt}")
    print(f"  Стартовый скрипт:  {args.script}")
    print("====================================")


def load_vfs_or_none(vfs_path: str) -> "vfs.VFSNode | None":
    """Загрузить VFS и показать отладочную информацию о результате.

    Если загрузка не удалась, печатает понятную ошибку и возвращает None —
    эмулятор продолжает работать дальше без VFS, а не падает.
    """
    try:
        root = vfs.load_vfs(vfs_path)
    except vfs.VFSError as e:
        print(f"Ошибка загрузки VFS: {e}")
        print("Эмулятор продолжит работу без VFS.")
        return None

    dirs, files = vfs.count_entries(root)
    print(f"VFS загружена успешно: {dirs} папок, {files} файлов")
    tree = vfs.render_tree(root)
    if tree:
        print("Структура VFS:")
        print(tree)
    return root


def main() -> None:
    args = parse_args()
    print_debug_info(args)

    state = commands.ShellState()
    if args.vfs_path:
        state.vfs_root = load_vfs_or_none(args.vfs_path)
        state.reset_cwd()

    if args.script:
        run_script(args.script, args.prompt, state)

    run_repl(args.prompt, state)


if __name__ == "__main__":
    main()
