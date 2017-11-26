import os
import sys
import time
import argparse
from enum import Enum
from threading import RLock
from sqlalchemy import delete, insert, select, update

from . import user_database
from .utils import Utils
from .config import Config
from .foundation import Foundation

from PyQt5 import QtCore, QtGui, QtQml, QtQuick, QtWidgets


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)
        self.createMenu()

    def createMenu(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Folders]).order_by(user_database.Folders.order)))

        for folder in results:
            name = folder.get("name")
            uid = folder.get("uid")
            path = folder.get("path")
            item = FolderMenuItem(self, name, path, uid)
            self.menu.addAction(item)

        self.exitAction = QtWidgets.QAction('&Exit', self)
        self.exitAction.setStatusTip('Exit application')
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)
           

class FolderMenuItem(QtWidgets.QAction):


    def __init__(self, parent, _name, _path, _uid):
        super().__init__(_name, parent)
        self.name = _name
        self.uid = _uid
        self.path = _path
        self.triggered.connect(self.openFolder)

    def openFolder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(Utils.norm_path(self.path)))
        return


class Download(object):
    def __init__(self, _id, _filename, _total_size, _color):
        self.id = _id
        self.filename = _filename
        self.total_size = _total_size
        self.color = _color
        self.cur_size = 0
        self.percent = 0
        self.speed = 0

    def getID(self):
        return self.id

    def getFilename(self):
        return self.filename

    def getTotalSize(self):
        return self.total_size
    
    def getColor(self):
        return self.color

    def getCurSize(self):
        return self.cur_size

    def getPercent(self):
        return self.percent

    def getSpeed(self):
        return self.speed

    def update(self, _cur_size, _percent, _speed):
        self.cur_size = _cur_size
        self.percent = _percent
        self.speed = _speed


class DownloadsModel(QtCore.QAbstractListModel):
    IDRole = QtCore.Qt.UserRole + 1
    FilenameRole = QtCore.Qt.UserRole + 2
    TotalSizeRole = QtCore.Qt.UserRole + 3
    ColorRole = QtCore.Qt.UserRole + 4
    CurSizeRole = QtCore.Qt.UserRole + 5
    PercentRole = QtCore.Qt.UserRole + 6
    SpeedRole = QtCore.Qt.UserRole + 7

    _roles = {IDRole: "id", FilenameRole: "filename", TotalSizeRole: "total_size", ColorRole: "color",
              CurSizeRole: "cur_size", PercentRole: "percent", SpeedRole: "speed"}

    def __init__(self, parent=None):
        super(DownloadsModel, self).__init__(parent)
        self._items = []

    def addItem(self, id, filename, total_size, color):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        self._items.append(Download(id, filename, total_size, color))
        self.endInsertRows()
        
        #self.do_update()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        try:
            item = self._items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role == self.IDRole:
            return item.getID()
        if role == self.FilenameRole:
            return item.getFilename()
        if role == self.TotalSizeRole:
            return item.getTotalSize()
        if role == self.ColorRole:
            return item.getColor()
        if role == self.CurSizeRole:
            return item.getCurSize()
        if role == self.PercentRole:
            return item.getPercent()
        if role == self.SpeedRole:
            return item.getSpeed()

        return QtCore.QVariant()

    def roleNames(self):
        return {x: self._roles[x].encode() for x in self._roles}

    # get list of ids from items
    def getIDs(self):
        return [item.getID() for item in self._items]

    # creates new unique id for download item in UI
    def createID(self):
        used_ids = self.getIDs()
        return Foundation.uniqueID(used_ids)

    # THIS MIGHT NEED TO BE SWITCHED TO SETDATA  https://stackoverflow.com/questions/20784500/qt-setdata-method-in-a-qabstractitemmodel
    # updates filename and color of current download item with id
    def updateItem(self, id, cur_size, progress, speed):
        for index, item in enumerate(self._items):
            if item.getID() == id:
                break
        else:   # id doesn't exist
            return

        self._items[index].update(cur_size, progress, speed)

        #self.do_update()

        model_index = self.index(index)
        self.dataChanged.emit(model_index, model_index, [])

    def do_update(self):
        start_index = self.createIndex(0,0)
        end_index = self.createIndex(len(self._items) - 1, 0)
        self.dataChanged.emit(start_index, end_index, [])
        

class ImageProvider(QtQuick.QQuickImageProvider):
    TMP_DIR = Utils.fv_path("tmp")

    def __init__(self):
        QtQuick.QQuickImageProvider.__init__(self, QtQuick.QQuickImageProvider.Pixmap)

    def requestImage(self, id, requestedSize):
        width = requestedSize.width()
        height = requestedSize.height()
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).where( user_database.History.id == id)))

        path = results[0].get("full_path")
        if not os.path.exists(path):
            _, ext = os.path.splitext(path)
            tmpfile = os.path.join(Program.TMP_DIR, "tmpfile" + ext)
            path = tmpfile

        #wat = QtCore.QFileInfo(path)
        icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(path))
        pixmap = icon.pixmap(icon.availableSizes()[-1]) # make pixmap out of largest icon size

        #if tmpfile:
        grayimage = pixmap.toImage().convertToFormat(QtGui.QImage.Format_Mono)
        return grayimage, requestedSize

    def requestPixmap(self, id, requestedSize):
        width = requestedSize.width()
        height = requestedSize.height()
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).where( user_database.History.id == id)))

        path = results[0].get("full_path")
        if not os.path.exists(path):
            _, ext = os.path.splitext(path)
            tmpfile = os.path.join(Program.TMP_DIR, "tmpfile" + ext)
            open(tmpfile, 'a').close()
            path = tmpfile

        icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(path))
        pixmap = icon.pixmap(icon.availableSizes()[-2])  # largest size screws up and makes small icon
        pixmap = pixmap.scaled(width, height, transformMode=QtCore.Qt.SmoothTransformation)
        return pixmap, requestedSize


