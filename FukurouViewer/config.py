import os
import json
from configparser import ConfigParser

from .utils import Utils


class Config(ConfigParser):
    """Configs for FukurouViewer application

    """

    SETTINGS_FILE = Utils.fv_path("settings.ini")

    SETTINGS = {
        "General": [
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
        self.set_defaults()
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

    def set_defaults(self):
        self.close = "tray"

    def save(self):
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            self.write(f)

    def load(self):
        with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.read_file(f)

    @property
    def close(self):
        return self.get("General", "close")

    @close.setter
    def close(self, type):
        self.set("General", "close", type)

    @property
    def folders(self):
        folders = self.get("General", "folders") or "[]"
        return list(map(Utils.norm_path, json.loads(folders)))

    @folders.setter
    def folders(self, folder):
        self.set("General", "folders", json.dumps(folder, ensure_ascii=False))

    @property
    def folder_options(self):
        options = self.get("General", "folder_options") or "{}"
        return json.loads(options)

    @folder_options.setter
    def folder_options(self, value):
        self.set("General", "folder_options", json.dumps(value, ensure_ascii=False))

    @property
    def doujin_downloader(self):
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
