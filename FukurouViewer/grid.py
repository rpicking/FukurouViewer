import os
from enum import Enum

from pathlib import Path
from typing import Union, Optional

from PySide2.QtCore import Slot, Qt, QSortFilterProxyModel

from FukurouViewer.foundation import BaseModel, FileItem, SortType, DirectoryItem
from FukurouViewer.gallery import ZipArchiveGallery, Gallery


class GridModel(BaseModel):
    NameRole = Qt.UserRole + 1
    FilepathRole = Qt.UserRole + 2
    FileURIRole = Qt.UserRole + 3
    TypeRole = Qt.UserRole + 4

    _roles = {NameRole: "name", FilepathRole: "filepath", FileURIRole: "fileURI", TypeRole: "type"}

    def __init__(self, directory: Union[DirectoryItem, str] = None, items=None, sortType: SortType = SortType.NAME, desc=True):
        super().__init__(items)

        self.sortType = sortType
        self.desc = desc

        self.directory = None
        if directory is not None:
            self.setDirectory(directory)

    def isCurrentFolder(self, other: Union[DirectoryItem, str]):
        if self.directory is None:
            return False

        path = Path(other).resolve()
        if path.is_dir():
            return self.directory.samefile(path)
        return self.directory.samefile(path.parent)

    def setDirectory(self, directory: Union[DirectoryItem, str]):
        if isinstance(directory, str):
            directory = DirectoryItem(directory)

        self.directory = directory

        if not self.directory.parsed:
            self.directory.parse(False)

        self.set_list(self.directory.contents)


class FilteredGridModel(QSortFilterProxyModel):

    def __init__(self, directory: Union[DirectoryItem, str] = None, sortType: SortType = SortType.NAME, desc=True, parent=None):
        super().__init__(parent)
        self.gridModel = GridModel(directory, sortType=sortType, desc=desc)
        self.setFilterRole(GridModel.NameRole)
        self.setSourceModel(self.gridModel)

    @Slot(str)
    def setDirectory(self, directory: str):
        self.gridModel.setDirectory(directory)

    @Slot(str)
    def filter(self, filterStr):
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterFixedString(filterStr)


class GalleryGridModel(GridModel):

    def __init__(self):
        super().__init__()

        self.gallery = None  # type: Optional[Gallery]

    def setGallery(self, gallery: Gallery):
        if self.gallery is not None:
            self.gallery = None

        self.gallery = gallery
        self.gallery.load()

        self.set_list(self.gallery.files)

    def getFile(self, filepath: str) -> Optional[FileItem]:
        if self.gallery is None:
            return None
        return self.gallery.get_file(filepath)

