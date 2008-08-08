#HTMLPublish.py - HTML Publishing utility
import sys
import os
import re
import StringIO
#import pre as re
import string
import wx
import fileutils
from htmlutils import *
import plugins
import utils
import settings
import constants
import conman

isPublic = True
from StringIO import StringIO

themename = "Default (frames)"

class BaseHTMLPublisher:
    """
    Class: HTMLPublish.HTMLPublisher
    Last Updated: 9/24/02  
    Description: This class creates an HTML version of the IMS Content Package viewable in all Javascript-enabled browsers.

    Attributes:
    - pub: the currently open ConMan project
    - parent: the window which initiated this class
    - dir: the root directory of the currently open ConMan project
    - templates: a dictionary of templates used when publishing HTML pages
    - appdir: Path to the EClass.Builder application
    - joustdir: Path to the Joust files directory

    Methods:
    - Publish: Creates the table of contents and publishes each page in the collection to HTML
    - CopyJoust: Copies the Joust navigation files to the published EClass
    - CreateTOCPage: Creates the table of contents for Joust
    - PublishPages: Publishes each node in the ConMan project to HTML 
    """

    def __init__(self, parent=None, dir=""):
        self.parent = parent
        self.pub = parent.pub
        self.dir = dir
        # be backwards compatible
        if self.dir == "":
            self.dir = settings.ProjectDir
        
        for subdir in constants.eclassdirs:
            fulldir = os.path.join(self.dir, subdir)
            if not os.path.exists(fulldir):
                os.makedirs(fulldir)
        
        self.counter = 1
        self.themedir = os.path.join(settings.AppDir, "themes", themename)
        self.cancelled = False

    def Publish(self):
        self.progress = None
        try:
            #delete old HTML files in case we've switched themes, etc.
            #files.DeleteFiles(os.path.join(self.dir, "*.htm"))
            #files.DeleteFiles(os.path.join(self.dir, "*.html"))
            #files.DeleteFiles(os.path.join(self.dir, "pub", "*.*"))

            if isinstance(self.parent, wx.Frame):
                self.progress = wx.ProgressDialog(_("Updating EClass"), _("Preparing to update EClass..."), self.parent.projectTree.GetCount() + 1, None, wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT)
            self.CopySupportFiles()
            #self.CreateTOC()
            #self.counter = 1
            if isinstance(self.pub, conman.conman.ConMan):
                self.PublishPages(self.pub.nodes[0])
        except:
            if self.progress:
                self.progress.Destroy()
            raise
            
        if self.progress:
            self.progress.Destroy()

        return not self.cancelled
    
    def CopySupportFiles(self):
        filesdir = os.path.join(self.themedir, "Files")
        if os.path.exists(filesdir):
            fileutils.CopyFiles(filesdir, self.dir, 1)

    def CreateTOC(self):
        filename = utils.GetFileLink(self.pub.nodes[0].content.filename)
        
        text = """foldersTree = gFld("%s", "%s")\n""" % (string.replace(self.pub.nodes[0].content.metadata.name, "\"", "\\\""), filename)
        text = text + self.AddTOCItems(self.pub.nodes[0], 1)
        searchenabled = False
        #if self.pub.settings["SearchEnabled"] != "":
        #   searchenabled = int(self.pub.settings["SearchEnabled"])

        #if searchenabled:
        #   if self.pub.settings["SearchProgram"] == "Swish-e":
        #       searchscript = "../cgi-bin/search.py"
        #       text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", searchscript)
        #   elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
        #       text = text + """searchID = insDoc(foldersTree, gLnk('S',"%s", "%s"))\n""" % ("Search", "../gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0")
        #file = open(os.path.join(self.themedir,"eclassNodes.js"), "r")
        #data = file.read()
        #file.close()
        #file = open(os.path.join(self.dir, "eclassNodes.js"), "w")
        #data = string.replace(data, "<!-- INSERT MENU ITEMS HERE -->", text)
        #file.write(data)
        #file.close()

        file = open(os.path.join(self.themedir,"index.tpl"), "r")
        data = file.read()
        file.close()
        file = open(os.path.join(self.dir, "index.htm"),"w")
        data = string.replace(data, "<!-- INSERT FIRST PAGE HERE -->", utils.GetFileLink(self.pub.nodes[0].content.filename))
        file.write(data)
        file.close()

    def AddTOCItems(self, nodes, level):
        text = ""
        for root in nodes.children:
            filename = ""
            if string.find(root.content.filename, "imsmanifest.xml") != -1:
                    root = root.pub.nodes[0]

            filename = utils.GetFileLink(root.content.filename) 

            if not root.content.public == "false":
                nodeName = "foldersTree"
                if (level > 1):
                    nodeName = "level" + `level` + "Node"
                if len(root.children) > 0:
                    nodeType = "../Graphics/menu/win/chapter.gif"
                else:
                    nodeType = "../Graphics/menu/win/page.gif"
                self.counter = self.counter + 1
            
                if len(root.children) > 0:
                    text = text + """level%sNode = insFld(%s, gFld("%s", "%s"))\n""" % (level + 1, nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), filename)
                    text = text + self.AddTOCItems(root, level + 1)
                else:
                    text = text + """insDoc(%s, gLnk('S', "%s", "%s"))\n""" % (nodeName, string.replace(root.content.metadata.name, "\"", "\\\""), filename)
            else:
                print "Item " + root.content.metadata.name + " is marked private and was not published."
            return text                 

    def GetContentsPage(self):
        if os.path.exists(os.path.join(self.themedir,"eclassNodes.js")):
            return "eclassNodes.js"
            
    def GetSearchPageLink(self):
        link = ""
        if self.pub.settings["SearchEnabled"] != "" and int(self.pub.settings["SearchEnabled"]):
            if self.pub.settings["SearchProgram"] == "Swish-e":
                link = "cgi-bin/search.py"
            elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
                link = "gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0"
        
        return link

    def PublishPages(self, node):
        print "In publish..."
        page = ""
        if self.cancelled:
            return
        keepgoing = True #assuming no dialog to cancel, this must always be the case
        if self.progress:
            keepgoing = self.progress.Update(self.counter, _("Updating page %(page)s") % {"page":node.content.metadata.name})
        if not keepgoing:
            result = wx.MessageDialog(self.parent, "Are you sure you want to cancel publishing this EClass?", "Cancel Publishing?", wx.YES_NO).ShowModal()
            if result == wx.ID_NO:
                self.cancelled = False
                self.progress.Resume()
            else:
                self.cancelled = true
                return
        self.counter = self.counter + 1
        if string.find(node.content.filename, "imsmanifest.xml") != -1:
            node = node.pub.nodes[0]

        try:
            publisher = plugins.GetPluginForFilename(node.content.filename).HTMLPublisher()
            publisher.Publish(self.parent, node, self.dir)
        except:
            print "Could not publish page " + os.path.join(self.dir, "pub", node.content.filename)
            import traceback
            print "Traceback is:\n" 
            traceback.print_exc()
            
        if len(node.children) > 0:
                for child in node.children:
                    self.PublishPages(child)
