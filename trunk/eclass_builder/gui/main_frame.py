#!/usr/bin/env python

import sys, urllib2, cPickle
import string, time, cStringIO, os, re, glob, csv, shutil

import wx
import wxaddons
import wxaddons.persistence
import wxaddons.sized_controls as sc
import time

wx.SystemOptions.SetOptionInt("mac.textcontrol-use-mlte", 1)

hasmozilla = False

import xml.dom.minidom

import ftplib
import themes.themes as themes
import conman.xml_settings as xml_settings
import conman.vcard as vcard
from convert.PDF import PDFPublisher
import wxbrowser
import ims
import ims.contentpackage

hasLucene = False
try:
    import PyLucene
    import indexer
    hasLucene = True
except:
    import traceback
    print `traceback.print_exc()`
    
import conman
import version
import utils
import fileutils
import guiutils
import constants
import mmedia
import analyzer
import eclass_convert
import eclass
import appdata

# Import the gui dialogs. They used to be embedded in editor.py
# so we will just import their contents for now to avoid conflicts.
# In the future, I'd like to not do things this way so that we can
# examine the code to find module dependencies.
import wx.lib.mixins.listctrl
import wx.lib.newevent

try:
    import taskrunner
except:
    pass

from gui.theme_manager import *
from gui.link_manager import *
from gui.startup import *
from gui.about import *
from gui.contacts import *
from gui.page_properties import *
from gui.open import *
from gui.new import *
from gui.options import *
from gui.ftp import *
from gui.indexing import *
from gui.project_props import *
from gui.activity_monitor import *
import gui.error_viewer
import gui.project_find_dialog as pfdlg
import gui.media_convert
import gui.prompts as prompts
import gui.imstree
import gui.menus as menus

try:
    import win32process, win32con
    # for the module detection script
    import wx.lib.iewin
except:
    pass

#dynamically import any plugin in the plugins folder and add it to the 'plugin registry'
import plugins
plugins.LoadPlugins() 

settings.plugins = plugins.pluginList

from constants import *
from gui.ids import *

try:
    import win32api
    import win32pipe
except:
    pass

try:
    import pythoncom
except:
    pass

class GUIIndexingCallback:
    def __init__(self, parent):
        self.parent = parent
        
    def fileProgress(self, totalFiles, statustext):
        wx.CallAfter(self.parent.OnIndexFileChanged, totalFiles, statustext)
        
class GUIFileCopyCallback:
    def __init__(self, parent):
        self.parent = parent
        
    def fileChanged(self, filename):
        wx.CallAfter(self.parent.OnFileChanged, filename)
        # TODO: Fix this very nasty hack. What we really need is a threaded
        # system which fires an event when finished.
        if wx.Platform == "__WXMAC__":
            wx.Yield()
        
#----------------------------- MainFrame Class ----------------------------------------------

