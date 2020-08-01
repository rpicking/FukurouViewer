import os
import random
import string
import bisect
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from datetime import timedelta
from typing import Union, List

from humanize import naturalsize
from sqlalchemy import select
from mimetypes import guess_type

from PySide2 import QtCore, QtGui

from . import user_database
from .filetype import FileType, FileTypeUtils
from .utils import Utils
from .logger import Logger


class Foundation(Logger):
    """Non "foundational" core functions for FukurouViewer application
        Functions that are used in multiple locations
        but are not building blocks for functionality
    """

    @staticmethod
    def uniqueID(items):
        """returns a unique id of length 6 for folder"""
        while True:
            id = Foundation.id_generator()
            if id not in items:
                return id

    @classmethod
    def uniqueFolderID(cls):
        with user_database.get_session(cls, acquire=True) as session:
            used_ids = Utils.convert_result(session.execute(
                select([user_database.Folders.uid])))

        used_ids = [item['uid'] for item in used_ids]
        return cls.uniqueID(used_ids)

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        """generates a id string"""
        return ''.join(random.choice(chars) for i in range(size))

    @classmethod
    def last_order(cls):
        """returns the highest order value + 1 of folders table"""
        with user_database.get_session(cls, acquire=True) as session:
            values = Utils.convert_result(session.execute(
                select([user_database.Folders.order])))
            if not values:
                return 1
            return max([x['order'] for x in values]) + 1

    @staticmethod
    def remove_invalid_chars(filename):
        """Remove invalid characters from string"""
        invalid_chars = '<>:"/\\|?*'
        return ''.join(c for c in filename if c not in invalid_chars)

    @staticmethod
    def format_size(size):
        """Returns string of number of bytes in human readable format"""
        size_string = naturalsize(size, binary=True)
        size_string = size_string.replace("i", "")
        return size_string.replace("ytes", "")

    @staticmethod
    def format_duration(duration):
        time_delta = timedelta(seconds=duration)
        days, seconds = time_delta.days, time_delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        eta_s = "{}{}{}{}".format(str(days) + "days, " if days > 0 else "",
                                  str(hours) + "h:" if hours > 0 else "",
                                  str(minutes) + "m:" if hours > 0 or minutes > 0 else "",
                                  str(seconds) + "s")
        return eta_s


class BaseModel(QtCore.QAbstractListModel, Logger):
    """ Base model implementation of abstract list model
        - insert_list
        - insert_item
        - remove_item
        - do_list_update
        - do_item_update        
    """

    _roles = {}

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._items = [] if items is None else items

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def roleNames(self):
        return {x: self._roles[x].encode() for x in self._roles}

    def getIndex(self, item):
        """Returns index of item in list returns None if not found"""
        for index, val in enumerate(self._items):
            if val == item:
                return index
        return None

    def set_list(self, list):
        self._items.clear()
        self.insert_list(list, 0)

    def insert_list(self, list, index=-1):
        """ insert list of items at index
            if index not specified insert at end
        """
        start_index = self.rowCount() if index == -1 else index
        end_index = start_index + len(list) - 1
        self.beginInsertRows(QtCore.QModelIndex(), start_index, end_index)

        self._items[start_index:start_index] = list

        self.endInsertRows()
        self.do_list_update(start_index)

    def insert_item(self, item, index=0):
        """ insert item into list at index """
        self.beginInsertRows(QtCore.QModelIndex(), index, index)
        self._items.insert(index, item)
        self.endInsertRows()
        self.do_list_update(index)

    def insert_new_item(self, item):
        index = bisect.bisect(self._items, item)
        self.insert_item(item, index)

    def remove_item(self, item, index=None):
        if index is None:
            index = self.getIndex(item)
        if index is not None:
            self.remove_item_by_index(index)

    def remove_item_by_index(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index, index)
        del self._items[index]
        self.endRemoveRows()
        self.do_list_update(index)

    def do_list_update(self, index=0):
        """notifies the view that the list starting at index has updated"""
        start_index = self.createIndex(index, 0)
        end_index = self.createIndex(len(self._items), 0)
        self.dataChanged.emit(start_index, end_index, [])

    def do_item_update(self, index):
        """notifies the view that item in the list at index has updated"""
        start_index = self.createIndex(index, 0)
        self.dataChanged.emit(start_index, start_index, [])

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """returns data at given index with for property role"""
        try:
            item = self._items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        return item.get(self._roles.get(role), None)

    @property
    def items(self):
        return self._items


class SortType(Enum):
    """Different ways of sorting list of files"""
    NAME = 1
    DATE_MODIFIED = 2


