import os
import hashlib

class Utils():

    @classmethod
    def base_path(cls, path: str = "") -> str:
        return os.path.dirname(os.path.abspath(__file__));
    
    @classmethod
    def fv_path(cls, path: str = "") -> str:
        return cls.norm_path(os.path.join("~/.fv", path))

    @staticmethod
    def norm_path(path: str) -> str:
        return os.path.normpath(os.path.realpath(os.path.expanduser(path)))

    @classmethod
    def generate_sha_hash(cls, filepath) -> str:
        with open(filepath, 'rb') as f:
            return hashlib.sha1(f.read()).hexdigest()
