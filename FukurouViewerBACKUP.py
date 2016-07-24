import os, sys

from shutil import copy2

from PyQt5 import QtGui, QtCore, QtMultimedia, QtWidgets


# Fukurou Viewer
# Class for displaying images in a folder 
# Currently only sorts by name
# Constructor takes folder path
# FORMATS: bmp gif jpg jpeg png pbm pgm ppm xbm xpm
class Image(QtWidgets.QMainWindow):
    MaxRecentImgs = 15
    validImageFormats = "Images (*.jpg *.jpeg *.png *.gif *.bmp *.pbm *.pgm *ppm *.xbm *.xpm)"
    validVideoFormats = ""

    def __init__(self):
        super().__init__()
        maxRecentImgs = 10
        maxRecentComics = 5
        self.settings = QtCore.QSettings("Settings.ini", QtCore.QSettings.IniFormat)

        self.recentImgActs = []
        for i in range(Image.MaxRecentImgs):
            self.recentImgActs.append(QtWidgets.QAction(self, visible=False, triggered=self.changeImage))

        recentImgs = []
        if self.settings.value("RecentImages") != None:
            recentImgs = self.settings.value("RecentImages")
        
        #self.recentComics = []
        #if self.settings.value("RecentComics") != None:
         #   self.recentComics = self.settings.value("RecentComics") 

        self.setupWindow()
        self.refreshImg()
        self.home()


    # Quit button
    def home(self):        
        recentImgs = []
        if self.settings.value("RecentImages") != None:
            recentImgs = self.settings.value("RecentImages")

        #------MENU BAR---------
        open = QtWidgets.QAction("&Open", self)
        open.setShortcut("Ctrl+O")
        open.setStatusTip("Open new file")
        open.triggered.connect(self.openFile)

        recentComic = QtWidgets.QMenu("&Recent Series", self)
        recentComic.setStatusTip('Recently viewed comics')

        recentImg = QtWidgets.QMenu("&Recent Images", self)
        recentImg.setStatusTip("Recently viewed images")

        for i in range(Image.MaxRecentImgs):
            recentImg.addAction(self.recentImgActs[i])

        clearRecentImgs = QtWidgets.QAction("Clear Recent Images", self, triggered=self.removeAllRecentImgs)
        recentImg.addSeparator()
        recentImg.addAction(clearRecentImgs)
        self.updateRecentActions()        

        closeBar = QtWidgets.QAction("&Close Application", self)
        closeBar.setShortcut("Ctrl+Q")
        closeBar.setStatusTip('Leave the Application')
        closeBar.triggered.connect(self.closeApplication)    

        changeFav = QtWidgets.QAction("Change Favorite Folder", self)
        changeFav.triggered.connect(self.changeFavFolder)

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(open)
        fileMenu.addMenu(recentImg)
        fileMenu.addMenu(recentComic)
        fileMenu.addAction(changeFav)
        fileMenu.addAction(closeBar)

        #------TOOL BAR--------- (ICONS)       
        closeAction = QtWidgets.QAction(QtGui.QIcon('Icon.png'), 'Quit Application', self)
        closeAction.triggered.connect(self.closeApplication)

        self.toolBar = self.addToolBar("Close")
        self.toolBar.addAction(closeAction)
        self.toolBar.setAutoFillBackground(True)
        self.toolBar.setMovable(False)

        #btn.show()


    def closeApplication(self):
        #trayIcon = QtWidgets.QSystemTrayIcon(self)
        #trayIcon.setIcon(QtGui.QIcon('Icon2.png'))
        #trayIcon.setVisible(True)
        #trayIcon.show()
        #self.hide()

        sys.exit()


    # button press event
    def keyPressEvent(self, event):
        key = event.key()
        
        if(key == QtCore.Qt.Key_Left):
            self.decrement()
        elif(key == QtCore.Qt.Key_Right):
            self.increment()
        elif(key == QtCore.Qt.Key_Delete):
            choice = QtGui.QMessageBox.question(self, "Delete Image", "Are you sure you want to delete this?", 
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if choice == QtGui.QMessageBox.Yes:
                print("delete file")
            else:
                print("don't delete")

    # event for mouse wheel
    def wheelEvent(self, event):
        if(event.angleDelta().y() > 0):
            self.decrement()
        elif(event.angleDelta().y() < 0):
            self.increment()

    
    def mousePressEvent(self, event):
        if(event.button() == QtCore.Qt.RightButton):
            if(self.label.underMouse()):
                menu = QtWidgets.QMenu(self)
                fav = QtWidgets.QAction(self)
                if self.path == self.favFolder:
                    fav.setText("Already in Favorites")
                else:
                    fav.setText("Add to Favorites")
                    fav.triggered.connect(self.addFavorite)
                menu.addAction(fav)
                menu.popup(QtGui.QCursor.pos())
    

    # updates items in "folder list" imgList
    def refreshList(self, path):
        self.imgList = []
        self.path = path
        for file in os.listdir(self.path):
            ext = os.path.splitext(file)[1]
            if(self.formatCheck(ext)):   #if valid format
                self.imgList.append(os.path.join(self.path, file))
        self.last = len(self.imgList) - 1
        self.count = 0
        self.sortDate()
        


    def formatCheck(self, ext):
        if(ext in [".bmp", ".gif", ".jpg", ".jpeg", ".png", ".pbm", ".pgm", ".ppm", ".xbm", ".xpm"]):
            return True
        return False


    #initialize window and label
    def setupWindow(self):
        self.setWindowTitle("Fukurou Viewer")
        self.setWindowIcon(QtGui.QIcon('Icon.png'))
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.show()
        QtGui.QGuiApplication.processEvents()

        self.label = QtWidgets.QLabel()
        self.label.setMargin(5)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(self.label)

        #background color
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.black)
        self.setPalette(p)
        self.changeFavFolder(True)


    # Changes images 
    # Only call when new image to load
    def refreshImg(self):
        recentImgs = []
        if self.settings.value("RecentImages") != None:
            recentImgs = self.settings.value("RecentImages")

        try:
            recentImgs.remove(self.imgList[self.count])
        except ValueError:
            pass
        recentImgs.insert(0, self.imgList[self.count])
        del recentImgs[Image.MaxRecentImgs:]

        self.settings.setValue("RecentImages", recentImgs)
        #self.settings.setValue("RecentComics", recentComics)
        
        image = QtGui.QImageReader(self.imgList[self.count])
        image.setAutoDetectImageFormat(True)
        imageFormat = str(image.format())

        self.setWindowTitle("Fukurou Viewer - " + self.imgList[self.count] + " ::: " + imageFormat)
        ext = os.path.splitext(self.imgList[self.count])[1]
        if(ext == ".gif"):
            self.label.setMovie(QtGui.QMovie(self.imgList[self.count]))
            self.label.movie().start()
        else: #standard image
            geometrya = self.geometry()
            geometry = self.label.geometry()
            height = self.height()
            self.image = QtGui.QImage(self.imgList[self.count])
            if (self.image.height() > (self.label.height() - (2 * self.label.margin()))):
                self.image = self.image.scaledToHeight(self.label.height() - (2 * self.label.margin()), QtCore.Qt.SmoothTransformation)
            self.label.setPixmap(QtGui.QPixmap.fromImage(self.image))

        self.label.repaint()
        self.updateRecentActions()


    # Updates actions in menu (recent images, etc)
    def updateRecentActions(self):
        recentImgs = []
        if self.settings.value("RecentImages") != None:
            recentImgs = self.settings.value("RecentImages")

        for i in range(len(recentImgs)):
            text = recentImgs[i]
            self.recentImgActs[i].setText(text)
            self.recentImgActs[i].setData(text)
            self.recentImgActs[i].setVisible(True)

        for j in range(len(recentImgs), Image.MaxRecentImgs):
            self.recentImgActs[j].setVisible(False)
       

    # Open file function for button
    def openFile(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setNameFilter(Image.validImageFormats)
        filename, filter = dialog.getOpenFileName(self, "Open File", self.path, Image.validImageFormats)
        if filename:
            self.refreshList(os.path.dirname(os.path.realpath(filename)))
            self.count = self.imgList.index(os.path.abspath(filename))
            self.refreshImg()


    # Raises index of image list
    def increment(self):
        if(self.count == self.last):
            self.count = 0
        else:
            self.count += 1
        self.refreshImg()


    # Lowers index of image list
    def decrement(self):
        if (self.count == 0):
            self.count = self.last
        else:
            self.count -= 1
        self.refreshImg()

    # Change to specific image
    def changeImage(self):
        action = self.sender()
        if action:
            newDir = os.path.dirname(os.path.realpath(action.data()))
            if newDir != self.path:
                if os.path.isdir(newDir):
                    self.refreshList(newDir)
                    self.count = self.imgList.index(action.data())
                else:
                    self.removeRecentImgs()
            else:
                self.count = self.imgList.index(action.data())
            self.refreshImg()


    # Removes all non existing Images from Recent list
    def removeRecentImgs(self):
        recentImgs = self.settings.value("RecentImages")
        for item in recentImgs[:]:
            if not os.path.isfile(item):
                recentImgs.remove(item)
        self.settings.setValue("RecentImages", recentImgs)
        self.updateRecentActions()
        

    # Removes all images from recent list
    def removeAllRecentImgs(self):
        recentImgs = []
        self.settings.setValue("RecentImages", recentImgs)
        self.updateRecentActions()
        

    # change favorites folder
    def changeFavFolder(self, first):
        if first:
            if self.settings.value("FavoritesFolder") == None:
                dialog = QtWidgets.QFileDialog(self)
                path = os.path.abspath(dialog.getExistingDirectory(self, "Favorites Folder"))
                self.settings.setValue("FavoritesFolder", path)
            else:
                path = self.settings.value("FavoritesFolder")
        else:
            dialog = QtWidgets.QFileDialog(self)
            path = os.path.abspath(dialog.getExistingDirectory(self, "Favorites Folder"))
            self.settings.setValue("FavoritesFolder", path)
        
        self.favFolder = path
        self.refreshList(path)
        self.refreshImg()


    # Adds copy of currently viewed image to favorites folder
    def addFavorite(self):
        file = self.imgList[self.count]
        testname = os.path.basename(file)
        basename, ext = os.path.splitext(testname)
        newName = self.uniqueFileName(basename, ext, testname, 0)
        copy2(file , os.path.join(self.favFolder, newName))


    # Returns unused filename in favorite folder (number starts at 0
    def uniqueFileName(self, basename, ext, testname, number):
        if os.path.isfile(os.path.join(self.favFolder, testname)):
            number += 1
            testname = basename + "(" + str(number) + ")" + ext
            return self.uniqueFileName(basename, ext, testname, number)
        else:
            return testname


    # Sorts by file date modified
    def sortDate(self):
        self.imgList.sort(key=lambda x: os.stat(x).st_mtime, reverse=True)

    
    # Sorts by format
    def sortExt(self):
        self.imgList.sort(key=lambda x: os.path.splitext(x)[1])


    # Sorts by name
    def sortName(self):
        self.imgList.sort()


    # sort by size
    def sortSize(self):
        self.imgList.sort(key=lambda x: os.stat(x).st_size, reverse=True)


def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = Image()
    gui.show()
    sys.exit(app.exec_())


main()