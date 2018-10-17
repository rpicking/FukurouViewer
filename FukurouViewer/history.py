from PyQt5 import QtCore
from sqlalchemy import delete, insert, select, update

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
    
    _roles = { IDRole: "id", DateRole: "date", FilenameRole: "filename", FilepathRole: "filepath",
               SrcUrlRole: "src_url", DeadRole: "dead" }
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_oldest_time(self):
        return self._items[len(self._items) - 1].get("time_added")


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

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(int)
    def load_existing(self, start=0):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History]).order_by(user_database.History.time_added.desc()).limit(self.LOAD_INIT_COUNT)))
        
        self._model.insert_list(results)

    @QtCore.pyqtSlot()
    def load_more(self):
        oldest_time = self._model.get_oldest_time()

        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.History])
                    .where(user_database.History.time_added < oldest_time)
                    .order_by(user_database.History.time_added.desc())
                    .limit(self.LOAD_COUNT)))

        self._model.insert_list(results)

    @QtCore.pyqtSlot(int)
    def delete_item(self, index):
        self._model.remove_item(index)
        
        

