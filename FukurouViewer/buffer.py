from FukurouViewer.files import FileItem, FileSystemItem


class ImageBuffer(object):

    FILES = {}

    @staticmethod
    def add(file: FileSystemItem):
        ImageBuffer.FILES[file.filepath] = file

    @staticmethod
    def remove(id: str):
        if id in ImageBuffer.FILES:
            ImageBuffer.FILES.pop(id)

    @staticmethod
    def isBufferFilepath(filepath: str):
        return filepath.startswith(FileItem.BUFFER_SUB_PROVIDER)

    @staticmethod
    def getFilepath(id: str):
        return id[len(FileItem.BUFFER_SUB_PROVIDER):]

    @staticmethod
    def getFileItem(id: str) -> FileSystemItem:
        filepath = ImageBuffer.getFilepath(id)
        return ImageBuffer.FILES[filepath]
