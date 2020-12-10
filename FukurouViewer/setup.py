import os
import shutil

from FukurouViewer.config import Config
from FukurouViewer.user_database import upgrade


def setup():
    if not os.path.exists(Config.appData):
        os.mkdir(Config.appData)

    upgrade()


def erase():
    if os.path.exists(Config.appData):
        shutil.rmtree(Config.appData)
