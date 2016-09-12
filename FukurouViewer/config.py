import os
import json
from configparser import SafeConfigParser

import FukurouViewer
from FukurouViewer.utils import Utils



class Config(SafeConfigParser):

    SETTINGS_FILE = Utils.fv_path("settings.ini")

    SETTINGS = {
        "General": [
            "folders",
            "folder_options",
            "sort_type",
            "sort_direction",
            "confirm_delete",
            "size",
            "recent_imgs",
            "recent_galleries",
        ],
        "Archive": [
            "extract_zip",
            "extract_cbz",
            "extract_rar",
            "extract_cbr",
            "extract_7z",
            "extract_cb7",
            "delete_after_extract",
            "backup",
            "backup_dir",
        ],
        "Online": [
            "ex_member_id",
            "ex_pass_hash",
        ],    
    }
    
    AUTO_METADATA = "auto_metadata"
    INDIVIDUAL = "individual"
    FOLDER_OPTIONS = [
        "individual",
        "auto_metadata",
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
        if isinstance(folders, str):
            return [Utils.norm_path(folders).strip('"')]
        return [ Utils.norm_path(x).strip('"') for x in folders ]

    @folders.setter
    def folders(self, folder):
        self.set("General", "folders", json.dumps(folder, ensure_ascii=False))

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