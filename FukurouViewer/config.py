import os
import json
from configparser import ConfigParser

from .utils import Utils


class Config(ConfigParser):
    """Configs for FukurouViewer application

    """

    SETTINGS_FILE = Utils.base_path("settings.ini")

    SETTINGS = {
        "General": [
            {"appData": "~/.fv"},
            {"close": "tray"},
            "doujin_downloader",
        ],
        "Online": [
            "ex_member_id",
            "ex_pass_hash",
        ],
    }
    # name
    FOLDER_OPTIONS = [
        "uid",
        "path",
        "order"
    ]

    def __init__(self):
        super().__init__()
        try:
            self.load()
        except FileNotFoundError:
            self.save()

        self.build()
        self.save()

    def build(self):
        for section in self.SETTINGS:
            if not self.has_section(section):
                self.add_section(section)
            for option in self.SETTINGS.get(section):                
                if type(option) is dict:
                    option_key = next(iter(option))
                else:
                    option_key = option
                if not self.has_option(section, option_key):
                    value = ""
                    if isinstance(option, dict):
                        value = option.get(option_key, "")
                    self.set(section, option_key, value)

    def set(self, section, option, value=None):
        super().set(section, option, value)
        self.save()

    def save(self):
        with open(self.SETTINGS_FILE, "w+", encoding="utf-8") as f:
            self.write(f)

    def load(self):
        with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.read_file(f)

    def fv_path(self, path: str = ""):
        return os.path.abspath(Utils.norm_path(os.path.join(self.appData, path)))

    @property
    def appData(self) -> str:
        return self.get("General", "appData")

    @appData.setter
    def appData(self, path):
        self.set("General", "appData", path)
        self.save()

    @property
    def close(self):
        return self.get("General", "close")

    @close.setter
    def close(self, close_type):
        self.set("General", "close", close_type)
        self.save()

    @property
    def folders(self):
        folders = self.get("General", "folders") or "[]"
        return list(map(Utils.norm_path, json.loads(folders)))

    @folders.setter
    def folders(self, folder):
        self.set("General", "folders", json.dumps(folder, ensure_ascii=False))
        self.save()

    @property
    def folder_options(self):
        options = self.get("General", "folder_options") or "{}"
        return json.loads(options)

    @folder_options.setter
    def folder_options(self, value):
        self.set("General", "folder_options", json.dumps(value, ensure_ascii=False))

    @property
    def doujin_downloader(self) -> str:
        return self.get("General", "doujin_downloader")

    @doujin_downloader.setter
    def doujin_downloader(self, value):
        value = Utils.norm_path(value)
        self.set("General", "doujin_downloader", value)

    @property
    def ex_member_id(self):
        return self.get("Online", "ex_member_id")

    @ex_member_id.setter
    def ex_member_id(self, id):
        self.set("Online", "ex_member_id", str(id))

    @property
    def ex_pass_hash(self):
        return self.get("Online", "ex_pass_hash")
    
    @ex_pass_hash.setter
    def ex_pass_hash(self, hash):
        self.set("Online", "ex_pass_hash", str(hash))


Config = Config()
