import os
import random
import hashlib
from sqlalchemy.engine import ResultProxy
from typing import List

class Utils():
    """Utility functions for FukurouViewer application

    """

    @staticmethod
    def convert_result(result: ResultProxy) -> List:
        return list(map(dict, result))

    @classmethod
    def convert_from_relative_path(cls, path: str = "") -> str:
        folder = os.path.dirname(__file__)
        return cls.norm_path(os.path.join(folder, path))

    @classmethod
    def base_path(cls, path: str = "") -> str:
        folder = os.path.dirname(os.path.abspath(__file__))
        return cls.norm_path(os.path.join(folder, path))
    
    @classmethod
    def fv_path(cls, path: str = "") -> str:
        return cls.norm_path(os.path.join("~/.fv", path))

    @staticmethod
    def norm_path(path: str) -> str:
        return os.path.normpath(os.path.expanduser(path))

    @staticmethod
    def generate_sha_hash(filepath: str) -> str:
        with open(filepath, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()

    @staticmethod
    def random_color() -> str:
        return "#%06x" % random.randint(0, 0xFFFFFF)
