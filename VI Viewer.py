import re
import sys
import time
from PyQt4 import QtGui, QtCore
import win32gui
import win32con
import win32ui
from PIL import Image
from ctypes import windll


# Get explicit something.vi string
# doesnt work with lvlibs and classes
def get_vi_name(string):
    if 'lvclass' in string:
        result = re.search(r'lvclass:(.*).vi', string)
        return result.group(1) + '.vi'

    # vi inside of lvlib but not class?
    else:
        return string.split('.vi')[0] + '.vi'



def get_proj_name(string):
    return string.split('.lvproj')[0] + '.lvproj'


def get_image(hwnd):
    minimized_window = False
    if win32gui.IsIconic(hwnd):
        minimized_window = True
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)

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

    # if minimized_window:
    # win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, left, top, width, height, win32con.SWP) # Can't find window after
    # win32gui.ShowWindow(hwnd, win32con.SW_SHOWMINNOACTIVE)
    # win32gui.ShowWindow(hwnd, win32con.SW_

    return image_name





    """"
    win32gui.EnumWindows(get_windows_callback)
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
    fp_windows = []
    bd_windows = []
    lvproj_windows = []
    """


class ViViewerApp(QtGui.QWidget):
    # TODO: BUG: VI Viewer can not close correctly and have its process stay open.
    def __init__(self):
        super(ViViewerApp, self).__init__()
        self.vi_dict = dict()
        self.fp_windows = []
        self.bd_windows = []
        self.proj_dict = dict()
        self.proj_windows = []
        self.preview = True
        self.line_edit = QtGui.QLineEdit()

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.createSearchBar()
        self.createMenuBar()
        self.proj_layout = QtGui.QVBoxLayout()
        self.layout.addLayout(self.proj_layout)
        self.layout.addWidget(QtGui.QLabel(), 1) # Adding this label moves everything up, I don't know
        self.layout.setMenuBar(self.menuBar)

        win32gui.EnumWindows(self.get_windows_callback, self.vi_dict)
        self.update_vi_dict()
        # Update list of vis every second
        timer = QtCore.QTimer(self)
        timer.start(1000)
        timer.timeout.connect(self.update_vi_dict)

        self.setWindowTitle('VI Viewer')
        icon = QtGui.QIcon("vi_viewer_icon.png")
        self.setWindowIcon(icon)
        self.showMaximized()

    def createMenuBar(self):
        self.menuBar = QtGui.QMenuBar()
        self.optionsMenu= QtGui.QMenu("&Options", self)
        self.someAction = self.optionsMenu.addAction("A&ction")
        self.menuBar.addMenu(self.optionsMenu)

        #self.someAction.triggered.connect()


    def createSearchBar(self):
        search_widget = QtGui.QWidget()
        search_layout = QtGui.QVBoxLayout()
        search_layout.addWidget(QtGui.QLabel("Search:"))
        search_layout.addWidget(self.line_edit)
        self.line_edit.textChanged.connect(self.search)
        search_widget.setLayout(search_layout)
        search_widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.layout.addWidget(search_widget)

    def search(self):
        for name in self.vi_dict.keys():
            if self.line_edit.text() not in self.vi_dict[name].vi_name:
                self.vi_dict[name].hide()
            else:
                self.vi_dict[name].show()


    # Sort window hwnds into Front Panel, Block Diagram, or lvproj dictionaries
    def get_windows_callback(self, hwnd, vi_dict):
        window_name = win32gui.GetWindowText(hwnd)
        if re.search(r'Front Panel', window_name):
            vi_name = get_vi_name(window_name)
            self.addViWidget(window_name, self)
            vi_dict[vi_name].setFPhwnd(hwnd)
            self.fp_windows.append(vi_name)

        if re.search(r'Block Diagram', window_name):
            vi_name = get_vi_name(window_name)
            self.addViWidget(window_name, self)
            vi_dict[vi_name].setBDhwnd(hwnd)
            self.bd_windows.append(vi_name)

        if re.search(r'Project Explorer', window_name):
            proj_name = get_proj_name(window_name)
            self.addLVProjWidget(window_name, hwnd, self)
            self.proj_windows.append(proj_name)

    def update_vi_dict(self):
        win32gui.EnumWindows(self.get_windows_callback, self.vi_dict)
        projects_to_remove = []
        for project_name in self.proj_dict.keys():
            self.proj_layout.addWidget(self.proj_dict[project_name])

            if project_name not in self.proj_windows:
                projects_to_remove.append(project_name)

        for project in projects_to_remove:
            self.proj_dict[project].deleteLater()
            del self.proj_dict[project]

        keys_to_remove = []
        for vi_name in self.vi_dict.keys():
            project_name = self.vi_dict[vi_name].project
            if project_name in self.proj_dict.keys():

                self.proj_dict[project_name].add_vi(self.vi_dict[vi_name])
            # TODO: ELSE ADD TO LOOSE VIs?

            if vi_name not in self.bd_windows:
                self.vi_dict[vi_name].hideBlockDiagram()
            else:
                self.vi_dict[vi_name].showBlockDiagram()

            if vi_name not in self.fp_windows:
                self.vi_dict[vi_name].close()
                keys_to_remove.append(vi_name)



        for key in keys_to_remove:
            self.vi_dict[key].deleteLater()
            del self.vi_dict[key]

        self.fp_windows = []
        self.bd_windows = []
        self.proj_windows = []


    def addViWidget(self, window_name, app):
        vi_name = get_vi_name(window_name)
        if not self.vi_dict.get(vi_name):
            vi_widget = ViWidget(vi_name, window_name, app)
            self.vi_dict[vi_name] = vi_widget

    def addLVProjWidget(self, window_name, hwnd, app):
        proj_name = get_proj_name(window_name)
        if not self.proj_dict.get(proj_name):
            proj_widget = LVProjWidget(window_name, hwnd, app)
            self.proj_dict[proj_name] = proj_widget


