"""Модульные тесты для src/vfs.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import vfs  # noqa: E402  (импорт после правки sys.path — так и должно быть)

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "vfs_examples")


class TestLoadVfs(unittest.TestCase):
    """Проверка загрузки разных вариантов VFS из CSV."""

    def test_minimal_vfs_has_one_file(self):
        root = vfs.load_vfs(os.path.join(EXAMPLES_DIR, "minimal.csv"))
        dirs, files = vfs.count_entries(root)
        self.assertEqual(dirs, 0)
        self.assertEqual(files, 1)

    def test_several_files_vfs(self):
        root = vfs.load_vfs(os.path.join(EXAMPLES_DIR, "several_files.csv"))
        dirs, files = vfs.count_entries(root)
        self.assertEqual(dirs, 0)
        self.assertEqual(files, 3)

    def test_nested_vfs_structure(self):
        root = vfs.load_vfs(os.path.join(EXAMPLES_DIR, "nested.csv"))
        dirs, files = vfs.count_entries(root)
        self.assertEqual(dirs, 3)
        self.assertEqual(files, 3)

    def test_broken_vfs_raises_vfs_error(self):
        with self.assertRaises(vfs.VFSError):
            vfs.load_vfs(os.path.join(EXAMPLES_DIR, "broken.csv"))

    def test_missing_file_raises_vfs_error(self):
        with self.assertRaises(vfs.VFSError):
            vfs.load_vfs(os.path.join(EXAMPLES_DIR, "does_not_exist.csv"))


if __name__ == "__main__":
    unittest.main()
