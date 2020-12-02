import os

from PySide2 import QtQuick, QtWidgets, QtCore
from sqlalchemy import select

from FukurouViewer import Utils, user_database
from .config import Config


class IconImageProvider(QtQuick.QQuickImageProvider):
    """image provider for default file icons i.e. icon of default program that runs file"""
    TMP_DIR = Config.fv_path("tmp")

    def __init__(self):
        QtQuick.QQuickImageProvider.__init__(self, QtQuick.QQuickImageProvider.Pixmap)

    def requestPixmap(self, id, size, requestedSize):
        width = requestedSize.width()
        height = requestedSize.height()
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).where(user_database.History.id == id)))[0]

        path = results.get("filepath")
        if not os.path.exists(path):
            _, ext = os.path.splitext(path)
            tmpfile = os.path.join(IconImageProvider.TMP_DIR, "tmpfile" + ext)
            open(tmpfile, 'a').close()
            path = tmpfile

        icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(path))
        pixmap = icon.pixmap(icon.availableSizes()[-2])  # largest size screws up and makes small icon
        pixmap = pixmap.scaled(width, height, mode=QtCore.Qt.SmoothTransformation)
        return pixmap
