from distutils.core import setup
import py2exe

setup(windows=[{"script": "VI Viewer.py", "icon_resources": [(1, "icon.ico")]}], options={"py2exe":{"includes":["sip"]}})