from PySide2 import QtCore

from sqlalchemy import select

from FukurouViewer import user_database, Utils
from FukurouViewer.foundation import Foundation


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
        # percent = cur_progress / self._total_progress
        return percent

    def get_eta(self):
        eta = 0
        for item in self._downloads:
            eta += item.get("eta")

        return Foundation.format_duration(eta)

    def add_download(self, id, total_size):
        self._total_downloads += 1
        self._total_progress += total_size

        self._downloads.append({"id": id, "total_size": total_size, "cur_size": 0, "speed": 0, "eta": 0})

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

    on_total_downloads = QtCore.Signal()
    total_downloads = QtCore.Property(int, get_total_downloads, notify=on_total_downloads)

    on_running_downloads = QtCore.Signal()
    running_downloads = QtCore.Property(int, get_running_downloads, notify=on_running_downloads)

    on_total_progress = QtCore.Signal()
    total_progress = QtCore.Property(str, get_total_progress, notify=on_total_progress)

    on_current_progress = QtCore.Signal()
    current_progress = QtCore.Property(str, get_current_progress, notify=on_current_progress)

    on_percent = QtCore.Signal()
    percent = QtCore.Property(float, get_percent, notify=on_percent)

    on_speed = QtCore.Signal()
    speed = QtCore.Property(str, get_speed, notify=on_speed)

    on_eta = QtCore.Signal()
    eta = QtCore.Property(str, get_eta, notify=on_eta)


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

    def data(self, index, role=QtCore.Qt.DisplayRole):
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

    # TODO: THIS MIGHT NEED TO BE SWITCHED TO SETDATA
    # https://stackoverflow.com/questions/20784500/qt-setdata-method-in-a-qabstractitemmodel
    # updates filename and color of current download item with id
    def updateItem(self, kwargs):
        """Updates active download values"""
        index = self.get_item_index(kwargs.get("id"))
        if index is None:
            return
        self._items[index].update(kwargs)
        self.do_item_update(index)

    def do_full_update(self):
        """Forces all items in UI to update to new data from model"""
        start_index = self.createIndex(0, 0)
        end_index = self.createIndex(len(self._items) - 1, 0)
        self.dataChanged.emit(start_index, end_index, [])

    def do_item_update(self, index):
        """Forces specific item at index to update in UI"""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index, self.roleNames())

    def start_item(self, id):
        """Sets start values for item that has begun downloading"""
        index = self.get_item_index(id)
        if index is None:
            return

        self._items[index].start()
        self.do_item_update(index)

    def finish_item(self, id, timestamp):
        """Sets values for item that has finished downloading"""
        index = self.get_item_index(id)
        if index is None:
            return

        self._items[index].finish(timestamp)
        self.do_item_update(index)
        return self._items[index].total_size

    def remove_item(self, id):
        """Remove an item at id from the download list and updates UI"""
        index = self.get_item_index(id)
        if index is None:
            return

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        self._items.pop(index)
        self.endRemoveRows()


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
