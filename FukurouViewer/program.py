import os
import sys
import time
import argparse
from enum import Enum
from threading import RLock
from sqlalchemy import delete, insert, select, update
from collections import namedtuple

from . import user_database
from .utils import Utils
from .config import Config
from .logger import Logger
from .foundation import Foundation

from PyQt5 import QtCore, QtGui, QtQml, QtQuick, QtWidgets

from urllib.parse import unquote


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
        self.setToolTip("Fukurou Viewer")
           

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
    def __init__(self, item):
        self.id = item.id
        self.filename = item.filename
        self.filepath = item.filepath
        self.total_size = item.total_size_str
        self.folderName = item.folder.get("name")
        self.color = item.folder.get("color")
        self.cur_size = "0 B"
        self.percent = 0
        self.speed = "queued"
        self.queued = True
        self.timestamp = item.start_time
        self.eta = item.ETA_LIMIT

    def update(self, kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

        if not isinstance(self.total_size, str):
            self.total_size = Foundation.format_size(self.total_size)
        if not isinstance(self.cur_size, str):
            self.cur_size = Foundation.format_size(self.cur_size)
        if not isinstance(self.speed, str):
            self.speed = Foundation.format_size(self.speed) + "/s"
        if not isinstance(self.eta, str):
            self.eta = Foundation.format_duration(self.eta)

    def start(self):
        self.queued = False
        self.speed = "0 KB/s"

    def finish(self, _timestamp):
        self.cur_size = self.total_size
        self.percent = 100
        self.speed = ""
        self.timestamp = _timestamp
        self.eta = ""


class DownloadsModel(QtCore.QAbstractListModel):
    IDRole = QtCore.Qt.UserRole + 1
    FilenameRole = QtCore.Qt.UserRole + 2
    FilepathRole = QtCore.Qt.UserRole + 3
    TotalSizeRole = QtCore.Qt.UserRole + 4
    FolderNameRole = QtCore.Qt.UserRole + 5
    ColorRole = QtCore.Qt.UserRole + 6
    CurSizeRole = QtCore.Qt.UserRole + 7
    PercentRole = QtCore.Qt.UserRole + 8
    SpeedRole = QtCore.Qt.UserRole + 9
    QueuedRole = QtCore.Qt.UserRole + 10
    TimeStampRole = QtCore.Qt.UserRole + 11
    EtaRole = QtCore.Qt.UserRole + 12

    _roles = {IDRole: "id", FilenameRole: "filename", FilepathRole: "filepath", 
              TotalSizeRole: "total_size", FolderNameRole: "folderName", 
              ColorRole: "color", CurSizeRole: "cur_size", PercentRole: "percent", 
              SpeedRole: "speed", QueuedRole: "queued", TimeStampRole: "timestamp",
              EtaRole: "eta"}

    def __init__(self, parent=None):
        super(DownloadsModel, self).__init__(parent)
        self._items = []

    def addItem(self, item):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self._items.insert(0, Download(item))
        self.endInsertRows()
        self.do_item_update(0)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        try:
            item = self._items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        if role == self.IDRole:
            return item.id
        if role == self.FilenameRole:
            return item.filename
        if role == self.FilepathRole:
            return item.filepath
        if role == self.TotalSizeRole:
            return item.total_size
        if role == self.FolderNameRole:
            return item.folderName
        if role == self.ColorRole:
            return item.color
        if role == self.CurSizeRole:
            return item.cur_size
        if role == self.PercentRole:
            return item.percent
        if role == self.SpeedRole:
            return item.speed
        if role == self.QueuedRole:
            return item.queued
        if role == self.TimeStampRole:
            return item.timestamp
        if role == self.EtaRole:
            return item.eta

        return QtCore.QVariant()

    def roleNames(self):
        return {x: self._roles[x].encode() for x in self._roles}

    def getIDs(self):
        """Returns list of all used download UI ids"""
        cur_ids = [item.id for item in self._items]

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Downloads])))
        unfinished_ids = [item.get("id") for item in results]
        return cur_ids + list(set(unfinished_ids) - set(cur_ids))

    # creates new unique id for download item in UI
    def createID(self):
        """Creates unique id for download UI list item"""
        used_ids = self.getIDs()
        return Foundation.uniqueID(used_ids)

    def get_item_index(self, id):
        """Return turns the index of the item with id if it exists in the list"""
        for index, item in enumerate(self._items):
            if item.id == id:
                return index
        else:   # id doesn't exist
            return None

    # TODO: THIS MIGHT NEED TO BE SWITCHED TO SETDATA  https://stackoverflow.com/questions/20784500/qt-setdata-method-in-a-qabstractitemmodel
    # updates filename and color of current download item with id
    def updateItem(self, kwargs):
        """Updates active download values"""                
        index = self.get_item_index(kwargs.get("id"))
        if index == None:
            return
        self._items[index].update(kwargs)
        self.do_item_update(index)


    def do_full_update(self):
        """Forces all items in UI to update to new data from model"""
        start_index = self.createIndex(0,0)
        end_index = self.createIndex(len(self._items) - 1, 0)
        self.dataChanged.emit(start_index, end_index, [])

    
    def do_item_update(self, index):
        """Forces specific item at index to update in UI"""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index, self.roleNames())
        

    def start_item(self, id):
        """Sets start values for item that has begun downloading"""
        index = self.get_item_index(id)
        if index == None:
            return

        self._items[index].start()
        self.do_item_update(index)


    def finish_item(self, id, timestamp):
        """Sets values for item that has finished downloading"""
        index = self.get_item_index(id)
        if index == None:
            return

        self._items[index].finish(timestamp)
        self.do_item_update(index)
        return self._items[index].total_size


    def remove_item(self, id):
        """Remove an item at id from the download list and updates UI"""
        index = self.get_item_index(id)
        if index == None:
            return

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self._items.pop(index)
        self.endRemoveRows()

        

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
                select([user_database.History]).where( user_database.History.id == id)))[0]

        path = results.get("full_path")
        if not os.path.exists(path):
            _, ext = os.path.splitext(path)
            tmpfile = os.path.join(Program.TMP_DIR, "tmpfile" + ext)
            open(tmpfile, 'a').close()
            path = tmpfile

        icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(path))
        pixmap = icon.pixmap(icon.availableSizes()[-2])  # largest size screws up and makes small icon
        pixmap = pixmap.scaled(width, height, transformMode=QtCore.Qt.SmoothTransformation)
        return pixmap, requestedSize



