import unittest
from pathlib import Path

from FukurouViewer import Utils
from FukurouViewer.user_database import Folder


class FoldersTest(unittest.TestCase):
    def test_select_folder(self):
        uid = "BLAN5S"
        folder = Folder.get_by_id(uid)
        self.assertEqual(uid, folder.uid)

    def test_regular_path(self):
        path = "C:/Test/Directory"
        parsed_path = Folder.parse_path(path)
        self.assertEqual(Path(path), parsed_path)

    def test_relative_path(self):
        parsed_path = Folder.parse_path("../Directory")
        self.assertEqual(Path(Utils.base_path("../Directory")), parsed_path)

    def test_drive_relative_path(self):
        parsed_path = Folder.parse_path("?:/Test/Directory")
        self.assertEqual(Path("C:/Test/Directory"), parsed_path)


if __name__ == '__main__':
    unittest.main()
