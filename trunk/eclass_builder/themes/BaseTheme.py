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

import eclassutils

isPublic = True
from StringIO import StringIO

themename = "Default (frames)"

import logging

class PublishErrorHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self, logging.ERROR)
        self.errors = []
        
    def clear(self):
        self.errors = []

    def emit(self, record):
        self.errors.append("%s" % record.getMessage())

errorLog = PublishErrorHandler()
log = logging.getLogger('HTMLPublisher')
log.addHandler(errorLog)

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
        self.dir = dir
        # be backwards compatible
        if self.dir == "":
            self.dir = settings.ProjectDir
        
        self.counter = 1
        self.themedir = os.path.join(settings.AppDir, "themes", themename)
        self.cancelled = False

    def GetErrors(self):
        global errorLog
        if errorLog:
            return errorLog.errors
    
        return None

    def Publish(self):
        global errorLog
        errorLog.clear()
        
        self.progress = None
        if not self.parent or not self.parent.imscp:
            return
            
        try:
            if isinstance(self.parent, wx.Frame):
                self.progress = wx.ProgressDialog(_("Updating EClass"), _("Preparing to update EClass..."), self.parent.projectTree.GetCount() + 1, None, wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT)
            self.CopySupportFiles()
            self.CreateTOC()
            
            self.PublishPages(self.parent.imscp.organizations[0].items[0])
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
        pass
            
    def GetSearchPageLink(self):
        link = ""
        if self.pub.settings["SearchEnabled"] != "" and int(self.pub.settings["SearchEnabled"]):
            if self.pub.settings["SearchProgram"] == "Swish-e":
                link = "cgi-bin/search.py"
            elif self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
                link = "gsdl?site=127.0.0.1&a=p&p=about&c=" + self.pub.pubid + "&ct=0"
        
        return link

    def PublishPages(self, node):
        page = ""
        if self.cancelled:
            return
        keepgoing = True #assuming no dialog to cancel, this must always be the case
        if self.progress:
            keepgoing = self.progress.Update(self.counter, _("Updating page %(page)s") % {"page":node.title.text})
        if not keepgoing:
            result = wx.MessageDialog(self.parent, "Are you sure you want to cancel publishing this EClass?", "Cancel Publishing?", wx.YES_NO).ShowModal()
            if result == wx.ID_NO:
                self.cancelled = False
                self.progress.Resume()
            else:
                self.cancelled = true
                return
        self.counter = self.counter + 1

        if node != None:
            filename = eclassutils.getEditableFileForIMSItem(self.parent.imscp, node)
            publisher = plugins.GetPublisherForFilename(filename)
            if publisher:
                publisher.Publish(self.parent, node, settings.ProjectDir)
            
        if len(node.items) > 0:
            for child in node.items:
                self.PublishPages(child)