class ProjectLabel(QtGui.QLabel):
    def __init__(self, text, hwnd):
        super(ProjectLabel, self).__init__()
        self.text = text
        self.hwnd = hwnd
        self.setText(text)
        font = QtGui.QFont()
        font.setPixelSize(15)
        self.setFont(font)
        #self.setStyleSheet("background-color: rgb(255,255,255); margin:5px; ")
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet("background-color: rgb(255,255,255);")

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet("")

    def mousePressEvent(self, QMouseEvent):
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)  # Use to maximize the window
        win32gui.SetForegroundWindow(self.hwnd)  # Won't maximize the window
        sys.exit(0)

class LVProjWidget(QtGui.QWidget):
    def __init__(self, window_name, hwnd, app, parent=None):
        super(LVProjWidget, self).__init__(parent)
        self.proj_vis = []
        self.window_name = window_name
        self.hwnd = hwnd
        self.app = app
        self.proj_name = get_proj_name(window_name)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        self.name_label = ProjectLabel(self.proj_name, self.hwnd)
        #self.name_label.setText(self.proj_name)
        #font = QtGui.QFont()
        #font.setPixelSize(15)
        #self.name_label.setFont(font)

        self.vi_layout = QtGui.QHBoxLayout()

        self.widget_layout = QtGui.QVBoxLayout()
        self.widget_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.widget_layout.addWidget(self.name_label)
        self.widget_layout.addLayout(self.vi_layout)

        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)

        self.widget_layout.addWidget(line)
        self.setLayout(self.widget_layout)

    def add_vi(self, vi_widget):
        self.vi_layout.addWidget(vi_widget)

    def remove_vi(self, vi_widget):
        self.vi_layout.removeWidget(vi_widget)