class FileSystemItem(object):

    def __init__(self, filepath: Union[Path, str], modified_date=None):
        if isinstance(filepath, str):
            filepath = Path(filepath).resolve()

        self.isBuffer = False
        self.path = Path(filepath).resolve()

        self.modified_date = self.getModifiedDate() if modified_date is None else modified_date

        self.initialize()
        self.type = self.determineType()

    def getModifiedDate(self) -> float:
        return os.path.getmtime(self.filepath) if os.path.exists(self.filepath) else -1

    @property
    def filepath(self):
        return str(self.path)

    @property
    def filename(self):
        return self.path.name

    @property
    def fileURI(self):
        return self.filepath

    @property
    def exists(self):
        return self.path.exists()

    def get(self, key, default=None):
        if key == "name":
            return self.filename
        if key == "fileURI":
            return self.fileURI
        if key == "filepath":
            return self.filepath
        if key == "modified_date":
            return self.modified_date
        if key == "type":
            return self.type.value
        return default

    @abstractmethod
    def initialize(self):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def determineType(self) -> FileType:
        return FileType.UNKNOWN

    def __eq__(self, other):
        if isinstance(other, FileSystemItem):
            return self.path == other.path
        elif isinstance(other, str):
            return self.path == Path(other).resolve()
        return False

    @staticmethod
    def createItem(path: Union[Path, str]):
        if path is None:
            return None

        if isinstance(path, str):
            path = Path(path).resolve()

        if path.is_dir():
            return DirectoryItem(path, False, False)
        else:
            return FileItem(path)


class DirectoryItem(FileSystemItem):

    def __init__(self, filepath: Union[Path, str], shouldParse=True, recursive=False):
        self.shouldParse = shouldParse
        self.recursive = recursive
        self.parsed = False

        self.directories = []  # type: List[DirectoryItem]
        self.files = []  # type: List[FileItem]

        super().__init__(filepath)

    def initialize(self):
        if self.shouldParse:
            self.parse(self.recursive)

    def determineType(self) -> FileType:
        return FileType.DIRECTORY

    def parse(self, recursive=False):
        item: os.DirEntry
        for item in os.scandir(str(self.filepath)):
            if item.is_dir():
                self.directories.append(DirectoryItem(item.path, recursive, recursive))
                continue
            else:
                self.files.append(FileItem(item.path))
        DirectoryItem.sort_files(self.files)
        self.parsed = True

    @property
    def contents(self) -> List[FileSystemItem]:
        contents = []  # type: List[FileSystemItem]
        contents.extend(self.directories)
        contents.extend(self.files)
        return contents

    @staticmethod
    def sort_files(files, sortMethod: SortType = SortType.NAME, desc=False):
        if sortMethod is SortType.NAME:
            def sortMethod(aFile: FileItem): return aFile.filename
        elif sortMethod is SortType.DATE_MODIFIED:
            def sortMethod(aFile: FileItem): return aFile.modified_date
        else:
            return

        files.sort(key=sortMethod, reverse=desc)


class FileItem(FileSystemItem):
    BUFFER_SUB_PROVIDER = "buffer/"

    def __init__(self, _filepath: Union[Path, str], _modified_date=None, data=None, isBuffer=None):
        self.data = data
        self.extension = None
        self.encoding = None
        self.mimetype = None
        self.mimeGroupType = None

        super().__init__(_filepath, _modified_date)
        self.isBuffer = isBuffer if isBuffer is not None else data is not None

    def initialize(self):
        _, extension = os.path.splitext(self.filepath)
        self.extension = extension[1:]

        self.mimetype, self.encoding = guess_type(str(self.path))
        self.mimeGroupType = None
        if self.mimetype is not None:
            self.mimeGroupType = self.mimetype.split("/", 1)[0]

    def determineType(self) -> FileType:
        mimeFileType = None
        if self.mimeGroupType is not None:
            mimeFileType = self.mimeGroupType.upper()

        # confirm image type
        if mimeFileType is FileType.IMAGE and self.canReadAsImage():
            return FileType.IMAGE

        extensionGuessedType = FileTypeUtils.file_type_from_extension(self.extension)

        if FileTypeUtils.extension_overrides_type(self.extension) and extensionGuessedType is not FileType.UNKNOWN:
            return extensionGuessedType

        isSupported = FileType.has_value(mimeFileType)
        if isSupported:
            return FileType(mimeFileType)

        return FileType.UNKNOWN

    def canReadAsImage(self):
        if self.isBuffer:
            return self.type == FileType.IMAGE

        imageReader = QtGui.QImageReader(self.filepath)
        imageReader.setDecideFormatFromContent(True)
        return imageReader.canRead()

    def updateModifiedDate(self):
        self.modified_date = os.path.getmtime(self.filepath) if os.path.exists(self.filepath) else -1

    def load(self, data):
        self.data = data

    @property
    def isLoaded(self):
        return self.data is not None

    @property
    def fileURI(self):
        return super().fileURI if not self.isBuffer else FileItem.BUFFER_SUB_PROVIDER + self.filepath

    def __lt__(self, other):
        return self.modified_date > other.modified_date

    def __str__(self):
        return ','.join((self.path.name, str(self.modified_date)))

    @property
    def __dict__(self):
        return {
            "name": self.filename,
            "filepath": self.filepath,
            "type": self.type.value,
            "fileURI": self.fileURI
        }
