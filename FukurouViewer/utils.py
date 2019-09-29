import os
import random
import hashlib
from sqlalchemy.engine import ResultProxy
from typing import List


class Utils:
    """Utility functions for FukurouViewer application

    """

    @staticmethod
    def convert_result(result: ResultProxy) -> List[dict]:
        return list(map(dict, result))

    @classmethod
    def convert_from_relative_path(cls, path: str = "") -> str:
        folder = os.path.dirname(__file__)
        return cls.norm_path(os.path.join(folder, path))

    @classmethod
    def base_path(cls, path: str = "") -> str:
        folder = os.path.dirname(os.path.abspath(__file__))
        return cls.norm_path(os.path.join(folder, path))
    
    @staticmethod
    def fv_path(path: str = "") -> str:
        return Utils.norm_path(os.path.join("~/.fv", path))

    @staticmethod
    def bin_path(path: str = "") -> str:
        return Utils.base_path(os.path.join("bin", path))

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

    # @staticmethod
    # def split_ex_url(url: str) -> list:
    #    pieces = url.rstrip('/').rsplit("/", 3)
    #    if pieces[1] == "g":
    #        return [int(pieces[1]), pieces[2]]
    #    split = pieces[3].split("-")
    #    return [int(split[0]), pieces[2], int(split[1])]

    @staticmethod
    def split_ex_url(url: str) -> dict:
        pieces = url.rstrip('/').rsplit("/", 3)
        if pieces[1] == "g":
            return {"type": "g", "gid": int(pieces[2]), "token": pieces[3]}
        split = pieces[3].split("-")
        return {"type": "s", 
                "page_token": pieces[2], 
                "gid": int(split[0]), 
                "page_number": int(split[1])}

    @staticmethod
    def merge_dicts(x: dict, y: dict) -> dict:
        z = x.copy()
        z.update(y)
        return z

    @staticmethod
    def seconds_to_ffmpeg_timestamp(total_seconds):
        total_seconds = total_seconds % (24 * 3600)
        hours = total_seconds // 3600
        total_seconds %= 3600
        minutes = total_seconds // 60
        total_seconds %= 60
        seconds = total_seconds
        return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