class ViWidget(QtGui.QWidget):

    def __init__(self, vi_name, window_name, app, parent=None):
        # window_name could be either Front Panel or Block Diagram
        super(ViWidget, self).__init__(parent)

        self.vi_name = vi_name
        self.app = app
        # What is the correct way to init null object values?
        self.fp_hwnd = ""
        self.bd_hwnd = ""
        self.bd_pixmap = ""
        self.fp_pixmap = ""

        self.vi_name = vi_name
        self.window_name = window_name
        self.project = ""
        result = re.search(r' on (.*)\/', self.window_name)
        if result.group(1):
            self.project = result.group(1)

        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

        # Get rid of?
        self.displayed = False

        self.name_label = QtGui.QLabel(self.vi_name)
        # self.name_label.setAlignment(QtCore.Qt.AlignBottom)
        # self.name_label.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)

        if self.project:
            self.project_label = QtGui.QLabel(self.project)

        self.close_button = QtGui.QToolButton()
        self.close_button.setIcon(QtGui.QApplication.style().standardIcon(QtGui.QStyle.SP_DialogCloseButton))
        self.close_button.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.close_button.clicked.connect(self.close_vi)

        self.fp_image_label = None
        self.bd_image_label = None

        self.header_layout = QtGui.QHBoxLayout()
        self.header_layout.addWidget(self.name_label)
        self.header_layout.addWidget(self.close_button)

        self.image_layout = QtGui.QGridLayout()

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addLayout(self.image_layout)
        # self.main_layout.addWidget(self.bd_image_label)
        # self.bd_image_label.setParent(self.bd_image_label)
        # self.bd_image_label.move(10, 10)

        self.setLayout(self.main_layout)

    def setFPhwnd(self, hwnd):
        if self.fp_hwnd == "":
            self.fp_hwnd = hwnd
            if self.app.preview:
                self.fp_image_label = ViImageLabel(self.fp_hwnd)
                self.image_layout.addWidget(self.fp_image_label, 0, 0)

    def setBDhwnd(self, hwnd):
        if self.bd_hwnd == "":
            self.bd_hwnd = hwnd
            if self.app.preview:
                self.bd_image_label = ViImageLabel(hwnd)
                self.image_layout.addWidget(self.bd_image_label, 0, 1)
                # self.main_layout.addWidget(self.bd_image_label)

    def close_vi(self):
        win32gui.PostMessage(self.fp_hwnd, win32con.WM_CLOSE, 0, 0)

    """"
    def resizeEvent(self, *args, **kwargs):
        rescaled_pixmap = self.pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.image_label.setPixmap(rescaled_pixmap)
    """

    def hideBlockDiagram(self):
        if self.bd_image_label:
            self.bd_image_label.hide()

    def showBlockDiagram(self):
        if self.bd_image_label:
            self.bd_image_label.show()


class ViImageLabel(QtGui.QLabel):
    def __init__(self, hwnd):
        super(ViImageLabel, self).__init__()
        self.hwnd = hwnd
        image = get_image(self.hwnd)
        self.pixmap = QtGui.QPixmap(image)
        rescaled_pixmap = self.pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio,
                                             QtCore.Qt.SmoothTransformation)
        self.setPixmap(rescaled_pixmap)
        self.setScaledContents(True)
        self.setMaximumWidth(500)
        # p = self.palette()
        # p.setColor(self.backgroundRole(), QtCore.Qt.white)
        # self.setPalette(p)
        # self.setStyleSheet("background-color: rgb(255,255,255); margin:5px; border:1px solid rgb(255, 255, 0); ")
        self.setStyleSheet("background-color: rgb(255,255,255); margin:5px; ")

    def enterEvent(self, *args, **kwargs):
        self.setAutoFillBackground(True)

    def leaveEvent(self, *args, **kwargs):
        self.setAutoFillBackground(False)

    def mousePressEvent(self, QMouseEvent):
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)  # Use to maximize the window
        win32gui.SetForegroundWindow(self.hwnd)  # Won't maximize the window
        sys.exit(0)

    def resizeEvent(self, *args, **kwargs):
        rescaled_pixmap = self.pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setPixmap(rescaled_pixmap)


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

        #self.name = name
        #self.image = image

        # Get rid of?
        self.displayed = False

        self.name_label = QtGui.QLabel()
        self.name_label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.name_label.setAlignment(QtCore.Qt.AlignBottom)
        self.name_label.setParent(self)

        self.close_button = QtGui.QPushButton("X")

        #self.header_layout = QtGui.QHBoxLayout()
        #self.header_layout.addWidget(self.name_label)
        #self.header_layout.addWidget(self.close_button)

        #self.image_label = ImageLabel(image)

        #self.image_label = AutoScalingPixmapLabel()
        #pixmap = QtGui.QPixmap(image)
        #self.image_label.setPixmap(pixmap)

        #main_layout = QtGui.QVBoxLayout()
        #main_layout.addLayout(self.header_layout)
        #main_layout.addWidget(self)

        #self.setLayout(main_layout)

    def setName(self, name):
        self.name = name
        self.name_label.setText(name)

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


def main():
    app = QtGui.QApplication(sys.argv)
    ViViewerApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
