import os
import sys
import time
import argparse
from enum import Enum
from threading import RLock
from sqlalchemy import select

from . import user_database
from .utils import Utils
from .config import Config

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

        self.openAction = QtWidgets.QAction('&Open', self)
        self.menu.addAction(self.openAction)

        self.closeAction = QtWidgets.QAction('&Close', self)
        self.menu.addAction(self.closeAction)

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
    FAVICON_DIR = Utils.fv_path("favicons")
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
        if not os.path.exists(self.FAVICON_DIR):
            os.makedirs(self.FAVICON_DIR)
        user_database.setup()     

        self.setFont(QtGui.QFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf")))

        # HANDLING OF TRAY ICON
        self.w = QtWidgets.QWidget()
        self.trayIcon = SystemTrayIcon(QtGui.QIcon(Utils.base_path("icon.ico")), self.w)
        self.trayIcon.show()
        self.trayIcon.exitAction.triggered.connect(self.quit)
        self.trayIcon.closeAction.triggered.connect(self.close)
        self.trayIcon.openAction.triggered.connect(self.open)
        # timer for differentiating double click from single click
        self.clickTimer = QtCore.QTimer(self)
        self.clickTimer.setSingleShot(True)
        self.clickTimer.timeout.connect(self.singleClickActivated)

        self.trayIcon.activated.connect(self.onTrayIconActivated)

        # ARGUMENTS
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--downloader", help="start program in downloader mode", action="store_true")
        args = parser.parse_args()

        if not args.downloader:    # launching app (not host)
            self.start_application()

        self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))
 
        #load configs HERE

    
    def start_application(self):
        self.engine = QtQml.QQmlApplicationEngine()
        self.engine.addImportPath(self.QML_DIR)
        #self.setAttribute(QtCore.Qt.AA_UseOpenGLES, True) gui non responsive with this in
        self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
        self.app_window = self.engine.rootObjects()[0]

        # SIGNALS
        self.app_window.requestHistory.connect(self.send_history)
        self.app_window.setMode("MINI") #, self.trayIcon.geometry().center())



    def send_history(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).order_by(user_database.History.time_added.desc()).limit(5)))

        self.app_window.receiveHistory.emit(results)

    # open application window
    def open(self):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            self.start_application()

        self.app_window.openWindow(self.trayIcon.geometry().center())
        #self.app_window.show()
        self.app_window.requestActivate()


    # close application window (don't quit app)
    def close(self):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            return
        self.engine.clearComponentCache()
        self.app_window.closeWindows()


    # quit application
    def quit(self):
        self.trayIcon.hide()
        super().quit()

    def onTrayIconActivated(self, event):
        #print("GOTCHA ", event)
        if event == QtWidgets.QSystemTrayIcon.Trigger:
            self.clickTimer.start(self.doubleClickInterval())
        elif event == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.open()

    # single click on tray icon
    def singleClickActivated(self):
        print("ONE FOR ALL")


    def exec_(self):
        return super().exec_()


