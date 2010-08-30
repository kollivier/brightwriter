import wx
import wx.stc
import wx.lib.sized_controls as sc

import string
import os
#import conman.conman as conman
import locale
import re
import settings
import eclassutils
import ims
import ims.contentpackage
import appdata

import conman
from xmlutils import *
from htmlutils import *
from fileutils import *
import plugins
from mmedia import HTMLTemplates
    #from conman.colorbutton import *

try:
    if settings.webkit:
        import wx.webview
        webkit_available = True
        from htmleditor import *
except:
    webkit_available = False

from StringIO import StringIO
from threading import *
import traceback
import sys
import utils, guiutils, settings

import logging
log = logging.getLogger('EClass')

#-------------------------- PLUGIN REGISTRATION ---------------------
# This info is used so that EClass can be dynamically be added into
# EClass.Builder's plugin registry.

plugin_info = { "Name":"html", 
                "FullName":"Web Page", 
                "Directory": "Text", 
                "Extension": ["xhtml", "htm", "html"], 
                "Mime Type": "text/html",
                "IMS Type": "webcontent",
                "Requires":"", 
                "CanCreateNew":True}

#-------------------------- DATA CLASSES ----------------------------

htmlpage = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>New Page</title>
    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
</head>
<body>
    <h1>New Page</h1>
</body>
</html>
"""

def CreateNewFile(filename, name="New Page"):
    if os.path.exists(filename):
        raise IOError, "File already exists!"
    file = htmlpage
    file = file.replace("New Page", name)
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    output = open(filename, "w")
    output.write(file.encode("utf-8"))
    output.close()

#------------------------ PUBLISHER CLASSES -------------------------------------------
#if this isn't the main script, then we're probably loading in EClass.Builder
#so load the plugin publisher class
if __name__ != "__main__":
    class HTMLPublisher(plugins.BaseHTMLPublisher):
        #init defined by parent class
        def GetFileLink(self, filename):
            return "pub/" + os.path.basename(self.GetFilename(filename))

        def GetData(self):
            if isinstance(self.node, conman.conman.ConNode):
                filename = self.node.content.filename
            
            elif isinstance(self.node, ims.contentpackage.Item):
                resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)
                filename = eclassutils.getEClassPageForIMSResource(resource)
                if not filename:
                    filename = resource.getFilename()
            
            filename = os.path.join(settings.ProjectDir, filename)
            
            if os.path.exists(filename):
                myfile = None
                myfile = utils.openFile(filename, 'r')
                
                #if myfile:
                myhtml = GetBodySoup(myfile)
                myfile.close()
                #else:
                #   myhtml = ""
            else:
                myhtml = ""

            self.data['content'] = myhtml

if __name__ != "__main__":
    class EditorDialog:
        def __init__(self, parent, node):
            self.parent = parent
            self.node = node
    
        def ShowModal(self):
            if isinstance(self.node, conman.conman.ConNode):
                filename = self.node.content.filename
            
            elif isinstance(self.node, ims.contentpackage.Item):
                resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)
                filename = eclassutils.getEClassPageForIMSResource(resource)
                if not filename:
                    filename = resource.getFilename()

            self.filename = os.path.join(settings.ProjectDir, filename)
            if not os.path.exists(self.filename):
                global htmlpage
                file = utils.openFile(self.filename, "w")
                file.write(htmlpage)
                file.close()

            
            if False:
                size = wx.Display().ClientArea.Size
                size.x = size.x / 2
                size.y = size.y / 2
                print "size is %s" % size
                self.frame = EditorFrame(self.parent, self.filename, size=size)
                #self.frame.currentItem = self.currentItem
                self.frame.Show()
                self.frame.CentreOnScreen()
            else:
                guiutils.openInHTMLEditor(self.filename)
                
            return wx.ID_OK

class MyApp(wx.App):
    def OnInit(self):
        self.frame = EditorFrame(None)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
