import os
from abc import abstractmethod
from enum import Enum
from mimetypes import guess_type
from pathlib import Path
from typing import Union, List, Optional

from PySide2 import QtGui

from FukurouViewer.filetype import FileType, FileTypeUtils
from FukurouViewer.utils import Utils


class SortType(Enum):
    """Different ways of sorting list of files"""
    NAME = 1
    DATE_MODIFIED = 2


class FileSystemItem(object):

    def __init__(self, filepath: Union[Path, str], modified_date=None):
        if isinstance(filepath, str):
            filepath = FileSystemItem.parse_path(filepath)

        self.isBuffer = False
        self.path = filepath

        self.modified_date = self.getModifiedDate() if modified_date is None else modified_date

        self.initialize()
        self.type = self.determineType()

    def getModifiedDate(self) -> float:
        return os.path.getmtime(self.filepath) if os.path.exists(self.filepath) else -1

    def samefile(self, other):
        if isinstance(other, FileSystemItem):
            return self.path.samefile(other.path)
        else:
            return self.path.samefile(other)

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
            path = FileSystemItem.parse_path(path)

        if path.is_dir():
            return DirectoryItem(path, False, False)
        else:
            return FileItem(path)

    @staticmethod
    def parse_path(path: str) -> Optional[Path]:
        """Given a path, return an absolute path, substituting a relative or drive relative path variables when required.
           Given D:/Dir/FukurouViewer/program.py
             ../Test/ -> D:/Dir/Test/
             ?:/Other/Test -> D:/Other/Test"""
        if path is None:
            return None

        # windows drive replacement
        if path.startswith("?:/"):
            drive, tail = os.path.splitdrive(Utils.base_path())
            path = path.replace("?:", drive)

        # UNC path replacement
        if path.startswith("//?/"):
            drive, tail = os.path.splitdrive(Utils.base_path())
            path = path.replace("//?", drive)

        # relative path replacement
        if path.startswith("../") or path.startswith("./"):
            path = Utils.base_path(path)

        return Path(path).resolve()


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
