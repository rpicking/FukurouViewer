import os

class Utils():
    """Utility functions for FukurouViewer host application

    """

    @classmethod
    def base_path(cls, path: str = "") -> str:
        return os.path.dirname(os.path.abspath(__file__));

    @staticmethod
    def norm_path(path: str) -> str:
        return os.path.normpath(os.path.expanduser(path))
