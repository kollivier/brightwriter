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
        
        self.isDirty = False
        self.imscp = None
        #dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
        self.dirtyNodes = []

        settings.ThirdPartyDir = os.path.join(settings.AppDir, "3rdparty", utils.getPlatformName())
        langdict = {"English":"en", "Espanol": "sp", "Francais":"fr"}
        settings.LangDirName = langdict[settings.AppSettings["Language"]]
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
        app.AddHandlerForID(ID_CLOSE, self.OnCloseProject)
        app.AddHandlerForID(ID_PROPS, self.OnProjectProps)
        app.AddHandlerForID(ID_TREE_REMOVE, self.RemoveItem)
        app.AddHandlerForID(ID_TREE_EDIT, self.OnEditItemProps) 
        app.AddHandlerForID(ID_EDIT_ITEM, self.EditItem)
        app.AddHandlerForID(ID_PREVIEW, self.OnPreviewEClass) 
        #wx.EVT_MENU(self, ID_PUBLISH, self.PublishToWeb)
        app.AddHandlerForID(ID_PUBLISH_CD, self.PublishToCD)
        #wx.EVT_MENU(self, ID_PUBLISH_PDF, self.PublishToPDF)
        app.AddHandlerForID(ID_PUBLISH_IMS, self.PublishToIMS)
        app.AddHandlerForID(ID_BUG, self.OnReportBug)
        app.AddHandlerForID(ID_THEME, self.OnManageThemes)
        
        app.AddHandlerForID(ID_ADD_MENU, self.OnNewItem)
        app.AddHandlerForID(ID_TREE_MOVEUP, self.OnMoveItemUp)
        app.AddHandlerForID(ID_TREE_MOVEDOWN, self.OnMoveItemDown)
        app.AddHandlerForID(ID_HELP, self.OnHelp)
        app.AddHandlerForID(ID_LINKCHECK, self.OnLinkCheck)
        app.AddHandlerForID(ID_CUT, self.OnCut)
        app.AddHandlerForID(ID_COPY, self.OnCopy)
        app.AddHandlerForID(ID_PASTE_BELOW, self.OnPaste)
        app.AddHandlerForID(ID_PASTE_CHILD, self.OnPaste)
        app.AddHandlerForID(ID_PASTE, self.OnPaste)
        app.AddHandlerForID(ID_IMPORT_FILE, self.OnImportFile)
        #wx.EVT_MENU(self, ID_REFRESH_THEME, self.OnRefreshTheme)
        #wx.EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
        app.AddHandlerForID(ID_ERRORLOG, self.OnErrorLog)
        app.AddHandlerForID(ID_ACTIVITY, self.OnActivityMonitor)
        app.AddHandlerForID(ID_CONTACTS, self.OnContacts)
        
        app.AddHandlerForID(ID_SETTINGS, self.OnAppPreferences)
        app.AddHandlerForID(wx.ID_ABOUT, self.OnAbout)
        
        app.AddUIHandlerForID(ID_SAVE, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_CLOSE, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PREVIEW, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_REFRESH_THEME, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH_MENU, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH_CD, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH_PDF, self.UpdateProjectCommand)
        
        app.AddUIHandlerForID(ID_PROPS, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_THEME, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_LINKCHECK, self.UpdateProjectCommand)
        
        app.AddUIHandlerForID(ID_CUT, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_COPY, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_PASTE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_FIND_IN_PROJECT, self.UpdatePageCommand)
        
        app.AddUIHandlerForID(ID_ADD_MENU, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_REMOVE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_IMPORT_FILE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_EDIT_ITEM, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_MOVEUP, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_MOVEDOWN, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_UPLOAD_PAGE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_EDIT, self.UpdatePageCommand)
        
        

        app.AddUIHandlerForID(self.GetMenuBar().FindMenu(_("Page")), self.UpdatePageCommand)
        app.AddUIHandlerForID(self.GetMenuBar().FindMenu(_("Edit")), self.UpdatePageCommand)
        #wx.EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

        app.AddHandlerForID(ID_EXIT, self.OnCloseWindow)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
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
        self.errorViewer.LoadState("ErrorLogViewer", dialogIsModal=False)
        
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

    def OnAbout(self, event):
        EClassAboutDialog(self).ShowModal()

    def OnHelp(self, event):
        import webbrowser
        url = os.path.join(settings.AppDir, "docs", settings.LangDirName, "index.htm")
        if not os.path.exists(url):
            url = os.path.join(settings.AppDir, "docs", "en", "manual", "index.htm")
        webbrowser.open_new("file://" + url)

    def OnAppPreferences(self, event):
        PreferencesEditor(self).ShowModal()

    def OnContacts(self, event):
        ContactsDialog(self).ShowModal()

    def OnEditItemProps(self, event):
        self.EditItemProps()
        
    def OnErrorLog(self, evt):
        self.errorViewer.Show()

    def OnFindInProject(self, evt):
        dlg = pfdlg.ProjectFindDialog(self)
        dlg.Show()

    def OnImportFile(self, event):
        parent = self.projectTree.GetCurrentTreeItem()
        if parent:
            parentitem = self.projectTree.GetCurrentTreeItemData()
            
            dialog = wx.FileDialog(self)
            if dialog.ShowModal() == wx.ID_OK:
                packagefile = guiutils.importFile(dialog.GetPath())
                
                newresource = ims.contentpackage.Resource()
                newresource.setFilename(packagefile)
                newresource.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                
                self.imscp.resources.append(newresource)
                
                newitem = ims.contentpackage.Item()
                newitem.title.text = os.path.basename(packagefile)
                newitem.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                newitem.attrs["identifierref"] = newresource.attrs["identifier"]
                
                parentitem.items.append(newitem)
                self.projectTree.AddIMSItemUnderCurrentItem(newitem)
                
                self.EditItemProps()
                
                

    def OnCut(self, event):
        sel_item = self.projectTree.GetSelection()
        self.CutNode = sel_item
        self.projectTree.SetItemTextColour(sel_item, wx.LIGHT_GREY)
        if self.CopyNode:
            self.CopyNode = None

    def OnCopy(self, event):
        sel_item = self.projectTree.GetSelection()
        self.CopyNode = sel_item
        if self.CutNode:
            self.projectTree.SetItemTextColour(self.CutNode, wx.BLACK)
            self.CutNode = None #copy automatically cancels a cut operation

    def OnLinkCheck(self, event):
        LinkChecker(self).ShowModal()

    def OnPaste(self, event):
        dirtyNodes = []
        sel_item = self.projectTree.GetSelection()
        pastenode = self.CopyNode
        if self.CutNode:
            pastenode = self.CutNode
        
        import copy
        pasteitem = copy.copy(self.projectTree.GetPyData(pastenode))

        newparent = None

        newitem = None            
        if event.GetId() == ID_PASTE_BELOW or event.GetId() == ID_PASTE:
            newitem = self.projectTree.InsertItem(self.projectTree.GetItemParent(sel_item), 
                                         sel_item, self.projectTree.GetItemText(pastenode), 
                                       -1, -1, wx.TreeItemData(self.projectTree.GetPyData(pastenode)))
            
            parent = self.projectTree.GetItemParent(sel_item)
            parentitem = self.projectTree.GetPyData(parent)
        
            beforeitem = self.projectTree.GetPyData(sel_item)
            assert(beforeitem)
            previndex = parentitem.items.index(beforeitem) + 1
            parentitem.items.insert(previndex, pasteitem)
            
            for item in parentitem.items:
                print "Title: " + item.title.text

        elif event.GetId() == ID_PASTE_CHILD:
            newitem = self.projectTree.AppendItem(sel_item, self.projectTree.GetItemText(pastenode), 
                                                -1, -1, wx.TreeItemData(self.projectTree.GetPyData(pastenode)))
            
            parentitem = self.projectTree.GetCurrentTreeItemData()
            parentitem.children.append(pasteitem)
        
        assert(newitem)
        if not self.projectTree.GetChildrenCount(pastenode, False) == 0:
            self.CopyChildrenRecursive(pastenode, newitem)

        dirtyNodes.append(pasteitem)

        if self.CutNode:
            cutparent = self.projectTree.GetItemParent(self.CutNode)
            cutparentitem = self.projectTree.GetPyData(cutparent)
            cutparentitem.items.remove(self.projectTree.GetPyData(pastenode))

            self.projectTree.Delete(self.CutNode)
            self.CutNode = None

        for item in dirtyNodes:
            self.Update(item)

    def CopyChildrenRecursive(self, sel_item, new_item):
        thisnode = self.projectTree.GetFirstChild(sel_item)[0]
        while (thisnode.IsOk()):
            thisitem = self.projectTree.AppendItem(new_item, self.projectTree.GetItemText(thisnode), 
                                 -1, -1, wx.TreeItemData(self.projectTree.GetPyData(thisnode)))
            
            if not self.projectTree.GetChildrenCount(thisnode, False) == 0:
                self.CopyChildrenRecursive(thisnode, thisitem)
            thisnode = self.projectTree.GetNextSibling(thisnode) 

    def OnActivate(self, event):
        if event.GetActive():
            appdata.activeFrame = self
        else:
            if appdata.activeFrame == self:
                appdata.activeFrame = None

    def OnCloseProject(self, event):
        if self.isDirty:
            answer = self.CheckSave()
            if answer == wx.ID_YES:
                self.SaveProject(event)
            elif answer == wx.ID_CANCEL:
                return
            else:
                self.isDirty = False

        self.imscp = None
        self.projectTree.DeleteAllItems()
        settings.ProjectDir = ""
        settings.ProjectSettings = conman.xml_settings.XMLSettings()
        if sys.platform.startswith("win"):
            self.ie.Navigate("about:blank")
            self.mozilla.Navigate("about:blank")
        else:
            self.browser.SetPage("<HTML><BODY></BODY></HTML")

    def OnManageThemes(self, event):
        ThemeManager(self).ShowModal()

    def OnMoveItemUp(self, event):
        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()
        parent = self.projectTree.GetItemParent(selection)
        parentitem = self.projectTree.GetPyData(parent)
        
        index = parentitem.items.index(selitem)
        if index > 0:
            parentitem.items.remove(selitem)
            parentitem.items.insert(index - 1, selitem)

            haschild = self.projectTree.ItemHasChildren(selection)
            prevsibling = self.projectTree.GetPrevSibling(selection)
            insertafter = self.projectTree.GetPrevSibling(prevsibling)
            
            self.projectTree.Delete(selection)
            newitem = self.projectTree.InsertItem(parent, insertafter, 
                                     selitem.title.text,-1,-1,wx.TreeItemData(selitem))
            if haschild:
                self.AddIMSChildItemsToTree(selection, selitem.items)
            self.projectTree.SelectItem(newitem)
            self.Update()
                
    def OnMoveItemDown(self, event):
        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()
        parent = self.projectTree.GetItemParent(selection)
        parentitem = self.projectTree.GetPyData(parent)
        
        index = parentitem.items.index(selitem)
        if index > 0:
            parentitem.items.remove(selitem)
            parentitem.items.insert(index + 1, selitem)

            insertafter = self.projectTree.GetNextSibling(selection)
            haschild = self.projectTree.ItemHasChildren(selection)
            
            self.projectTree.Delete(selection)
            newitem = self.projectTree.InsertItem(parent, insertafter, 
                                     selitem.title.text,-1,-1,wx.TreeItemData(selitem))
            if haschild:
                self.AddIMSChildItemsToTree(selection, selitem.items)
            self.projectTree.SelectItem(newitem)
            self.Update()

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

    def OnPreviewEClass(self, event):
        self.UpdateEClassDataFiles()
        import webbrowser
        webbrowser.open_new("file://" + os.path.join(settings.ProjectDir, "index.htm")) 

    def OnProjectProps(self, event):
        props = ProjectPropsDialog(self)
        props.ShowModal()
        props.Destroy()
        
    def OnReportBug(self, event):
        import webbrowser
        webbrowser.open_new("http://sourceforge.net/tracker/?group_id=67634")
        
    def OnTreeSelChanged(self, event):
        self.Preview()
        event.Skip()
        
    def OnTreeItemContextMenu(self, event):
        pt = event.GetPoint()
        item = event.GetItem() 
        if item:
            self.PopupMenu(menus.getPageMenu(), pt)
            
    def OnTreeDoubleClick(self, event):
        pt = event.GetPosition()
        item = self.projectTree.GetCurrentTreeItemData()

        if item:
            self.EditItem(event)
            self.Preview()
        
    def SkipNotebookEvent(self, evt):
        evt.Skip()
        
    def UpdateProjectCommand(self, event):
        value = not self.imscp is None
        event.Enable(value)
        
    def UpdatePageCommand(self, event):
        value = not self.projectTree.GetCurrentTreeItem() is None
        if event.GetId() == ID_TREE_REMOVE:
            value = value and not self.projectTree.GetCurrentTreeItem() == self.projectTree.GetRootItem()

        event.Enable(value)          
            
    def OnCloseWindow(self, event):
        self.ShutDown(event)

    def PromptToSaveExistingProject(self):
        msg = wx.MessageDialog(self, _("Would you like to save the current project before continuing?"),
                                        _("Save Project?"), wx.YES_NO | wx.CANCEL)
        return msg.ShowModal()

    def PublishToCD(self,event):
        folder = settings.ProjectDir
        if settings.ProjectSettings["CDSaveDir"] == "":
            result = wx.MessageDialog(self, _("You need to specify a directory in which to store the CD files for burning.\nWould you like to do so now?"), _("Specify CD Save Directory?"), wx.YES_NO).ShowModal()
            if result == wx.ID_YES:
                dialog = wx.DirDialog(self, _("Choose a folder to store CD files."), style=wx.DD_NEW_DIR_BUTTON)
                if dialog.ShowModal() == wx.ID_OK:
                    folder = settings.ProjectSettings["CDSaveDir"] = dialog.GetPath()
            else:
                return
        else:
            folder = settings.ProjectSettings["CDSaveDir"]

        self.UpdateContents()
        self.UpdateEClassDataFiles()
        #self.UpdateTextIndex()
        self.CopyCDFiles()
        message = _("A window will now appear with all files that must be published to CD-ROM. Start your CD-Recording program and copy all files in this window to that program, and your CD will be ready for burning.")
        dialog = wx.MessageBox(message, _("Export to CD Finished"))

        #Open the explorer/finder window
        if sys.platform.startswith("win"):
            if settings.ProjectSettings["SearchProgram"] == "Greenstone":
                folder = os.path.join(settings.AppSettings["GSDL"], "tmp", "exported_collections")
        
        guiutils.openFolderInGUI(folder)

    def OnFileChanged(self, filename):
        self.filesCopied += 1
        self.keepCopying = self.dialog.Update(self.filesCopied, "Copying: " + filename)

    def OnNewItem(self, event):
        self.CreateIMSResource()
    
    def CreateIMSResource(self, name=None, isroot=False):
        dialog = NewPageDialog(self)
        if name:
            dialog.txtTitle.SetValue(name)

        if dialog.ShowModal() == wx.ID_OK:
            pluginName = dialog.cmbType.GetStringSelection()
            plugin = plugins.GetPlugin(pluginName)
            if plugin:
                filename = os.path.join(plugin.plugin_info["Directory"], dialog.txtFilename.GetValue())
                    
                created = plugin.CreateNewFile(dialog.txtTitle.GetValue(), os.path.join(settings.ProjectDir, filename))
                if created:
                    newresource = ims.contentpackage.Resource()

                    if os.path.splitext(filename)[1] == ".ecp":
                        eclassutils.setEClassPageForIMSResource(newresource, filename)
                    else:
                        newresource.setFilename(filename)
                    
                    newresource.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                    
                    self.imscp.resources.append(newresource)
                    
                    newitem = ims.contentpackage.Item()
                    newitem.title.text = dialog.txtTitle.GetValue()
                    newitem.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                    newitem.attrs["identifierref"] = newresource.attrs["identifier"]
                    
                    parentitem = self.projectTree.GetCurrentTreeItemData()
                    parentitem.items.append(newitem)
                    
                    self.imscp.resources.append(newresource)
                    
                    
                    newtreeitem = self.projectTree.AddIMSItemUnderCurrentItem(newitem)
                        
                    if not self.projectTree.IsExpanded(self.projectTree.GetCurrentTreeItem()):
                            self.projectTree.Expand(self.projectTree.GetCurrentTreeItem())
                    
                    self.projectTree.SelectItem(newtreeitem)

                    self.EditItem(None)
                    self.UpdateContents()
    
                self.isNewCourse = False
            dialog.Destroy()
            
    def CopyCDFiles(self):
        #cleanup after old EClass versions
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.pyd"))
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.dll"))
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.exe"))

        pubdir = settings.ProjectDir
        if settings.ProjectSettings["CDSaveDir"] != "":
            pubdir = settings.ProjectSettings["CDSaveDir"]

        if pubdir != settings.ProjectDir:
            callback = GUIFileCopyCallback(self)
            maxfiles = fileutils.getNumFiles(settings.ProjectDir) + 1
            self.filesCopied = 0
            self.dialog = wx.ProgressDialog(_("Copying CD Files"), _("Preparing to copy CD files...") + "                            ", maxfiles, style=wx.PD_APP_MODAL)

            fileutils.CopyFiles(settings.ProjectDir, pubdir, 1, callback)

            self.dialog.Destroy()
            self.dialog = None
        # copy the server program
        if settings.ProjectSettings["SearchProgram"] != "Greenstone":
            fileutils.CopyFile("autorun.inf", os.path.join(settings.AppDir, "autorun"),pubdir)
            fileutils.CopyFile("loader.exe", os.path.join(settings.AppDir, "autorun"),pubdir)

        if settings.ProjectSettings["SearchProgram"] == "Greenstone":
            cddir = os.path.join(settings.AppSettings["GSDL"], "tmp", "exported_collections")
            if not os.path.exists(os.path.join(cddir, "gsdl", "eclass")):
                os.mkdir(os.path.join(cddir, "gsdl", "eclass"))
            fileutils.CopyFiles(settings.ProjectDir, os.path.join(cddir, "gsdl", "eclass"), True)
            fileutils.CopyFile("home.dm", os.path.join(settings.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
            fileutils.CopyFile("style.dm", os.path.join(settings.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
        elif settings.ProjectSettings["SearchProgram"] == "Lucene":
            pass

    def ShutDown(self, event):
        if self.isDirty:
            answer = self.PromptToSaveExistingProject()
            if answer == wx.ID_YES:
                self.SaveProject(event)
            elif answer == wx.ID_CANCEL:
                return
        
        settings.AppSettings.SaveAsXML(os.path.join(settings.PrefDir,"settings.xml"))
        
        # TODO: Make these utility windows and have their state saved and loaded
        # at app startup, shutdown
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
    
    def EditItem(self, event):
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
        
    def EditItemProps(self):
        selitem = self.projectTree.GetCurrentTreeItemData()
        seltreeitem = self.projectTree.GetCurrentTreeItem()
        if selitem:
            result = PagePropertiesDialog(self, selitem, None, os.path.join(settings.ProjectDir, "Text")).ShowModal()
            self.projectTree.SetItemText(seltreeitem, selitem.title.text)
            self.Update()
            self.isDirty = True

    def RemoveItem(self, event):
        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()
        if selection:
            mydialog = wx.MessageDialog(self, _("Are you sure you want to delete this page? Deleting this page also deletes any sub-pages or terms assigned to this page."), 
                                             _("Delete Page?"), wx.YES_NO)

            if mydialog.ShowModal() == wx.ID_YES:
                parent = self.projectTree.GetItemParent(selection)
                parentitem = self.projectTree.GetPyData(parent)
                
                parentitem.items.remove(selitem)
                
                self.projectTree.Delete(selection)
                self.UpdateContents()
                self.Update()
                self.isDirty = True

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
            self.dirtyNodes.append(imsitem)
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
            
    def UpdateEClassDataFiles(self, pubid=""):
        result = False
        busy = wx.BusyCursor()
        wx.Yield()
        #self.CreateDocumancerBook()
        #self.CreateDevHelpBook()
        utils.CreateJoustJavascript(self.imscp.organizations[0].items[0])
        index_config_file = os.path.join(settings.ProjectDir, "index_settings.cfg")
        # if an index settings file doesn't exist, create one with some common defaults
        if not os.path.exists(index_config_file):
            import ConfigParser
            config = ConfigParser.ConfigParser()
            config.add_section("Settings")
            config.set("Settings", "IgnoreFileTypes", "ecp,quiz,gif,jpg,png,bmp,swf,avi,mov,wmv,rm,wav,mp3")
            config.write(utils.openFile(index_config_file, "w"))
        del busy

        return True

    def PublishToIMS(self, event):
        import zipfile
        import tempfile
        #zipname = os.path.join(settings.ProjectDir, "myzip.zip")
        deffilename = fileutils.MakeFileName2(self.imscp.organizations[0].items[0].title.text) + ".zip"
        dialog = wx.FileDialog(self, _("Export IMS Content Package"), "", deffilename, _("IMS Content Package Files") + " (*.zip)|*.zip", wx.SAVE)
        if dialog.ShowModal() == wx.ID_OK: 
            tempdir = tempfile.mkdtemp()
            imsdir = os.path.dirname(os.path.join(tempdir, "IMSPackage"))
            if not os.path.exists(imsdir):
                os.makedirs(imsdir)
            imstheme = self.themes.FindTheme("IMS Package")
            publisher = imstheme.HTMLPublisher(self, imsdir)
            publisher.Publish()
            fileutils.CopyFiles(os.path.join(settings.ProjectDir, "File"), os.path.join(imsdir, "File"), 1)

            handle, zipname = tempfile.mkstemp()
            os.close(handle)
            if os.path.exists(dialog.GetPath()):
                result = wx.MessageBox(_("The file %s already exists in this directory. Do you want to overwrite this file?") % dialog.GetFilename(), 
                            _("Overwrite file?"), wx.YES_NO | wx.CANCEL | wx.ICON_WARNING)
                
                if not result == wx.ID_YES:
                    return
                    
                os.remove(dialog.GetPath())
        
            assert(self.imscp.filename)
            import zipfile
            import tempfile
            
            myzip = zipfile.ZipFile(zipname, "w")
            import utils.zip
            utils.zip.dirToZipFile("", myzip, os.path.dirname(self.imscp.filename), excludeFiles=["imsmanifest.xml"], 
                            excludeDirs=["installers", "cgi-bin"], ignoreHidden=True)

            myzip.close()
            os.rename(zipname, dialog.GetPath())

        wx.MessageBox("Finished exporting!")    