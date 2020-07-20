from PySide2 import QtWidgets, QtGui, QtCore
from sqlalchemy import select

from FukurouViewer import user_database, Utils


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, _program, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        self.program = _program
        self.menu = QtWidgets.QMenu(parent)
        self.exitAction = QtWidgets.QAction('&Exit', self)
        self.createMenu()

        self.last = None
        self.clickTimer = QtCore.QTimer(self)
        self.clickTimer.setSingleShot(True)
        self.clickTimer.timeout.connect(self.singleClick)
        self.activated.connect(self.onTrayIconActivated)

    def createMenu(self):
        with user_database.get_session(self, acquire=True) as session:
            results = Utils.convert_result(session.execute(
                select([user_database.Folders]).order_by(user_database.Folders.order)))

        for folder in results:
            name = folder.get("name")
            uid = folder.get("uid")
            path = folder.get("path")
            item = FolderMenuItem(self, name, path, uid)
            self.menu.addAction(item)

        self.menu.addSeparator()
        openMenu = QtWidgets.QAction("Open", self)
        openMenu.setStatusTip("Open Application")
        openMenu.triggered.connect(self.openApp)
        self.menu.addAction(openMenu)

        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.program.quit)
        self.menu.addAction(self.exitAction)
        self.setContextMenu(self.menu)
        self.setToolTip("Fukurou Viewer")

    def openApp(self):
        self.program.open("APP")

    def onTrayIconActivated(self, event):
        if event == QtWidgets.QSystemTrayIcon.Trigger:
            self.last = "Click"
            self.clickTimer.start(self.program.doubleClickInterval())
        elif event == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.doubleClick()

    def singleClick(self):
        if self.last != "Click":
            return
        self.program.open()

    def doubleClick(self):
        self.last = "DoubleClick"
        self.program.close()
        self.program.open("APP")


class FolderMenuItem(QtWidgets.QAction):
    def __init__(self, parent, _name, _path, _uid):
        super().__init__(_name, parent)
        self.name = _name
        self.uid = _uid
        self.path = _path
        self.triggered.connect(self.openFolder)

    def openFolder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(Utils.norm_path(self.path)))
