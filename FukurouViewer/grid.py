from pathlib import Path
from PySide2 import QtCore

from FukurouViewer.foundation import BaseModel


class GridModel(BaseModel):
    NameRole = QtCore.Qt.UserRole + 1
    FilepathRole = QtCore.Qt.UserRole + 2
    TypeRole = QtCore.Qt.UserRole + 3

    _roles = {NameRole: "name", FilepathRole: "filepath", TypeRole: "type"}

    def __init__(self, _folder_path, items=None):
        super().__init__(items)
        self.folder_path = Path(_folder_path).resolve()

    def isCurrentFolder(self, other):
        path = Path(other).resolve()
        if path.is_dir():
            return self.folder_path.samefile(path)
        return self.folder_path.samefile(path.parent)


class FilteredGridModel(QtCore.QSortFilterProxyModel):

    def __init__(self, gridModel, parent=None):
        super().__init__(parent)

        self.gridModel = gridModel
        self.setFilterRole(GridModel.NameRole)
        self.setSourceModel(self.gridModel)

    @QtCore.Slot(str)
    def filter(self, filterStr):
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterFixedString(filterStr)
