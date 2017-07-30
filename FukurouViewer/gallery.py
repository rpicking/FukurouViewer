from .utils import Utils
from .logger import Logger
from .config import Config


class GenericGallery(Logger):
    IMAGE_WIDTH = 200
    IMAGE_HEIGHT = 280
    id = None
    title = ""
    romanji_title = ""
    origin_title = ""
    time_added = None
    last_modified = None
    site_rating = None
    user_rating = None
    rating_count = 5
    total_size = 0
    file_count = 0
    url = None
    virtual = None
