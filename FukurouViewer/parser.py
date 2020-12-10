from typing import List

from FukurouViewer.files import DirectoryItem
from FukurouViewer.filetype import FileType
from FukurouViewer.gallery import DirectoryGallery, Gallery, ZipArchiveGallery
from FukurouViewer.user_database import Collection


class CollectionParser:
    """Responsible for parsing a given directory and creating gallery(s)"""

    @staticmethod
    def add(path: str) -> Collection:
        """Add a new collection.  If a folder already exists with the path, don't create a new one and just parse"""

        collection = Collection.get_by_path(path)
        if collection is not None:
            CollectionParser.parse(collection)
            return collection

        collection = Collection(path=path, recursive=True)
        collection.add()
        CollectionParser.parse(collection)
        return collection

    @staticmethod
    def parse(collection: Collection):
        collection.galleries.extend(CollectionParser.parse_directory(collection.directory))

    @staticmethod
    def parse_directory(directory: DirectoryItem) -> List[Gallery]:
        galleries = []

        type = Collection.determine_type(directory)
        if type is Collection.Type.GALLERY:
            galleries.append(DirectoryGallery(directory))
        elif type is Collection.Type.COLLECTION_GALLERY:
            for file in directory.files:
                if file.type is FileType.ARCHIVE:
                    galleries.append(ZipArchiveGallery(file))
                pass

            for directory in directory.directories:
                galleries.extend(CollectionParser.parse_directory(directory))

        return galleries
