import os
from datetime import datetime
from PySide2 import QtCore
from sqlalchemy import delete, select, update

from . import user_database
from .utils import Utils
from .logger import Logger
from .foundation import BaseModel


class HistoryModel(BaseModel):
    IDRole = QtCore.Qt.UserRole + 1
    DateRole = QtCore.Qt.UserRole + 2
    FilenameRole = QtCore.Qt.UserRole + 3
    FilepathRole = QtCore.Qt.UserRole + 4
    SrcUrlRole = QtCore.Qt.UserRole + 5
    DeadRole = QtCore.Qt.UserRole + 6
    
    _roles = {IDRole: "id", DateRole: "date", FilenameRole: "filename", FilepathRole: "filepath",
              SrcUrlRole: "src_url", DeadRole: "dead"}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        

class History(QtCore.QObject, Logger):
    LOAD_INIT_COUNT = 100
    LOAD_COUNT = 50
        
    def __init__(self):
        super().__init__()
        self._model = HistoryModel()
        self.load_existing()

    @QtCore.Property(QtCore.QObject, constant=True)
    def model(self):
        return self._model
    
    def newest_timestamp(self):
        return self._model.items[0].get("time_added")

    @QtCore.Slot(name="load_existing")
    def load_existing(self):
        today = datetime.today()
        items = []
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(
                session.execute(select([user_database.History])
                                .order_by(user_database.History.time_added.desc())
                                .limit(self.LOAD_COUNT)
                                .offset(self._model.rowCount())))
            for item in results:
                history_item = HistoryItem(item)

                cur_date = datetime.fromtimestamp(item.get("time_added"))
                day_diff = (today - cur_date).days
                if day_diff == 0:
                    date_str = "Today"
                elif day_diff == 1:
                    date_str = "Yesterday"
                else:
                    date_str = cur_date.strftime("%B %d, %Y")
                history_item.date = date_str

                # check if file exists 
                if not os.path.exists(item.get("filepath")):
                    session.execute(update(user_database.History).where(
                        user_database.History.id == item.get("id")).values({"dead": True}))
                    history_item.dead = True

                items.append(history_item)

        self._model.insert_list(items)

    def add_new(self):
        today = datetime.today()
        items = []
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(
                session.execute(select([user_database.History])
                                .where(user_database.History.time_added > self.newest_timestamp())
                                .order_by(user_database.History.time_added.desc())))

        for item in results:
            history_item = HistoryItem(item)
            cur_date = datetime.fromtimestamp(item.get("time_added"))
            day_diff = (today - cur_date).days
            if day_diff == 0:
                date_str = "Today"
            elif day_diff == 1:
                date_str = "Yesterday"
            else:
                date_str = cur_date.strftime("%B %d, %Y")
            history_item.date = date_str
            items.append(history_item)

        self._model.insert_list(items, 0)

    @QtCore.Slot(int, int, name="delete_item")
    def delete_item(self, index, db_id):
        self._model.remove_item_by_index(index)
        
        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.History).where(user_database.History.id == db_id))


class HistoryItem(object):
    def __init__(self, item):
        self.id = item.get("id")
        self.date = item.get("date")
        self.time_added = item.get("time_added")
        self.filename = item.get("filename")
        self.filepath = item.get("filepath")
        self.src_url = item.get("src_url")
        self.dead = item.get("dead")

    def __lt__(self, other):
        return self.id > other.id

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return ','.join((self.id, self.filename, self.filepath))