class DownloadUIManager(QtCore.QObject):
    
    def __init__(self):
        super().__init__()
        self._total_downloads = 0
        self._running_downloads = 0
        self._total_progress = 0
        self._downloads = []

    def get_total_downloads(self):
        return self._total_downloads

    def get_running_downloads(self):
        return self._running_downloads

    def get_total_progress(self):
        return Foundation.format_size(self._total_progress)

    def get_current_progress(self):
        cur_progress = 0
        for item in self._downloads:
            cur_progress += item.get("cur_size", 0)
        return Foundation.format_size(cur_progress)

    def get_speed(self):
        speed = 0
        for item in self._downloads:
            speed += item.get("speed")
        return Foundation.format_size(speed) + "/s"

    def get_percent(self):
        cur_progress = 0
        for item in self._downloads:
            cur_progress += item.get("cur_size")

        percent = 0 if not cur_progress else cur_progress / self._total_progress
        #percent = cur_progress / self._total_progress
        return percent

    def get_eta(self):
        eta = 0
        for item in self._downloads:
            eta += item.get("eta")

        return Foundation.format_duration(eta)

    def add_download(self, id, total_size):
        self._total_downloads += 1
        self._total_progress += total_size

        self._downloads.append({"id": id, "total_size": total_size, "cur_size": 0, "speed": 0, "eta": 0 })

        self.on_total_downloads.emit()
        self.on_total_progress.emit()

    def start_download(self):
        self._running_downloads += 1
        self.on_running_downloads.emit()

    def update_progress(self, kwargs):
        for item in self._downloads:
            if item.get("id") == kwargs.get("id"):
                item["cur_size"] = kwargs.get("cur_size", item["cur_size"])
                item["speed"] = kwargs.get("speed", item["speed"])
                item["eta"] = kwargs.get("eta", item["eta"])
                break

        self.on_speed.emit()
        self.on_current_progress.emit()
        self.on_percent.emit()
        self.on_eta.emit()

    def finish_download(self, id, total_size):
        self.update_progress({"id": id, "cur_size": total_size, "speed": 0})

        self._running_downloads -= 1        
        self.on_running_downloads.emit()

    def remove_download(self, id, status):
        for item in self._downloads:
            if item.get("id") == id:
                self._total_progress -= item.get("total_size")
                self.on_total_progress.emit()
                self._downloads.remove(item)
                break

        if status != "done":
            self._running_downloads -= 1
            self.on_running_downloads.emit()

        self._total_downloads -= 1
        self.on_total_downloads.emit()

        self.on_speed.emit()
        self.on_current_progress.emit()
        self.on_percent.emit()
        self.on_eta.emit()


    on_total_downloads = QtCore.pyqtSignal()
    total_downloads = QtCore.pyqtProperty(int, get_total_downloads, notify=on_total_downloads)

    on_running_downloads = QtCore.pyqtSignal()
    running_downloads = QtCore.pyqtProperty(int, get_running_downloads, notify=on_running_downloads)

    on_total_progress = QtCore.pyqtSignal()
    total_progress = QtCore.pyqtProperty(str, get_total_progress, notify=on_total_progress)

    on_current_progress = QtCore.pyqtSignal()
    current_progress = QtCore.pyqtProperty(str, get_current_progress, notify=on_current_progress)

    on_percent = QtCore.pyqtSignal()
    percent = QtCore.pyqtProperty(float, get_percent, notify=on_percent)

    on_speed = QtCore.pyqtSignal()
    speed = QtCore.pyqtProperty(str, get_speed, notify=on_speed)

    on_eta = QtCore.pyqtSignal()
    eta = QtCore.pyqtProperty(str, get_eta, notify=on_eta)


