import os
import random
import string
import bisect
from pathlib import Path
from datetime import timedelta
from humanize import naturalsize
from sqlalchemy import select
from mimetypes import guess_type

from PySide2 import QtCore

from . import user_database
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
        invalid_chars = '<>:"/\|?*'
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

    def do_list_update(self, index):
        """notifies the view that the list starting at index has updated"""
        start_index = self.createIndex(index, 0)
        end_index = self.createIndex(len(self._items), 0)
        self.dataChanged.emit(start_index, end_index, [])

    def do_item_update(self, index):
        """notifies the view that item in the list at index has updated"""
        start_index = self.createIndex(index, 0)
        self.dataChanged.emit(start_index, start_index, [])
        
    def data(self, index, role):
        """returns data at given index with for property role"""
        try:
            item = self._items[index.row()]
        except IndexError:
            return QtCore.QVariant()

        return item.get(self._roles.get(role), None)


class FileItem(object):

    def __init__(self, _filepath, _modified_date=None):
        self.filepath = _filepath
        self.path = Path(_filepath).resolve()

        mimetype, encoding = guess_type(str(self.path))
        self.type = mimetype.split("/", 1)[0]

        if _modified_date is not None:
            self.modified_date = _modified_date
        else:
            self.updateModifiedDate()

    def __lt__(self, other):
        return self.modified_date > other.modified_date

    def get(self, key, default=None):
        if key == "filepath":
            return str(self.path)
        if key == "modified_date":
            return self.modified_date
        if key == "type":
            return self.type
        return default

    def exists(self):
        return self.path.exists()

    def setModifiedDate(self, date):
        self.modified_date = date

    def updateModifiedDate(self):
        self.modified_date = os.path.getmtime(self.filepath) if os.path.exists(self.filepath) else -1

    def __eq__(self, other):
        return self.path == other.path

    def __str__(self):
        return ','.join((self.path.name, str(self.modified_date)))