class MainFrame2(sc.SizedFrame): 
    def __init__(self, parent, ID, title):
        busy = wx.BusyCursor()
        sc.SizedFrame.__init__(self, parent, ID, title, size=(780,580), 
                      style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN)
        
        # the default encoding isn't correct for Mac.
        if wx.Platform == "__WXMAC__":
            wx.SetDefaultPyEncoding("utf-8")
        
        #wx.FRAME_EX_UNIFIED = 0x100
        #self.SetExtraStyle(wx.FRAME_EX_UNIFIED)
        self.isDirty = False
        self.isNewCourse = False
        self.CurrentItem = None #current node
        self.CurrentTreeItem = None
        self.imscp = ims.contentpackage.ContentPackage() 
        #dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
        self.dirtyNodes = []

        settings.ThirdPartyDir = os.path.join(settings.AppDir, "3rdparty", utils.getPlatformName())
        self.errorPrompts = prompts.errorPrompts

        # These are used for copy and paste, and drag and drop
        self.DragItem = None
        self.CutNode = None
        self.CopyNode = None
        
        self.themes = themes.ThemeList(os.path.join(settings.AppDir, "themes"))
        self.currentTheme = self.themes.FindTheme("Default (no frames)")
        
        wx.InitAllImageHandlers()

        import errors
        self.log = errors.appErrorLog

        self.statusBar = None #self.CreateStatusBar()

        if sys.platform.startswith("win"):
            self.SetIcon(wx.Icon(os.path.join(settings.AppDir, "icons", "eclass_builder.ico"), wx.BITMAP_TYPE_ICO))

        #load icons
        imagepath = os.path.join(settings.AppDir, "icons")
        icnNewProject = wx.Bitmap(os.path.join(imagepath, "book_green16.gif"), wx.BITMAP_TYPE_GIF)
        icnOpenProject = wx.Bitmap(os.path.join(imagepath, "open16.gif"), wx.BITMAP_TYPE_GIF)
        icnSaveProject = wx.Bitmap(os.path.join(imagepath, "save16.gif"), wx.BITMAP_TYPE_GIF)

        icnNewPage = wx.Bitmap(os.path.join(imagepath, "new16.gif"), wx.BITMAP_TYPE_GIF)
        icnEditPage = wx.Bitmap(os.path.join(imagepath, "edit16.gif"), wx.BITMAP_TYPE_GIF)
        icnPageProps = wx.Bitmap(os.path.join(imagepath, "properties16.gif"), wx.BITMAP_TYPE_GIF)
        icnDeletePage = wx.Bitmap(os.path.join(imagepath, "delete16.gif"), wx.BITMAP_TYPE_GIF)

        icnPreview = wx.Bitmap(os.path.join(imagepath, "doc_map16.gif"), wx.BITMAP_TYPE_GIF)
        icnPublishWeb = wx.Bitmap(os.path.join(imagepath, "ftp_upload16.gif"), wx.BITMAP_TYPE_GIF)
        icnPublishCD = wx.Bitmap(os.path.join(imagepath, "cd16.gif"), wx.BITMAP_TYPE_GIF)
        icnPublishPDF = wx.Bitmap(os.path.join(imagepath, "pdf.gif"), wx.BITMAP_TYPE_GIF)
        icnHelp = wx.Bitmap(os.path.join(imagepath, "help16.gif"), wx.BITMAP_TYPE_GIF)

        self.treeimages = wx.ImageList(15, 15)
        #self.treeimages.Add(wxBitmap(os.path.join(imagepath, "bookclosed.gif"), wxBITMAP_TYPE_GIF))
        #self.treeimages.Add(wxBitmap(os.path.join(imagepath, "chapter.gif"), wxBITMAP_TYPE_GIF))
        #self.treeimages.Add(wxBitmap(os.path.join(imagepath, "page.gif"), wxBITMAP_TYPE_GIF))

        #create toolbar
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.AddSimpleTool(ID_NEW, icnNewProject, _("New"), _("Create a New Project"))
        self.toolbar.AddSimpleTool(ID_OPEN, icnOpenProject, _("Open"), _("Open an Existing Project")) 
        self.toolbar.AddSimpleTool(ID_SAVE, icnSaveProject, _("Save"), _("Save Current Project"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_ADD_MENU, icnNewPage, _("New Page"), _("Adds a New EClass Page"))
        self.toolbar.AddSimpleTool(ID_EDIT_ITEM, icnEditPage, _("Edit Page"), _("Edits the Currently Selected Eclass Page"))
        self.toolbar.AddSimpleTool(ID_TREE_EDIT, icnPageProps, _("Page Properties"), _("View and Edit Page Properties"))
        self.toolbar.AddSimpleTool(ID_TREE_REMOVE, icnDeletePage, _("Delete Page"), _("Delete Currently Selected Page"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_PREVIEW, icnPreview, _("Preview EClass"), _("Preview EClass in Browser"))
        self.toolbar.AddSimpleTool(ID_PUBLISH_CD, icnPublishCD, _("Publish to CD-ROM"), _("Publish to CD-ROM"))
        self.toolbar.AddSimpleTool(ID_PUBLISH, icnPublishWeb, _("Publish to web site"), _("Publish to web site"))
        self.toolbar.AddSimpleTool(ID_PUBLISH_PDF, icnPublishPDF, _("Publish to PDF"), _("Publish to PDF"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_HELP, icnHelp, _("View Help"), _("View Help File"))

        if not sys.platform.startswith("darwin"):
            self.toolbar.SetToolBitmapSize(wx.Size(16,16))

        self.toolbar.Realize()

        if sys.platform.startswith("darwin"):
            wx.App.SetMacPreferencesMenuItemId(ID_SETTINGS)

        self.SetMenuBar(menus.getMenuBar())
        
        pane = self.GetContentsPane()
        #split the window into two - Treeview on one side, browser on the other
        self.splitter1 = wx.SplitterWindow(pane, -1, style=wx.NO_BORDER)
        self.splitter1.SetSashSize(7)
        self.splitter1.SetSizerProps({"expand":True, "proportion":1})

        # Tree Control for the XML hierachy
        self.projectTree = gui.imstree.IMSCPTreeControl(self.splitter1,
                    -1 ,
                    style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.SIMPLE_BORDER)

        #self.projectTree.SetImageList(self.treeimages)

        #handle delete key
        accelerators = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_TREE_REMOVE)])
        self.SetAcceleratorTable(accelerators)

        #self.previewbook = wx.Notebook(self.splitter1, -1, style=wx.CLIP_CHILDREN)

        # TODO: This really needs fixed once webkit issues are worked out
        self.browsers = {}
        browsers = wxbrowser.browserlist
        #if len(browsers) == 1 and browsers[0] == "htmlwindow":
        #   self.browsers["htmlwin"] = self.browser = wx.HtmlWindow(self.previewbook, -1)
        #   self.previewbook.AddPage(self.browser, _("HTML Preview"))
        #else:
        if 1:
            #if "htmlwindow" in browsers:
            #   browsers.remove("htmlwindow")
            default = "htmlwindow"
            if sys.platform.startswith("win") and "ie" in browsers:
                default = "ie"
            elif sys.platform.startswith("darwin") and "webkit" in browsers:
                default = "webkit"
            elif "mozilla" in browsers:
                default = "mozilla"
            self.browser = wxbrowser.wxBrowser(self.splitter1, -1, default)
            self.browsers[default] = self.browser
            #for browser in browsers:
                #panel = sc.SizedPanel(self.previewbook, -1)
                #self.browser = self.browsers[browser] = wxbrowser.wxBrowser(self.previewbook, -1, browser)
                #self.browser.browser.SetSizerProps({"expand": True, "proportion":1})
                #self.previewbook.AddPage(self.browser.browser, self.browsers[browser].GetBrowserName())
        
        self.splitter1.SplitVertically(self.projectTree, self.browser.browser, 200)

        #wx.EVT_MENU(self, ID_NEW, self.NewProject)
        app = wx.GetApp()
        app.AddHandlerForID(ID_OPEN, self.OnOpen)
        app.AddHandlerForID(ID_SAVE, self.SaveProject)
        #wx.EVT_MENU(self, ID_CLOSE, self.OnClose)
        #wx.EVT_MENU(self, ID_EXIT, self.TimeToQuit)
        #wx.EVT_MENU(self, ID_PROPS, self.LoadProps)
        #wx.EVT_MENU(self, ID_TREE_REMOVE, self.RemoveItem)
        #wx.EVT_MENU(self, ID_TREE_EDIT, self.EditItem) 
        #wx.EVT_MENU(self, ID_EDIT_ITEM, self.EditFile) 
        #wx.EVT_MENU(self, ID_PREVIEW, self.PublishIt) 
        #wx.EVT_MENU(self, ID_PUBLISH, self.PublishToWeb)
        #wx.EVT_MENU(self, ID_PUBLISH_CD, self.PublishToCD)
        #wx.EVT_MENU(self, ID_PUBLISH_PDF, self.PublishToPDF)
        #wx.EVT_MENU(self, ID_PUBLISH_IMS, self.PublishToIMS)
        #wx.EVT_MENU(self, ID_BUG, self.ReportBug)
        #wx.EVT_MENU(self, ID_THEME, self.ManageThemes)
        
        #wx.EVT_MENU(self, ID_ADD_MENU, self.OnNewItem)
        #wx.EVT_MENU(self, ID_SETTINGS, self.EditPreferences)
        #wx.EVT_MENU(self, ID_TREE_MOVEUP, self.MoveItemUp)
        #wx.EVT_MENU(self, ID_TREE_MOVEDOWN, self.MoveItemDown)
        #wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
        #wx.EVT_MENU(self, ID_HELP, self.OnHelp)
        #wx.EVT_MENU(self, ID_LINKCHECK, self.OnLinkCheck)
        #wx.EVT_MENU(self, ID_CUT, self.OnCut)
        #wx.EVT_MENU(self, ID_COPY, self.OnCopy)
        #wx.EVT_MENU(self, ID_PASTE_BELOW, self.OnPaste)
        #wx.EVT_MENU(self, ID_PASTE_CHILD, self.OnPaste)
        #wx.EVT_MENU(self, ID_PASTE, self.OnPaste)
        #wx.EVT_MENU(self, ID_IMPORT_FILE, self.AddNewItem)
        #wx.EVT_MENU(self, ID_REFRESH_THEME, self.OnRefreshTheme)
        #wx.EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
        app.AddHandlerForID(ID_ERRORLOG, self.OnErrorLog)
        app.AddHandlerForID(ID_ACTIVITY, self.OnActivityMonitor)
        app.AddHandlerForID(ID_CONTACTS, self.OnContacts)
        #wx.EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged, self.projectTree)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.OnTreeItemContextMenu, self.projectTree)
        self.projectTree.Bind(wx.EVT_LEFT_DCLICK, self.OnTreeDoubleClick)

        #wx.EVT_RIGHT_DOWN(self.projectTree, self.OnTreeRightClick)
        #self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged, self.projectTree)
        #wx.EVT_LEFT_DCLICK(self.projectTree, self.OnTreeDoubleClick)
        
        self.SetMinSize(self.GetSizer().GetMinSize())

        #if sys.platform.startswith("win"):
        # this nasty hack is needed because on Windows, the controls won't
        # properly layout until the frame is resized. 
        # It appears it is now needed on Mac, too.
        self.SetSize((self.GetSize()[0]+1, self.GetSize()[1]+1))
            
        #if sys.platform.startswith("darwin"):
        #    self.FileMenu.FindItemById(ID_PUBLISH_PDF).Enable(False)
        #    self.toolbar.EnableTool(ID_PUBLISH_PDF, False)
        
        self.activityMonitor = ActivityMonitor(self)
        self.activityMonitor.LoadState("ActivityMonitor")
        
        self.errorViewer = gui.error_viewer.ErrorLogViewer(self)
        self.errorViewer.LoadState("ErrorLogViewer")
        
        if wx.Platform == '__WXMSW__':
            EVT_CHAR(self.previewbook, self.SkipNotebookEvent)

        if settings.AppSettings["LastOpened"] != "" and os.path.exists(settings.AppSettings["LastOpened"]):
            self.LoadEClass(settings.AppSettings["LastOpened"])
            
        #else:
        #    dlgStartup = StartupDialog(self)
        #    result = dlgStartup.ShowModal()
        #    dlgStartup.Destroy()
            
        #    if result == 0:
        #        self.NewProject(None)
        #    if result == 1:
        #        self.OnOpen(None)
        #    if result == 2:
        #        self.OnHelp(None)
                
    def OnActivityMonitor(self, evt):
        self.activityMonitor.Show()

    def OnContacts(self, event):
        ContactsDialog(self).ShowModal()

    def OnErrorLog(self, evt):
        self.errorViewer.Show()

    def OnFindInProject(self, evt):
        dlg = pfdlg.ProjectFindDialog(self)
        dlg.Show()
        
    def OnActivate(self, event):
        if event.GetActive():
            appdata.activeFrame = self
        else:
            if appdata.activeFrame == self:
                appdata.activeFrame = None
        
    def OnOpen(self,event):
        """
        Handler for File-Open
        """
        
        if self.isDirty:
            answer = self.CheckSave()
            if answer == wx.ID_YES:
                self.SaveProject(event)
            elif answer == wx.ID_CANCEL:
                return
            else:
                self.isDirty = False
        
        defaultdir = ""
        if settings.AppSettings["CourseFolder"] != "" and os.path.exists(settings.AppSettings["CourseFolder"]):
            defaultdir = settings.AppSettings["CourseFolder"]

        dialog = OpenPubDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            self.LoadEClass(dialog.GetPath())
        
        dialog.Destroy()
        
    def OnTreeSelChanged(self, event):
        self.toolbar.EnableTool(ID_EDIT_ITEM, True)
        self.toolbar.EnableTool(ID_TREE_EDIT, True)
        self.toolbar.EnableTool(ID_ADD_MENU, True)
        pageMenu = self.menuBar.FindMenu(_("Page"))
        self.menuBar.EnableTop(pageMenu, True)

        if self.CurrentTreeItem == self.projectTree.GetRootItem():
            self.PopMenu.Enable(ID_TREE_REMOVE, False)
            self.toolbar.EnableTool(ID_TREE_REMOVE, False)
        else:
            self.PopMenu.Enable(ID_TREE_REMOVE, True)
            self.toolbar.EnableTool(ID_TREE_REMOVE, True)

        self.Preview()
        event.Skip()
        
    def OnTreeItemContextMenu(self, event):
        pt = event.GetPoint()
        item = event.GetItem() 
        if item:
            self.PopupMenu(self.PopMenu, pt)
            
    def OnTreeDoubleClick(self, event):
        pt = event.GetPosition()
        item = self.projectTree.GetCurrentTreeItemData()

        if item:
            self.EditFile(event)
            self.Preview()
        
    def SkipNotebookEvent(self, evt):
        evt.Skip()
            
    def UpdateUIState(self):
        # determine whether or not we have a project file
        value = not self.imscp is None
        
        menubar = self.GetMenuBar() 
        menubar.FindItem(ID_SAVE).Enable(value)
        menubar.FindItem(ID_CLOSE).Enable(value)
        menubar.FindItem(ID_PREVIEW).Enable(value)
        menubar.FindItem(ID_REFRESH_THEME).Enable(value)
        menubar.FindItem(ID_PUBLISH_MENU).Enable(value)
        menubar.FindItem(ID_PROPS).Enable(value)

        self.toolbar.EnableTool(ID_SAVE, value)
        self.toolbar.EnableTool(ID_PREVIEW, value)
        self.toolbar.EnableTool(ID_PUBLISH, value)
        self.toolbar.EnableTool(ID_PUBLISH_CD, value)
        if not sys.platform.startswith("darwin"):
            self.toolbar.EnableTool(ID_PUBLISH_PDF, value)
        self.toolbar.EnableTool(ID_TREE_ADD_ECLASS, value)
        self.toolbar.EnableTool(ID_TREE_EDIT, value)
        self.toolbar.EnableTool(ID_EDIT_ITEM, value)
        self.toolbar.EnableTool(ID_TREE_REMOVE, value)

        self.menuBar.EnableTop(self.menuBar.FindMenu(_("Edit")), value)
        # TODO: Only disable items that require a course to be open
        self.menuBar.EnableTop(self.menuBar.FindMenu(_("Tools")), value)
        if sys.platform.startswith("darwin"):
            #still needed?
            self.menuBar.Refresh()
        
        if self.CurrentTreeItem:
            self.menuBar.EnableTop(self.menuBar.FindMenu(_("Page")), value)
            
    def OnClose(self, event):
        self.ShutDown(event)

    def PromptToSaveExistingProject(self):
        msg = wx.MessageDialog(self, _("Would you like to save the current project before continuing?"),
                                        _("Save Project?"), wx.YES_NO | wx.CANCEL)
        return msg.ShowModal()

    def ShutDown(self, event):
        if self.isDirty:
            answer = self.PromptToSaveExistingProject()
            if answer == wx.ID_YES:
                self.SaveProject(event)
            elif answer == wx.ID_CANCEL:
                return
        
        settings.AppSettings.SaveAsXML(os.path.join(settings.PrefDir,"settings.xml"))
        if self.activityMonitor:
            self.activityMonitor.SaveState("ActivityMonitor")
            self.activityMonitor.Destroy()
        if self.errorViewer:
            self.errorViewer.SaveState("ErrorLogViewer")
            self.errorViewer.Destroy()
        self.Destroy()
        
    def SaveProject(self, event):
        """
        Runs when the user selects the Save option from the File menu
        """
        filename = self.imscp.filename
        if not filename or not os.path.exists(filename):
            defaultdir = ""
            if settings.AppSettings["CourseFolder"] != "" and os.path.exists(settings.AppSettings["CourseFolder"]):
                defaultdir = settings.AppSettings["CourseFolder"]
            
            f = wx.FileDialog(self, _("Select a file"), defaultdir, "", "XML Files (*.xml)|*.xml", wx.SAVE)
            if f.ShowModal() == wx.ID_OK:
                filename = f.GetPath()
                self.isDirty = False
            f.Destroy()
        
        #self.CreateDocumancerBook()
        #self.CreateDevHelpBook()

        try:
            self.imscp.saveAsXML(filename)
            self.isDirty = False
        except IOError, e:
            message = _("Could not save EClass project file. Error Message is:")
            self.log.write(message)
            wx.MessageBox(message + str(e), _("Could Not Save File"))
        
    def LoadEClass(self, filename):
        busy = wx.BusyCursor()
        if not os.path.exists(filename):
            self.errorPrompts.displayError(_("Could not find EClass file: %s") % filename)
            return
            
        try:
            converter = eclass_convert.EClassIMSConverter(filename)
            self.imscp = None
            if converter.IsEClass():
                # TODO: detect if there are non-ascii characters,
                # and prompt the user for language to convert from
                self.imscp = converter.ConvertToIMSContentPackage()
            else:
                self.imscp = ims.contentpackage.ContentPackage()
                self.imscp.loadFromXML(filename)
            
            if self.imscp:
                settings.ProjectDir = os.path.dirname(filename)
                # TODO: We should store the project as a global rather than its settings
                settings.ProjectSettings = xml_settings.XMLSettings()
                settingsfile = os.path.join(settings.ProjectDir, "settings.xml")
                if os.path.exists(settingsfile):
                    settings.ProjectSettings.LoadFromXML(settingsfile)
                    
                pylucenedir = os.path.join(settings.ProjectDir, "index.pylucene")
                if os.path.exists(pylucenedir):
                    os.rename(pylucenedir, os.path.join(settings.ProjectDir, "index.lucene"))
    
                if len(self.imscp.organizations) > 0:
                    self.projectTree.AddIMSItemsToTree(self.imscp.organizations[0].items[0])
                    self.Preview()
                
                mytheme = settings.ProjectSettings["Theme"]
                self.currentTheme = self.themes.FindTheme(mytheme)
                if not self.currentTheme:
                    self.currentTheme = self.themes.FindTheme("Default (frames)")
    
                if settings.ProjectSettings["SearchProgram"] == "Swish-e":
                    settings.ProjectSettings["SearchProgram"] = "Lucene"
                    self.errorPrompts.displayError(_("The SWISH-E search program is no longer supported. This project has been updated to use the Lucene search engine instead. Run the Publish to CD function to update the index."))
    
                self.isDirty = False
                
                self.SetFocus()
                # self.SwitchMenus(True)
                settings.AppSettings["LastOpened"] = filename
                settings.ProjectSettings = settings.ProjectSettings
                viddir = os.path.join(settings.ProjectDir, "Video")
                auddir = os.path.join(settings.ProjectDir, "Audio")
                
                if os.path.exists(viddir) or os.path.exists(auddir):
                    self.errorPrompts.displayInformation(_("Due to new security restrictions in some media players, video and audio files need to be moved underneath of the 'pub' directory. EClass will now do this automatically and update your pages. Sorry for any inconvenience!"), _("Moving media files"))
                    os.rename(viddir, os.path.join(settings.ProjectDir, "pub", "Video"))
                    os.rename(auddir, os.path.join(settings.ProjectDir, "pub", "Audio"))
                    #self.PublishPageAndChildren(self.pub.nodes[0])
        except:
            del busy
            raise
            
        del busy

    # FIXME: Determine the best place to put this function
    def GetEditableFileForIMSItem(self, imsitem):
        filename = None
        if imsitem:
            import ims.utils
            selresource = ims.utils.getIMSResourceForIMSItem(self.imscp, imsitem)
            if selresource:
                filename = selresource.attrs["href"]
                eclasspage = eclass.getEClassPageForIMSResource(selresource)
                if eclasspage:
                    filename = eclasspage
                    
        return filename
    
    def EditFile(self, event):
        try:
            selitem = self.projectTree.GetCurrentTreeItemData()
            filename = self.GetEditableFileForIMSItem(selitem)
            isplugin = False
            result = wx.ID_CANCEL
            plugin = plugins.GetPluginForFilename(filename)
            if plugin:
                mydialog = plugin.EditorDialog(self, selitem)
                result = mydialog.ShowModal()
    
            if result == wx.ID_OK:
                self.Update()
                self.projectTree.SetItemText(self.projectTree.GetCurrentTreeItem(), selitem.title.text)
                self.isDirty = True
        except:
            message = _("There was an unknown error when attempting to start the page editor.")
            self.log.write(message)
            self.errorPrompts.displayError(message + constants.errorInfoMsg)
            raise
            
    def Preview(self):
        imsitem = self.projectTree.GetCurrentTreeItemData()
        if imsitem:
            import ims.utils
            resource = ims.utils.getIMSResourceForIMSItem(self.imscp, imsitem)
            if resource:
                filename = resource.attrs["href"]
        
        if filename:
            publisher = plugins.GetPublisherForFilename(filename)
            filelink = publisher.GetFileLink(filename).replace("/", os.sep)
            filename = os.path.join(settings.ProjectDir, filelink)
    
            #we shouldn't preview files that EClass can't view
            ok_fileTypes = ["htm", "html", "jpg", "jpeg", "gif"]
            if sys.platform == "win32":
                ok_fileTypes.append("pdf")
    
            if os.path.exists(filename) and os.path.splitext(filename)[1][1:] in ok_fileTypes:
                for browser in self.browsers:
                    self.browsers[browser].LoadPage(filename)
            else:
                #self.status.SetStatusText("Cannot find file: "+ filename)
                for browser in self.browsers:
                    self.browsers[browser].SetPage(utils.createHTMLPageWithBody("<p>" + _("The page %(filename)s cannot be previewed inside EClass. Double-click on the file to view or edit it.") % {"filename": os.path.basename(filename)} + "</p>"))

    def PublishPage(self, imsitem):
        if imsitem != None:
            filename = self.GetEditableFileForIMSItem(imsitem)
            publisher = plugins.GetPublisherForFilename(filename)
            if publisher:
                publisher.Publish(self, imsitem, settings.ProjectDir)

    def Update(self, imsitem = None):
        if imsitem == None:
            imsitem = self.projectTree.GetCurrentTreeItemData()
            
        self.UpdateContents()
        try:
            self.PublishPage(imsitem)

            self.Preview()
            self.dirtyNodes.append(myitem)
            if string.lower(settings.ProjectSettings["UploadOnSave"]) == "yes":
                self.UploadPage()
        except:
            message = _("Error updating page. ") + constants.errorInfoMsg
            self.errorPrompts.displayError(message)
            
    def UpdateContents(self):
        if self.statusBar:
            self.statusBar.SetStatusText(_("Updating table of contents..."))
        
        if not self.currentTheme:
            self.currentTheme = self.themes.FindTheme("Default (frames)")
        try:
            publisher = self.currentTheme.HTMLPublisher(self)
            result = publisher.CreateTOC()
        except IOError, e:
            message = utils.getStdErrorMessage("IOError", {"filename": e.filename, "type":"write"})
            self.errorPrompts.displayError(message, _("Could Not Save File"))
        except:
            pass #we shouldn't do this, but there may be non-fatal errors we shouldn't
                 #catch
        if self.statusBar:
            self.statusBar.SetStatusText("")