class GridModel(QtCore.QAbstractListModel):
    IDRole = QtCore.Qt.UserRole + 1
    NameRole = QtCore.Qt.UserRole + 2
    FilepathRole = QtCore.Qt.UserRole + 3

    _roles = { IDRole: "id", NameRole: "name", FilepathRole: "filepath" }

    def __init__(self, items, parent=None):
        super(GridModel, self).__init__(parent)
        self._items = items
        #self.setRoleNames(dict(enumerate(GridModel.COLUMNS)))

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def roleNames(self):
        return {x: self._roles[x].encode() for x in self._roles}

    def data(self, index, role):
        if index.isValid():
            return self._items[index.row()]
        return None

    def data(self, index, role):
        try:
            item = self._items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        return item.get(GridModel._roles.get(role), QtCore.QVariant())


class ThumbnailProvider(QtQuick.QQuickImageProvider):
    THUMB_DIR = Utils.fv_path("thumbs")

    def __init__(self):
        QtQuick.QQuickImageProvider.__init__(self, QtQuick.QQuickImageProvider.Pixmap)
        
        self.supported_formats = [ "." + format.data().decode("utf-8") for format in QtGui.QImageReader.supportedImageFormats() ]

    def requestImage(self, file, requestedSize):
        width = requestedSize.width()
        height = requestedSize.height()

        filepath = unquote(file)
        _, ext = os.path.splitext(filepath)

        if ext in self.supported_formats:
            image = QtGui.QImage(filepath)
            image = image.scaledToWidth(width, QtCore.Qt.SmoothTransformation)
        else:
            image = QtGui.QImage(200, 280, QtGui.QImage.Format_RGB32)
            image.fill(QtCore.Qt.red)

        return image, requestedSize

    def requestPixmap(self, file, requestedSize):
        width = requestedSize.width()
        height = requestedSize.height()

        filepath = unquote(file)
        _, ext = os.path.splitext(filepath)

        if ext in self.supported_formats:
            image = QtGui.QPixmap(filepath)
            if width != -1 and height != -1:
                image = image.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            image = QtGui.QPixmap(200, 280)
            image.fill(QtCore.Qt.red)

        return image, requestedSize


Coordinate = namedtuple("Coordinate", "x y")