class Program(QtWidgets.QApplication):
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
        self.addLibraryPath(os.path.dirname(__file__))  #not sure
        super().__init__(args)
        self.setApplicationName("FukurouViewer")
        self.version = "0.2.0"
    
        self.setQuitOnLastWindowClosed(False)
        self.setFont(QtGui.QFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf")))
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))


    def setup(self, args):
        if not os.path.exists(self.THUMB_DIR):
            os.makedirs(self.THUMB_DIR)
        if not os.path.exists(self.FAVICON_DIR):
            os.makedirs(self.FAVICON_DIR)
        if not os.path.exists(self.TMP_DIR):
            os.makedirs(self.TMP_DIR)
        user_database.setup()     

        # HANDLING OF TRAY ICON
        self.w = QtWidgets.QWidget()
        self.trayIcon = SystemTrayIcon(QtGui.QIcon(Utils.base_path("icon.ico")), self.w)
        self.trayIcon.show()
        self.trayIcon.exitAction.triggered.connect(self.quit)
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
            self.start_application("MAIN")
        else:
            self.start_application()

    
    def start_application(self, mode="MINI"):
        try:
            self.engine
        except AttributeError:  # qml engine not started
            self.engine = QtQml.QQmlApplicationEngine()
            self.engine.addImportPath(self.QML_DIR)
            #self.setAttribute(QtCore.Qt.AA_UseOpenGLES, True) gui non responsive with this in
            self.image_provider = ImageProvider()
            self.engine.addImageProvider("fukurou", self.image_provider)

            self.downloadsModel = DownloadsModel()
            #self.create_download_item("XXXXX", "test1.pdf", 1000, "red")
            #self.create_download_item("SSSSS", "test2.pdf", 1000, "blue")

            self.context = self.engine.rootContext()
            self.context.setContextProperty("downloadsModel", self.downloadsModel)

            self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
            self.app_window = self.engine.rootObjects()[0]

            # SIGNALS
            self.app_window.requestHistory.connect(self.send_history)
            self.app_window.requestFolders.connect(self.send_folders)
            self.app_window.createFavFolder.connect(self.add_folder)
            self.app_window.requestValidFolder.connect(self.set_folder_access)
            self.app_window.deleteHistoryItem.connect(self.delete_history_item)
            self.app_window.updateFolders.connect(self.update_folders)
            self.app_window.openItem.connect(self.open_item)

            self.app_window.setMode(mode) # default mode? move to qml then have way of changing if not starting in default

            #self.create_download_item("AAAAA", "test3.pdf", 1000, "green")
            #self.create_download_item("BBBBB", "test4.pdf", 1000, "purple")

            #with user_database.get_session(self, acquire=True) as session:
             #   results = session.query(user_database.History).filter(user_database.History.id == 183).first()
              #  test = results.gallery
               # print("BREAK")

    # sends limit number of history entries newest first to ui
    def send_history(self, limit=0):
        self.history_health_check()
        with user_database.get_session(self, acquire=True) as session:
            if not limit:
                results = Utils.convert_result(session.execute(
                    select([user_database.History]).order_by(user_database.History.time_added.desc())))
            else:
                results = Utils.convert_result(session.execute(
                    select([user_database.History]).order_by(user_database.History.time_added.desc()).limit(limit)))
            self.app_window.receiveHistory.emit(results)


    # checks health of files in history table changing to dead if no longer exists
    def history_health_check(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).order_by(user_database.History.time_added.desc())))

            for item in results:
                if not os.path.exists(item.get("full_path")):
                    session.execute(update(user_database.History).where(
                        user_database.History.id == item.get("id")).values(
                        { "dead": True }))


    # delete history item
    def delete_history_item(self, id):
        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.History).where(user_database.History.id == id))
        self.send_history()


    # open history item file in default application or open file explorer to directory
    def open_item(self, path, type):
        if type == "file":
            qurl = QtCore.QUrl.fromLocalFile(path)
            #QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        elif type == "folder":
            qurl = QtCore.QUrl.fromLocalFile(os.path.dirname(os.path.abspath(path)))
            #QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        elif type == "url":
            qurl = QtCore.QUrl(path)
            #QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        QtGui.QDesktopServices.openUrl(qurl)


    # open url in default browser
    def open_url(self, url):
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
        order = Foundation.lastOrder()

        # testing stuff
        test_id = self.downloadsModel.getIDs()[0]
        self.downloadsModel.updateItem(test_id, "CHANGED", "black")

        return

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

    def create_download_item(self, id, filename, total_size, color):
        self.downloadsModel.addItem(id, filename, total_size, color)

    def update_download_item(self, id, cur_size, progress, speed):
        self.downloadsModel.updateItem(id, cur_size, progress, speed)

    # open application window
    def open(self):
        #self.start_application()
        self.app_window.openWindow(self.trayIcon.geometry().center())
        #self.app_window.show()
        #self.app_window.requestActivate()


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
        if event == QtWidgets.QSystemTrayIcon.Trigger:
            self.last = "Click"
            self.open()
            self.clickTimer.start(self.doubleClickInterval())
        elif event == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.last = "DoubleClick"
            self.close()
            print("OPENING MAIN APPLICATION")


    # single click on tray icon
    def singleClickActivated(self):
        if self.last == "Clicks":
            self.open()


    def exec_(self):
        return super().exec_()
