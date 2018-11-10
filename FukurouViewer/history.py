import os
from datetime import datetime
from PyQt5 import QtCore
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

    @QtCore.pyqtProperty(QtCore.QAbstractListModel, constant=True)
    def model(self):
        return self._model
    
    def newest_timestamp(self):
        return self._model._items[0].get("time_added")

    @QtCore.pyqtSlot(name="load_existing")
    def load_existing(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(
                session.execute(select([user_database.History])
                                .order_by(user_database.History.time_added.desc())
                                .limit(self.LOAD_COUNT)
                                .offset(self._model.rowCount())))
            for item in results:
                item["date"] = datetime.fromtimestamp(item.get("time_added")).strftime("%B %d, %Y")

                # check if file exists 
                if not os.path.exists(item.get("filepath")):
                    session.execute(update(user_database.History).where(
                        user_database.History.id == item.get("id")).values({"dead": True}))
                    item["dead"] = True

        today = datetime.today()
        for item in results:
            
            cur_date = datetime.fromtimestamp(item.get("time_added"))
            day_diff = (today - cur_date).days
            if day_diff == 0:
                item["date"] = "Today"
            elif day_diff == 1:
                item["date"] = "Yesterday"
            else:
                break
        self._model.insert_list(results)

    def add_new(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(
                session.execute(select([user_database.History])
                                .where(user_database.History.time_added > self.newest_timestamp())
                                .order_by(user_database.History.time_added.desc())))

        today = datetime.today()
        for item in results:
            cur_date = datetime.fromtimestamp(item.get("time_added"))
            day_diff = (today - cur_date).days
            if day_diff == 0:
                item["date"] = "Today"
            elif day_diff == 1:
                item["date"] = "Yesterday"
            else:
                break
        self._model.insert_list(results, 0)

    @QtCore.pyqtSlot(int, int, name="delete_item")
    def delete_item(self, index, db_id):
        self._model.remove_item(index)
        
        with user_database.get_session(self, acquire=True) as session:
            session.execute(delete(user_database.History).where(user_database.History.id == db_id))
