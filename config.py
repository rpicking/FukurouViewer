from configparser import SafeConfigParser

try:
    from .utils import Utils
except Exception: #ImportError workaround for vs
    from utils import Utils

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
        print("HERE")
        try:
            self.load()
        except FileNotFoundError:
            print("WTF")
            self.save()
        self.build()
        self.save()

    def build(self):
        print("BUILDING")
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