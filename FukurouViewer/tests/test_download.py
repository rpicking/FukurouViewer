import unittest

from FukurouViewer.threads import ThreadManager


class DownloadTest(unittest.TestCase):

    def __init__(self):
        super().__init__()
        self.threadManager = ThreadManager()

    def test_file_download(self):
        self.assertEqual(True, False)

    def test_manga_download(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
