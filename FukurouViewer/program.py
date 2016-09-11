import os
import sys
from enum import Enum
from threading import RLock

try:
    from .utils import Utils
    from .config import Config
    from .search import Search
#except Exception: #ImportError workaround for vs
#    from utils import Utils
#    from config import Config
#    from search import Search

from PyQt5 import QtCore, QtGui, QtQml, QtWidgets



class Program(QtWidgets.QApplication):
    BASE_PATH = Utils.base_path()
    QML_DIR = os.path.join(BASE_PATH, "qml")
    THUMB_DIR = Utils.fv_path("thumbs")
    gallery_lock = RLock()

    class SortMethodMap(Enum):
        NameSort = "sort_name"
        ArtistSort = "sort_artist"
        ReadCountSort = "read_count"
        LastReadSort = "last_read"
        RatingSort = "sort_rating"
        DateAddedSort = "sort_date"
        TagSort = "sort_tag"

    def __init__(self, args):
        super().__init__(args)
        self.setApplicationName("FukurouViewer")
        self.setup()
    
    def setup(self):
        if not os.path.exists(self.THUMB_DIR):
            os.makedirs(self.THUMB_DIR)        
        
        self.setFont(QtGui.QFont(os.path.join(self.QML_DIR, "fonts/Lato-Regular.ttf")))
        self.engine = QtQml.QQmlApplicationEngine()
        self.engine.addImportPath(self.QML_DIR)
        self.engine.load(os.path.join(self.QML_DIR, "main.qml"))
        self.win = self.engine.rootObjects()[0]

        #------------
        #SIGNALS FROM UI GO HERE
        #------------

        self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))

        #load configs HERE
        Search.search_ex_gallery()
        self.win.show()



#if __name__ == '__main__':
#    app = Program(sys.argv)
#    sys.exit(app.exec_())