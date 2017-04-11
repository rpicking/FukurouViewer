import os
import sys
import time
from enum import Enum
from threading import RLock

from .utils import Utils
from .config import Config
from .search import Search

from PyQt5 import QtCore, QtGui, QtQml, QtWidgets


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)

        folder_options = Config.folder_options
        for folder in sorted(folder_options):
            uid = folder_options.get(folder).get("uid")
            item = FolderMenuItem(folder, self, uid)
            self.menu.addAction(item)

        self.exitAction = QtWidgets.QAction('&Exit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)


class FolderMenuItem(QtWidgets.QAction):

    def __init__(self, folder, parent, _uid):
        super().__init__(folder, parent)
        self.uid = _uid
        self.triggered.connect(self.openFolder)

    def openFolder(self):
        folder_options = Config.folder_options
        for folder in folder_options:
            if self.uid in folder_options.get(folder).values():
                dir = folder_options.get(folder).get("path")
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(Utils.norm_path(dir)))
                return


class Program(QtWidgets.QApplication):
    BASE_PATH = Utils.base_path()
    QML_DIR = os.path.join(BASE_PATH, "qml")
    THUMB_DIR = Utils.fv_path("thumbs")
    gallery_lock = RLock()

    class SortMethodMap(Enum):
        NameSort = "sort_name"
        ArtistSort = "sort_artist"
        ReadCountSort = "read_count"
        LastReadSort = "last_read"
        RatingSort = "sort_rating"
        DateAddedSort = "sort_date"
        TagSort = "sort_tag"

    def __init__(self, args):
        self.addLibraryPath(os.path.dirname(__file__))  #not sure
        super().__init__(args)
        self.setApplicationName("FukurouViewer")
        self.version = "0.2.0"
    
    def setup(self):
        if not os.path.exists(self.THUMB_DIR):
            os.makedirs(self.THUMB_DIR)        
        
        if True:    # temp for launching in host mode
            self.w = QtWidgets.QWidget()
            self.trayIcon = SystemTrayIcon(QtGui.QIcon(Utils.base_path("icon.ico")), self.w)
            self.trayIcon.show()
            self.trayIcon.exitAction.triggered.connect(self.quit)
        else:
            self.setFont(QtGui.QFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf")))
            self.engine = QtQml.QQmlApplicationEngine()
            self.engine.addImportPath(self.QML_DIR)
            #self.setAttribute(QtCore.Qt.AA_UseOpenGLES, True) gui non responsive with this in
            self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
            self.win = self.engine.rootObjects()[0]
            self.win.show()
            #------------
            #SIGNALS FROM UI GO HERE
            #------------

            self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))

            #load configs HERE
            #Search.search_ex_gallery()
            #time.sleep(5)
            #self.win.show()

    def quit(self):
        self.trayIcon.hide()
        super().quit()

    def exec_(self):
        return super().exec_()


