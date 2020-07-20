from enum import Enum


class FileType(Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    ARCHIVE = "ARCHIVE"
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    DOCUMENT = "DOCUMENT"

    UNKNOWN = "UNKNOWN"

    @classmethod
    def has_value(cls, value):
        return value in set(item.value for item in FileType)


class FileTypeUtils:

    COMMON_IMAGE_EXTENSIONS = []
    COMMON_VIDEO_EXTENSIONS = []
    COMMON_AUDIO_EXTENSIONS = []
    COMMON_ARCHIVE_EXTENSIONS = ["cbz", "zip"]

    EXTENSION_OVERRIDES_TYPE = ["cbz"]

    @staticmethod
    def file_type_from_extension(extension):
        if extension in FileTypeUtils.COMMON_IMAGE_EXTENSIONS:
            return FileType.IMAGE
        if extension in FileTypeUtils.COMMON_VIDEO_EXTENSIONS:
            return FileType.VIDEO
        if extension in FileTypeUtils.COMMON_AUDIO_EXTENSIONS:
            return FileType.AUDIO
        if extension in FileTypeUtils.COMMON_ARCHIVE_EXTENSIONS:
            return FileType.ARCHIVE

        return FileType.UNKNOWN

    @staticmethod
    def extension_overrides_type(extension):
        return extension in FileTypeUtils.EXTENSION_OVERRIDES_TYPE
