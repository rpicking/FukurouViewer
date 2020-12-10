from unittest import TestCase

from FukurouViewer.config import Config
from FukurouViewer.setup import setup, erase


class DBTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        Config.appData = "../../testAppData"
        setup()

    @classmethod
    def tearDownClass(cls) -> None:
        erase()
