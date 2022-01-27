from __future__ import absolute_import
from .BaseTheme import *
themename = "Default (frames)"
import fileutils
import settings

# all file links are relative to the directory specified here
rootdir = ""

class HTMLPublisher(BaseHTMLPublisher):
    def __init__(self, parent=None, dir=""):
        BaseHTMLPublisher.__init__(self, parent, dir)
        self.themedir = os.path.join(settings.AppDir, "themes", themename)

    def CopySupportFiles(self):
        BaseHTMLPublisher.CopySupportFiles(self)
        fileutils.CopyFiles(os.path.join(settings.AppDir, "web"), self.dir, recurse=True)
        
    def CreateTOC(self):
        pass
