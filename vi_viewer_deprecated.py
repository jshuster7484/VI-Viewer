import re
import sys
import time
from PyQt4 import QtGui, QtCore
import win32gui
import win32con
import win32ui
from PIL import Image
from ctypes import windll
import functools


enum_windows = []


# http://stackoverflow.com/questions/24106903/resizing-qpixmap-while-maintaining-aspect-ratio/24114974
class ImageLabel(QtGui.QLabel):
    def __init__(self, img):
        super(ImageLabel, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.pixmap = QtGui.QPixmap(img)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

    def paintEvent(self, event):
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0,0)
        scaledPix = self.pixmap.scaled(size, QtCore.Qt.KeepAspectRatio, transformMode = QtCore.Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaledPix.width())/2)
        point.setY((size.height() - scaledPix.height())/2)
        #print point.x(), ' ', point.y()
        painter.drawPixmap(point, scaledPix)

    #def resizeEvent(self, *args, **kwargs):


class AutoScalingPixmapLabel(QtGui.QLabel):
    """
    Extension of QLabel that automatically scales the QPixmap image it contains as it is resized.
    Translated from C++ code posted by StackOverflow user phyatt at http://stackoverflow.com/a/22618496/3300060.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(100)
        self._pixmap = None
        #self.text_label = QtGui.QLabel(self)
        #self.text_label.setText("TEST")
        #self.text_label.move(100, 100)
        #self.text_label.show()

    def setPixmap(self, pixmap, *args, **kwargs):
        self._pixmap = pixmap
        super().setPixmap(pixmap, *args, **kwargs)
        self.resizeEvent()  # Calling self.resize doesn't seem to trigger the event, so do it explicitly

    def heightForWidth(self, width, *args, **kwargs):
        return self._pixmap.height() * width / self._pixmap.width()

    def sizeHint(self, *args, **kwargs):
        width = self.width()
        size = QtCore.QSize(width, self.heightForWidth(width))
        return size

    def resizeEvent(self, *args, **kwargs):
        rescaled_pixmap = self._pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio,
                                              QtCore.Qt.SmoothTransformation)
        super().setPixmap(rescaled_pixmap)


        #print(self.size())
        #print(rescaled_pixmap.rect())
        #print(rescaled_pixmap.rect())
        #self.text_label.move(rescaled_pixmap.rect().x(), rescaled_pixmap.rect().top())

    def getPixmapHeight(self):
        return self.pixmap.height()

    def getPixmapWidth(self):
        return self.pixmap.width()


# https://github.com/Werkov/PyQt4/blob/master/examples/layouts/flowlayout.py
class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.maximumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


class ViWidget(QtGui.QWidget):

    def __init__(self, name, image, parent=None):
        super(ViWidget, self).__init__(parent)

        self.name = name
        self.image = image

        # Get rid of?
        self.displayed = False

        self.name_label = QtGui.QLabel(name)
        self.name_label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.name_label.setAlignment(QtCore.Qt.AlignBottom)

        self.close_button = QtGui.QPushButton("X")
        #self.close_button.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        # self.close_button.connect()
        #self.close_button.setAlignment(QtCore.Qt.AlignBottom)

        self.header_layout = QtGui.QHBoxLayout()
        self.header_layout.addWidget(self.name_label)
        self.header_layout.addWidget(self.close_button)

        #self.image_label = ImageLabel(image)

        self.image_label = AutoScalingPixmapLabel()
        pixmap = QtGui.QPixmap(image)
        self.image_label.setPixmap(pixmap)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(self.header_layout)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

if False:
    for item in list:
        if re.search(r'.vi Front Panel', item[1]):
            print(item)
            rect = win32gui.GetWindowRect(item[0])
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            win32gui.ShowWindow(item[0], win32con.SW_RESTORE)
            win32gui.SetActiveWindow(item[0])
            win32gui.SetForegroundWindow(item[0])
            # gui.SetWindowPos(item[0], win32con.HWND_TOP, 0, 0, width, height, win32con.SWP_SHOWWINDOW)
        if re.search(r'.vi Block Diagram', item[1]):
            print(item)
            rect = win32gui.GetWindowRect(item[0])
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            win32gui.ShowWindow(item[0], win32con.SW_RESTORE)
            win32gui.SetActiveWindow(item[0])
            win32gui.SetForegroundWindow(item[0])
            # gui.SetWindowPos(item[0], win32con.HWND_NOTOPMOST, 100, 100, width, height, win32con.SWP_SHOWWINDOW)


def enum_callback(hwnd, vi_dict):
    window_text = win32gui.GetWindowText(hwnd)
    global enum_windows
    if re.search(r'.vi (Front Panel|Block Diagram)', window_text):
        enum_windows.append(window_text)
        if window_text not in vi_dict:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Saves a copy of the image!
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)

            saveDC.SelectObject(saveBitMap)

            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)

            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)

            if result == 1:
                # PrintWindow Succeeded
                image_name = "test_{0}.png".format(hwnd)
                im.save(image_name)

            # If the vi is not in the dictionary, add it.
            if window_text not in vi_dict:
                vi_widget = ViWidget(window_text, image_name)
                vi_dict[vi_widget.name] = vi_widget


def update_vi_dict(vi_dict, layout):
    global enum_windows
    win32gui.EnumWindows(enum_callback, vi_dict)
    keys_to_remove = []
    for name in vi_dict.keys():
        if not vi_dict[name].displayed:
            # This way of adding widgets adds them alphabetically
            layout.addWidget(vi_dict[name])
        if name not in enum_windows:
            print(name)
            keys_to_remove.append(name)
    for key in keys_to_remove:
        vi_dict[key].deleteLater()
        del vi_dict[key]
    enum_windows = []


def main():
    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    layout = QtGui.QHBoxLayout(w)

    vi_dict = dict()
    win32gui.EnumWindows(enum_callback, vi_dict)
    update_vi_dict(vi_dict, layout)

    # Update list of vis every second
    timer = QtCore.QTimer()
    timer.start(1000)
    timer.timeout.connect(functools.partial(update_vi_dict, vi_dict, layout))

    #w.resize(800, 600)
    #w.move(300, 300)
    w.setWindowTitle('VI Viewer')
    w.show()
    #w.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
