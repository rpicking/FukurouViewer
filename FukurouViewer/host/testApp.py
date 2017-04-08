from PyQt5 import QtCore, QtWidgets, QtGui

from . import testThread
from .config import Config

class testProgram(QtWidgets.QApplication):
    def __init__(self, args):
        super().__init__(args)

    def setup(self):
        self.w = QtWidgets.QWidget()
        self.trayIcon = SystemTrayIcon(QtGui.QIcon("../icon.ico"), self.w)
        self.trayIcon.show()
        self.trayIcon.exitAction.triggered.connect(self.quit)

    def exec_(self):
        return super().exec_()

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QtWidgets.QMenu(parent)
        self.exitAction = QtWidgets.QAction('&Exit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)
