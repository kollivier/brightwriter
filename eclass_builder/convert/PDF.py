import sys, copy
import os
import re
import StringIO
import string
import types
from htmlutils import *
from fileutils import *
import settings
import tempfile
import shutil
import utils
import constants
import appdata
import eclassutils
import ims

import wx

import plugins

from StringIO import StringIO

themename = "PDF"
Elements = []

import errors
log = errors.appErrorLog

class PDFPublisher:
    """
    Class: BaseTheme.BasePDFPublisher
    Last Updated: 9/24/02  
    Description: This class creates an PDF version of the IMS Content Package viewable in all Javascript-enabled browsers.

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

    def __init__(self, parent=None):
        self.parent = parent
        self.dir = settings.ProjectDir
        #if sys.platform != "win32":
        #   self.dir = string.replace(self.dir, " ", "\\ ")
        self.counter = 1

        self.themedir = os.path.join(settings.AppDir, "themes", themename)
        #self.templates = parent.templates
        self.cancelled = False
        self.progress = None
        self.pdffile = ""
        self.pdfdir = ""
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)
        self.files = []

    def Publish(self):
        global log
        self.pdfdir = self.dir
        if os.path.exists(self.tempdir):
            try:
                shutil.rmtree(self.tempdir)
            except:
                log.error(_("Could not remove directory '%(dir)s'.") % {"dir": self.tempdir})

        try:
            if isinstance(self.parent, wx.Frame):
                self.progress = wx.ProgressDialog("Publishing PDF", "Publishing PDF", 
                              self.parent.projectTree.GetCount() + 1, None, 
                              wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT)
            self.counter = 1
            self.PublishPages(appdata.currentPackage.organizations[0].items[0])
        except:
            if self.progress:
                self.progress.Destroy()
            raise
          
        #self.myfile.close()
        lang = appdata.projectLanguage
        self.pdffile = os.path.join(self.pdfdir, MakeFileName2(appdata.currentPackage.metadata.lom.general.title[lang] + ".pdf"))
        bookfile = "#HTMLDOC\n"
        pdffile = self.pdffile
        if sys.platform == "win32":
            pdffile = string.replace(self.pdffile, "\\", "/")
        bookfile = bookfile + "-f \"" + pdffile + "\" -t pdf --no-toc --no-links --compression=9 --jpeg=90 --verbose\n" 
        for afile in self.files:
            if afile != "" and os.path.exists(afile):
                if sys.platform == "win32":
                    afile = afile.replace("\\", "/")
                bookfile = bookfile + afile + "\n"

        handle, bookpath = tempfile.mkstemp() #os.path.join(self.tempdir, "eclass.book")
        os.close(handle)
        
        try:
            book = utils.openFile(bookpath, "w")
            book.write(bookfile)
            book.close()
            os.rename(bookpath, bookpath + ".book")
        except:
            message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":bookpath})
            log.error(message)
            return False
        
        if sys.platform == "win32":
            htmldoc = os.path.join(settings.ThirdPartyDir, "htmldoc", "htmldoc.exe")
        else:
            htmldoc = os.path.join(settings.ThirdPartyDir, "htmldoc", "bin", "htmldoc")

        try:
            datadir = os.path.dirname(htmldoc)
            if sys.platform == "win32":
                # use quotes to avoid issues with spaces in filenames
                htmldoc = '"' + htmldoc + '"'
                datadir = '"' + datadir + '"'
                bookpath = '"' + bookpath + '"' 
            else:
                bookpath = bookpath.replace(" ", "\\ ")
                datadir = datadir.replace(" ", "\\ ")
                
            #print 'Command is: ' + htmldoc + ' --datadir %s --batch %s' % (datadir, bookpath)
            command = htmldoc + " --datadir %s --batch %s" % (datadir, bookpath)
            result = wx.Execute(command, wx.EXEC_SYNC)
            if result == -1:
                message = _("Could not execute command '%(command)s'.") % {"command": command}
                log.error(message)
                wx.MessageBox(message)
        except:
            message = _("Could not publish PDF File.")
            log.error(message)
            if isinstance(self.parent, wx.Frame):
                wx.MessageBox(message  + constants.errorInfoMsg)
            self.cancelled = True
    
        if self.progress:
            self.progress.Destroy()

        return not self.cancelled

    def CreateTOC(self):
        pass

    def AddTOCItems(self, nodes, level):
        pass                

    def PublishPages(self, node):
        page = ""
        if self.cancelled:
            return
        keepgoing = True #assuming no dialog to cancel, this must always be the case
        if self.progress:
            keepgoing = self.progress.Update(self.counter, _("Updating ") + node.title.text)
        if not keepgoing:
            result = wx.MessageDialog(self.parent, _("Are you sure you want to cancel publishing this EClass?"), 
                                       _("Cancel Publishing?"), wx.YES_NO).ShowModal()
            if result == wx.ID_NO:
                self.cancelled = False
                self.progress.Resume()
            else:
                self.cancelled = True
                return
        self.counter = self.counter + 1
      
        filename = eclassutils.getEditableFileForIMSItem(appdata.currentPackage, node)
        publisher = plugins.GetPublisherForFilename(filename)
        
        if publisher:
            resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, node)
            if resource:
                filename = resource.getFilename()
            try:
                publisher.node = node
                publisher.data['name'] = TextToHTMLChar(node.title.text)
                publisher.GetData()
                templatefile = os.path.join(settings.AppDir, "convert", "PDF.tpl")
                publisher.data['charset'] = publisher.GetConverterEncoding()
                
                myhtml = publisher.ApplyTemplate(templatefile, publisher.data)
                
                myhtml = publisher.EncodeHTMLToCharset(myhtml, publisher.data['charset'])
                
                #myhtml = publisher.Publish(self.parent, node, self.dir)
                #myhtml = GetBody(StringIO(myhtml))
                #print "in PDF plugin, myhtml = " + myhtml[:100]
                if not myhtml == "":
                    myfile = utils.openFile(os.path.join(self.tempdir, filename), "w")
                    myfile.write(myhtml)
                    myfile.close()
                    self.files.append(os.path.join(self.tempdir, filename))
            except:
                message = _("Could not publish page '%(page)s'") % {"page": os.path.join(self.tempdir, filename)}
                global log
                log.error(message)
                if "--debug" in sys.argv:
                    raise

        if len(node.items) > 0:
            for child in node.items:
                self.PublishPages(child)
