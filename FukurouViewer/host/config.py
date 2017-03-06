import os
import json
from configparser import SafeConfigParser

from utils import Utils


class Config(SafeConfigParser):
    """Configs for FukurouViewer host application

    """

    SETTINGS_FILE = "settings.ini"

    SETTINGS = {
        "General": [
            "folders",
            "folder_options",
        ],
    }
    # uid
    FOLDER_OPTIONS = [
        "name",
        "path",
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
                if not self.has_option(section, option):
                    self.set(section, option, "")

    def save(self):
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            self.write(f)

    def load(self):
        with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.read_file(f)

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


Config = Config()
