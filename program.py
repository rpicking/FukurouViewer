import sys
import os
from enum import Enum

from PyQt5 import QtCore, QtGui, QtQml, QtWidgets


class Program(QtWidgets.QApplication):
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    QML_PATH = os.path.join(BASE_PATH, "qml")

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
		#check and create thumb dir
        self.setFont(QtGui.QFont(os.path.join(self.QML_PATH, "fonts/Lato-Regular.ttf")))
        self.engine = QtQml.QQmlApplicationEngine()
        self.engine.addImportPath(self.QML_PATH)
        self.engine.load(os.path.join(self.QML_PATH, "main.qml"))
        self.win = self.engine.rootObjects()[0]
        #SIGNALS FROM UI GO HERE
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.BASE_PATH, "icon.ico")))
        #load configs HERE
        self.win.show()


if __name__ == '__main__':
    app = Program(sys.argv)
    sys.exit(app.exec_())