VI Viewer Dependencies:
Python 3.4
pillow
pywin32
PyQt4

Build Dependencies:
py2exe

To run VI Viewer from source:
Make sure all VI Viewer dependencies are installed. Once Python is installed the other dependencies can be installed easily with pip, e.g. "pip install pillow". PyQt4 can not be installed from pip, get it from the following link:
https://riverbankcomputing.com/software/pyqt/download

To build VI Viewer from source:
Make sure all VI Viewer and Build dependencies are installed. Open a command window in the same directory as the setup.py file and run "python setup.py py2exe".

To run the built VI Viewer:
Execute VI Viewer.exe in the dist folder. You can copy the dist folder to another location for your own use or use the dist folder on P4. Pinning the application to desktop or having a desktop shortcut is recommended for usability.