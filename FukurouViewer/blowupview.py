from collections import namedtuple

from PySide2 import QtCore

Coordinate = namedtuple("Coordinate", "x y")


class BlowUpItem(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._x = 0
        self._y = 0
        self.startPoint = Coordinate(0, 0)
        self.anchorPosition = Coordinate(0, 0)  # top left point for thumbnail

        self.width = 0
        self.height = 0
        self.x_ratio = 0
        self.y_ratio = 0

    def initItem(self, _start_point, thumb_width, thumb_height, item_width, item_height, xPercent, yPercent):
        self.startPoint = Coordinate(_start_point.x(), _start_point.y())

        self._x = self.startPoint.x - (item_width * xPercent)
        self._y = self.startPoint.y - (item_height * yPercent)
        self.anchorPosition = Coordinate(self._x, self._y)

        self.width = item_width
        self.height = item_height
        self.x_ratio = int(item_width / thumb_width)
        self.y_ratio = int(item_height / thumb_height)

        self.on_postion_change.emit()

    def movePosition(self, mouseX, mouseY):
        deltaX = self.startPoint.x - mouseX
        deltaY = self.startPoint.y - mouseY

        self._x = self.anchorPosition.x + (deltaX * self.x_ratio)
        self._y = self.anchorPosition.y + (deltaY * self.y_ratio)
        self.on_postion_change.emit()

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    on_postion_change = QtCore.Signal()
    x = QtCore.Property(int, get_x, notify=on_postion_change)
    y = QtCore.Property(int, get_y, notify=on_postion_change)
