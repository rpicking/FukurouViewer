import os
from enum import Enum

from pathlib import Path
from typing import Union, Optional

from PySide2.QtCore import Slot, Qt, QSortFilterProxyModel

from FukurouViewer.foundation import BaseModel, FileItem
from FukurouViewer.gallery import GalleryArchive


class SortType(Enum):
    """Different ways of sorting list of files"""
    NAME = 1
    DATE_MODIFIED = 2


class GridModel(BaseModel):
    NameRole = Qt.UserRole + 1
    FilepathRole = Qt.UserRole + 2
    FileURIRole = Qt.UserRole + 3
    TypeRole = Qt.UserRole + 4

    _roles = {NameRole: "name", FilepathRole: "filepath", FileURIRole: "fileURI", TypeRole: "type"}

    def __init__(self, directory: str = None, items=None, sortType: SortType = SortType.NAME, desc=True):
        super().__init__(items)

        self.sortType = sortType
        self.desc = desc

        self.directory = None
        if directory is not None:
            self.setDirectory(directory)

    def isCurrentFolder(self, other):
        if self.directory is None:
            return False

        path = Path(other).resolve()
        if path.is_dir():
            return self.directory.samefile(path)
        return self.directory.samefile(path.parent)

    def setDirectory(self, directory: Union[str, Path]):
        if isinstance(directory, str):
            directory = Path(directory).resolve()

        self.directory = directory
        self._items.clear()

        files = []
        file: os.DirEntry
        for file in os.scandir(str(directory.absolute())):
            if file.is_dir():
                continue
            files.append(FileItem(file.path))

        self.sortFiles(files)
        self.insert_list(files, 0)

    def sortFiles(self, files):
        if self.sortType is SortType.NAME:
            def sortMethod(aFile): return aFile.path.name
        elif self.sortType is SortType.DATE_MODIFIED:
            def sortMethod(aFile): return aFile.modified_date
        else:
            return

        files.sort(key=sortMethod, reverse=self.desc)


class FilteredGridModel(QSortFilterProxyModel):

    def __init__(self, directory: str = None, sortType: SortType = SortType.NAME, desc=True, parent=None):
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

        self.gallery = None  # type: Optional[GalleryArchive]

    def setGallery(self, gallery: GalleryArchive):
        if self.gallery is not None:
            self.gallery = None

        self.gallery = gallery
        self.gallery.load()

        self.insert_list(self.gallery.files, 0)

    def getFile(self, filepath: str) -> Optional[FileItem]:
        if self.gallery is None:
            return None
        return self.gallery.getFile(filepath)

