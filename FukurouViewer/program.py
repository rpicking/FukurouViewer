import os
import sys
import argparse
from enum import Enum
from threading import RLock

from PySide2.QtCore import Slot
from sqlalchemy import insert, select, update

from FukurouViewer.downloads import DownloadUIManager, DownloadsModel
from FukurouViewer.grid import GridModel, FilteredGridModel, SortType, GalleryGridModel
from . import user_database
from .blowupview import BlowUpItem
from .filetype import FileType
from .gallery import GalleryArchive
from .iconprovider import IconImageProvider
from .threads import ThreadManager
from .tray import SystemTrayIcon
from .utils import Utils
from .config import Config
from .logger import Logger
from .foundation import Foundation, FileItem
from .history import History
from .thumbnails import ThumbnailProvider

from PySide2 import QtCore, QtGui, QtQml, QtWidgets


class Program(QtWidgets.QApplication, Logger):
    GITHUB = "https://github.com/rpicking/FukurouViewer"
    BASE_PATH = Utils.base_path()
    QML_DIR = os.path.join(BASE_PATH, "qml")
    THUMB_DIR = Utils.fv_path("thumbs")
    FAVICON_DIR = Utils.fv_path("favicons")
    TMP_DIR = Utils.fv_path("tmp")  # 2nd definition in imageprovider need to find solution for only 1
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
        self.addLibraryPath(os.path.dirname(__file__))  # not sure
        super().__init__(args)
        self.setOrganizationName("FV")
        self.setApplicationName("FukurouViewer")
        self.setOrganizationDomain(self.GITHUB)
        self.version = "0.2.0"
        self.setQuitOnLastWindowClosed(False)

        # id = QtGui.QFontDatabase.addApplicationFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf"))
        # family = QtGui.QFontDatabase.applicationFontFamilies(id)[0]
        # font = QtGui.QFont(family)
        font = QtGui.QFont("Verdana")
        self.setFont(font)

        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(self.BASE_PATH, "icon.png"))))
        # self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))
        self.trayIcon = SystemTrayIcon(QtGui.QIcon(Utils.base_path("icon.ico")), self)

        self.iconImageProvider = IconImageProvider()
        self.thumb_image_provider = ThumbnailProvider()
        self.downloadsModel = DownloadsModel()
        self.downloadUIManager = DownloadUIManager()

        # blow up preview
        self.blowUpItem = BlowUpItem()
        # history manager
        self.history = History()

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Folders]).where(user_database.Folders.id == 1)))
            if results:
                results = results[0]

        aDirectory = results.get("path") if results else None

        # main filtered gridmodel
        self.mainFilteredGridModel = FilteredGridModel(aDirectory, SortType.DATE_MODIFIED)

        self.galleryGridModel = GalleryGridModel()

        self.threadManager = ThreadManager(self)

        self.engine = None
        self.context = None
        self.app_window = None

    def setup(self, args):
        if not os.path.exists(self.THUMB_DIR):
            os.makedirs(self.THUMB_DIR)
        if not os.path.exists(self.FAVICON_DIR):
            os.makedirs(self.FAVICON_DIR)
        if not os.path.exists(self.TMP_DIR):
            os.makedirs(self.TMP_DIR)
        user_database.setup()

        self.setDoubleClickInterval(300)
        self.trayIcon.show()

        # ARGUMENTS
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--downloader", help="start program in downloader mode", action="store_true")
        args = parser.parse_args()

        if not args.downloader:  # launching app (not host)
            self.start_application("MAIN")
        else:
            self.start_application()

        self.threadManager.startThreads()

    def start_application(self, mode="TRAY"):
        if self.engine is not None:
            return

        self.engine = QtQml.QQmlApplicationEngine()
        self.engine.addImportPath(self.QML_DIR)

        self.engine.addImageProvider("icon", self.iconImageProvider)
        self.engine.addImageProvider("thumbs", self.thumb_image_provider)

        self.context = self.engine.rootContext()
        self.setContextProperties()

        self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
        self.app_window = self.engine.rootObjects()[0]

        self.setupSignals()

        # self.open("APP")

        #  default mode? move to qml then have way of changing if not starting in default
        # self.app_window.setMode(mode)

        # with user_database.get_session(self, acquire=True) as session:
        #     results = session.query(user_database.History).filter(user_database.History.id == 183).first()
        #     test = results.gallery
        #     print("BREAK")

    def setContextProperties(self):
        """
            Sets the context properties for use within QML components
        """
        self.context.setContextProperty("application", self)
        self.context.setContextProperty("downloadsModel", self.downloadsModel)
        self.context.setContextProperty("downloadManager", self.downloadUIManager)
        self.context.setContextProperty("gridModel", self.mainFilteredGridModel)
        self.context.setContextProperty("galleryGridModel", self.galleryGridModel)
        self.context.setContextProperty("blowUp", self.blowUpItem)
        self.context.setContextProperty("history", self.history)

    def setupSignals(self):
        """
            Sets up the signal connections between QML app methods and Program python methods
        """
        self.app_window.requestFolders.connect(self.send_folders)
        self.app_window.createFavFolder.connect(self.add_folder)
        self.app_window.requestValidFolder.connect(self.set_folder_access)
        self.app_window.updateFolders.connect(self.update_folders)
        self.app_window.openItem.connect(Program.open_item)
        self.app_window.setEventFilter.connect(self.setEventFilter)
        self.app_window.closeApplication.connect(self.close)
        self.app_window.downloader_task.connect(self.downloader_task)

    @Slot(str, str, result="QVariant")
    def loadGallery(self, filepath, type: str) -> dict:

        if FileType.has_value(type):
            type = FileType(type)
        else:
            return {}

        if type is FileType.ARCHIVE:
            archiveGal = GalleryArchive(filepath)
            self.galleryGridModel.setGallery(archiveGal)

            return vars(archiveGal)


        return {}

    def setEventFilter(self, coords, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent):
        self.installEventFilter(self)
        self.blowUpItem.initItem(coords, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent)

    def closeBlowUpItem(self):
        self.app_window.closeBlowUpWindow()
        self.removeEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseMove:
            self.blowUpItem.movePosition(event.globalX(), event.globalY())
            return True
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.LeftButton:
                self.closeBlowUpItem()
            return True
        if event.type() == QtCore.QEvent.Wheel:  # zoom blowup on scroll wheel
            scrollAmount = event.angleDelta().y() / 120
            self.app_window.scrollBlowUp.emit(scrollAmount)
            return True
        return super().eventFilter(obj, event)

    @staticmethod
    def sorted_dir(folder):
        def getmtime(name):
            path = os.path.join(folder, name)
            return os.path.getmtime(path)

        return sorted(os.listdir(folder), key=getmtime)

    @staticmethod
    def open_item(path, type):
        """open history item file in default application or open file explorer to directory"""
        if type == "file":
            qurl = QtCore.QUrl.fromLocalFile(path)
        elif type == "folder":
            qurl = QtCore.QUrl.fromLocalFile(os.path.dirname(os.path.abspath(path)))
        elif type == "url":
            qurl = QtCore.QUrl(path)
        else:
            return
        QtGui.QDesktopServices.openUrl(qurl)

    @staticmethod
    def open_url(url):
        """open url in default browser"""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    # sends folders list to ui
    def send_folders(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Folders]).order_by(user_database.Folders.order)))
            self.app_window.receiveFolders.emit(results)

    # add new folder entry into database
    def add_folder(self, name, path, color, type):
        uid = Foundation.uniqueFolderID()
        order = Foundation.last_order()

        with user_database.get_session(self) as session:
            session.execute(insert(user_database.Folders).values(
                {
                    "name": name,
                    "uid": uid,
                    "path": path,
                    "color": color,
                    "order": order,
                    "type": type
                }))

            # updates ui indicator if folder path is accessable

    def set_folder_access(self, path: str):
        if os.path.exists(path):
            valid = os.access(path, os.R_OK | os.W_OK)
            self.app_window.receiveValidFolder.emit(valid)
        else:
            self.app_window.receiveValidFolder.emit(False)

    # update order of folders
    def update_folders(self, folders):
        folders = folders.toVariant()
        with user_database.get_session(self) as session:
            for folder in folders:
                session.execute(update(user_database.Folders).where(
                    user_database.Folders.id == folder.get("id")).values(
                    {
                        "order": folder.get("order")
                    }))

    def create_download_ui_item(self, item):
        """Creates download item in ui"""
        self.downloadsModel.addItem(item)
        self.downloadUIManager.add_download(item.id, item.total_size)

    def start_download_ui_item(self, id):
        """Start queued item in ui"""
        self.downloadsModel.start_item(id)
        self.downloadUIManager.start_download()

    def update_download_ui_item(self, kwargs):
        self.downloadsModel.updateItem(kwargs)
        self.downloadUIManager.update_progress(kwargs)

    def finish_download_ui_item(self, id, timestamp, total_size):
        self.downloadsModel.finish_item(id, timestamp)
        self.downloadUIManager.finish_download(id, total_size)
        self.history.add_new()

    def downloader_task(self, id, status):
        if status == "delete" or status == "done":
            self.downloadsModel.remove_item(id)
            self.downloadUIManager.remove_download(id, status)

    def open(self, mode="TRAY"):
        self.app_window.openWindow(mode, self.trayIcon.geometry().center())

    # close application window to tray or entirely
    def close(self):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            return

        type = Config.close
        if type == "tray":
            self.engine.clearComponentCache()
            self.app_window.closeWindows()
        elif type == "minimize":
            self.app_window.minimizeWindows()
        elif type == "quit":
            self.app_window.closeWindows()
            self.quit()
        else:
            self.logger.error("received invalid close parameter")
            self.quit()

    # quit application
    def quit(self):
        self.trayIcon.hide()
        super().quit()

    # single click on tray icon
    def singleClickActivated(self):
        if self.last == "Click":
            self.open()

    def exec_(self):
        return super().exec_()
