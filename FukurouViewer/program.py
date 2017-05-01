import os
import sys
import time
import argparse
from enum import Enum
from threading import RLock

from .utils import Utils
from .config import Config
from .search import Search

from PyQt5 import QtCore, QtGui, QtQml, QtWidgets


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    openSignal = QtCore.pyqtSignal()

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)
        self.activated.connect(self.click_trap)



        folder_options = Config.folder_options
        for folder in sorted(folder_options):
            uid = folder_options.get(folder).get("uid")
            item = FolderMenuItem(folder, self, uid)
            self.menu.addAction(item)

        self.openAction = QtWidgets.QAction('&Open', self)
        self.menu.addAction(self.openAction)

        self.closeAction = QtWidgets.QAction('&Close', self)
        self.menu.addAction(self.closeAction)

        self.exitAction = QtWidgets.QAction('&Exit', self)
        self.exitAction.setStatusTip('Exit application')
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)

    def click_trap(self, value):
        if value == self.Trigger:   # left click
            #self.menu.popup(QtGui.QCursor.pos())
            self.openSignal.emit()
            

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
    
        self.setQuitOnLastWindowClosed(False)

    def setup(self, args):
        if not os.path.exists(self.THUMB_DIR):
            os.makedirs(self.THUMB_DIR)        

        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--downloader", help="start program in downloader mode", action="store_true")
        args = parser.parse_args()

        self.setFont(QtGui.QFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf")))

        self.w = QtWidgets.QWidget()
        self.trayIcon = SystemTrayIcon(QtGui.QIcon(Utils.base_path("icon.ico")), self.w)
        self.trayIcon.show()
        self.trayIcon.exitAction.triggered.connect(self.quit)
        self.trayIcon.closeAction.triggered.connect(self.close)
        self.trayIcon.openAction.triggered.connect(self.open)
        self.trayIcon.openSignal.connect(self.signalCatch)
        
        if not args.downloader:    # launching app (not host)
            self.start_application()

        
        # APP SIGNALS

        # UI SIGNALS


        self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))


        #load configs HERE
        #Search.search_ex_gallery()
        #time.sleep(5)

    def start_application(self):
        self.engine = QtQml.QQmlApplicationEngine()
        self.engine.addImportPath(self.QML_DIR)
        #self.setAttribute(QtCore.Qt.AA_UseOpenGLES, True) gui non responsive with this in
        self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
        self.app_window = self.engine.rootObjects()[0]
        self.app_window.startMode("APP")

    # open application window
    def open(self):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            self.start_application()

        self.app_window.show()
        self.app_window.requestActivate()

    # close application window (don't quit app)
    def close(self):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            return
        self.engine.clearComponentCache()
        self.app_window.hide()

    # quit application
    def quit(self):
        self.trayIcon.hide()
        super().quit()

    def signalCatch(self):
        print("GOTCHA")

    def exec_(self):
        return super().exec_()