class BlowUpItem(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._x = 0
        self._y = 0
        self.startPoint = Coordinate(0,0)
        self.anchorPosition = Coordinate(0,0)    # top left point for thumbnail
        
        self.width = 0
        self.height = 0

    def initItem(self, _start_point, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent):
        self.startPoint = Coordinate(_start_point.x(), _start_point.y())

        self._x = self.startPoint.x - (item_width * xPercent);
        self._y =  self.startPoint.y - (item_height * yPercent);
        self.anchorPosition = Coordinate(self._x, self._y)

        self.width = item_width
        self.height = item_height
        self.x_ratio = int(item_width / thumb_width)
        self.y_ratio = int(item_height / thumb_height)

        self.on_postion_change.emit()

    def movePosition(self, mouseX, mouseY):
        deltaX = self.startPoint.x - mouseX
        deltaY = self.startPoint.y - mouseY

        self._x = self.anchorPosition.x + (deltaX * self.x_ratio)
        self._y = self.anchorPosition.y + (deltaY * self.y_ratio)
        self.on_postion_change.emit()

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    on_postion_change = QtCore.pyqtSignal()
    x = QtCore.pyqtProperty(int, get_x, notify=on_postion_change)
    y = QtCore.pyqtProperty(int, get_y, notify=on_postion_change)


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
        self.addLibraryPath(os.path.dirname(__file__))  #not sure
        super().__init__(args)
        self.setOrganizationName("FV")
        self.setApplicationName("FukurouViewer")
        self.setOrganizationDomain(self.GITHUB)
        self.version = "0.2.0"
    
        self.setQuitOnLastWindowClosed(False)

        #id = QtGui.QFontDatabase.addApplicationFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf"))
        #family = QtGui.QFontDatabase.applicationFontFamilies(id)[0]
        #font = QtGui.QFont(family)
        font = QtGui.QFont("Verdana")
        self.setFont(font)
        
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(self.BASE_PATH, "icon.png"))))
        #self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))


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
        self.setDoubleClickInterval(300)
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

    
    def start_application(self, mode="TRAY"):
        try:
            self.engine
        except AttributeError:  # qml engine not started

            self.engine = QtQml.QQmlApplicationEngine()
            self.engine.addImportPath(self.QML_DIR)

            self.image_provider = ImageProvider()
            self.engine.addImageProvider("fukurou", self.image_provider)

            self.thumb_image_provider = ThumbnailProvider()
            self.engine.addImageProvider("thumbs", self.thumb_image_provider)


            self.downloadsModel = DownloadsModel()
            self.downloadUIManager = DownloadUIManager()

            
            with user_database.get_session(self, acquire=True) as session:
                results = Utils.convert_result(session.execute(
                    select([user_database.Folders]).where(user_database.Folders.id == 1)))[0]

            test_folder = results.get("path")            

            # gallery test grid
            test = []
            for dirpath, subdirs, filenames in os.walk(test_folder):
                for file in sorted(filenames, key=lambda file: 
                                   os.path.getmtime(os.path.join(dirpath, file)), reverse=True):
                    test.append({"name": file, "filepath": os.path.join(dirpath, file)})

            self.gridModel = GridModel(test[0:150])

            # blow up preview 
            self.blow_up_item = BlowUpItem()
            
            self.context = self.engine.rootContext()

            self.context.setContextProperty("downloadsModel", self.downloadsModel)
            self.context.setContextProperty("downloadManager", self.downloadUIManager)
            self.context.setContextProperty("gridModel", self.gridModel)
            self.context.setContextProperty("blowUp", self.blow_up_item)
            
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
            self.app_window.setEventFilter.connect(self.setEventFilter)
            self.app_window.closeApplication.connect(self.close)
            self.app_window.downloader_task.connect(self.downloader_task)

            #self.open("APP")

            #self.app_window.setMode(mode) # default mode? move to qml then have way of changing if not starting in default

            #with user_database.get_session(self, acquire=True) as session:
             #   results = session.query(user_database.History).filter(user_database.History.id == 183).first()
              #  test = results.gallery
               # print("BREAK")

    def setEventFilter(self, coords, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent):
        self.installEventFilter(self)
        self.blow_up_item.initItem(coords, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent)
        

    def closeBlowUpItem(self):
        self.app_window.closeBlowUpWindow()
        self.removeEventFilter(self)


    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseMove:
            self.blow_up_item.movePosition(event.globalX(), event.globalY())
            return True
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.LeftButton:
                self.closeBlowUpItem()
            return True
        if event.type() == QtCore.QEvent.Wheel: # zoom blowup on scroll wheel
            scrollAmount = event.angleDelta().y() / 120
            self.app_window.scrollBlowUp.emit(scrollAmount)
            return True
        return super().eventFilter(obj, event)


    def sorted_dir(self, folder):
        def getmtime(name):
            path = os.path.join(folder, name)
            return os.path.getmtime(path)
        
        return sorted(os.listdir(folder), key=getmtime)

    # sends limited number of history entries newest first to ui
    def send_history(self, index, limit=0):
        self.history_health_check()

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).order_by(user_database.History.time_added.desc())))

            results = results[index: index + limit]
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
    def delete_history_item(self, id, count):
        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.History).where(user_database.History.id == id))
        self.send_history(0, count - 1)


    # open history item file in default application or open file explorer to directory
    def open_item(self, path, type):
        if type == "file":
            qurl = QtCore.QUrl.fromLocalFile(path)
        elif type == "folder":
            qurl = QtCore.QUrl.fromLocalFile(os.path.dirname(os.path.abspath(path)))
        elif type == "url":
            qurl = QtCore.QUrl(path)
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
        
    def downloader_task(self, id, status):
        if status == "delete" or status == "done":
            self.downloadsModel.remove_item(id)
            self.downloadUIManager.remove_download(id, status)

    # open application window
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

    def onTrayIconActivated(self, event):
        if event == QtWidgets.QSystemTrayIcon.Trigger:
            self.last = "Click"
            self.clickTimer.start(self.doubleClickInterval())
        elif event == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.last = "DoubleClick"
            self.close()
            self.open("APP")
            print("OPENING MAIN APPLICATION")


    # single click on tray icon
    def singleClickActivated(self):
        if self.last == "Click":
            self.open()


    def exec_(self):
        return super().exec_()
