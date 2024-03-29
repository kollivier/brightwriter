#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import urllib.request, urllib.parse, urllib.error
import zipfile

import wx
import wx.lib.sized_controls as sc

import appdata
import settings

import app_server

KOLIBRI_EXPORT_AVAILABLE = False
try:
    import export.kolibri
    KOLIBRI_EXPORT_AVAILABLE = True
except Exception as e:
    logging.warning("Unable to import ricecooker")
    logging.warning(e)
    raise

use_launch = False # not hasattr(sys, 'frozen')
if use_launch:
    import launch

import themes
import conman.xml_settings as xml_settings
import conman.vcard as vcard
from convert.PDF import PDFPublisher
import wxbrowser
import ims
import ims.contentpackage
import ims.zip_packaging

import conman
import epub
import version
import utils
import fileutils
import guiutils
import constants
import mmedia
import analyzer
import eclass_convert

# modules that don't get picked up elsewhere...
import wx.aui as aui
import wx.lib.mixins.listctrl
import wx.lib.newevent
import wx.lib.pubsub
from wx.lib.pubsub import pub

try:
    import externals.taskrunner as taskrunner
except:
    pass

import htmlutils
from . import source_edit_dialog

use_aui = True

# Import the gui dialogs. They used to be embedded in editor.py
# so we will just import their contents for now to avoid conflicts.
# In the future, I'd like to not do things this way so that we can
# examine the code to find module dependencies.
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
from gui.task_dialog import TaskDialog, wxDoneEvent, wxLogHandler
from gui.kolibri_export import KolibriExportDialog
from gui.import_url import ImportURLDialog

import gui.error_viewer
import gui.media_convert
import gui.prompts as prompts
import gui.imstree
import gui.ims_dialogs
import gui.menus as menus

#dynamically import any plugin in the plugins folder and add it to the 'plugin registry'
import plugins
plugins.LoadPlugins()

settings.plugins = plugins.pluginList

from constants import *
from gui.ids import *

try:
    import export.kolibri
    KOLIBRI_EXPORT_AVAILABLE = True
except Exception as e:
    logging.warning("Unable to import ricecooker")
    import traceback
    logging.warning('\n'.join(traceback.format_stack()))

IMPORT_FROM_URL_AVAILABLE = False
try:
    from ricecooker.utils.downloader import archive_page
    IMPORT_FROM_URL_AVAILABLE = True
except Exception as e:
    logging.warning("Unable to import ricecooker")
    logging.warning(e)

# we shouldn't preview files that EClass can't view
editable_file_types = ["htm", "html", "xhtml"]
previewable_file_types = editable_file_types + ["gif", "jpg", "jpeg", "pdf"]


def getMimeTypeForHTML(html):
    mimetype = 'text/html'
    if html.find("//W3C//DTD XHTML") != -1:
        mimetype = 'application/xhtml+xml'
    return mimetype


class GUIIndexingCallback(object):
    def __init__(self, parent):
        self.parent = parent

    def fileProgress(self, totalFiles, statustext):
        wx.CallAfter(self.parent.OnIndexFileChanged, totalFiles, statustext)


class GUIFileCopyCallback(object):
    def __init__(self, parent):
        self.parent = parent

    def fileChanged(self, filename):
        wx.CallAfter(self.parent.OnFileChanged, filename)
        # This is needed because for smaller packages, the copy dialog may be destroyed before
        # this event fires.
        wx.Yield()
        
command_ids = {
    ID_BOLD: "Bold",
    ID_ITALIC: "Italic",
    ID_UNDERLINE: "Underline",
    ID_BULLETS: "InsertUnorderedList",
    ID_NUMBERING: "InsertOrderedList",
    ID_ALIGN_LEFT: "JustifyLeft",
    ID_ALIGN_CENTER: "JustifyCenter",
    ID_ALIGN_RIGHT: "JustifyRight",
    ID_ALIGN_JUSTIFY: "JustifyFull",
}

#----------------------------- MainFrame Class ----------------------------------------------

frameClass = wx.Frame
if not use_aui:
    frameClass = sc.SizedFrame

class MainFrame2(frameClass):
    def __init__(self, parent, ID, title):
        busy = wx.BusyCursor()
        width, height = wx.GetDisplaySize()
        frameClass.__init__(self, parent, ID, title, size=(max(600, width * 0.7), max(500, height * 0.7)),
                      style=wx.DEFAULT_FRAME_STYLE|wx.WANTS_CHARS)

        self.imscp = None
        #dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
        self.dirtyNodes = []
        self.dirty = False

        # Used to check if page content has changed since it was loaded, to know if we need to
        #  present the save dialog.
        self.contents_on_load = None

        settings.ThirdPartyDir = os.path.join(settings.AppDir, "3rdparty", utils.getPlatformName())
        langdict = {"English":"en", "Espanol": "sp", "Francais":"fr"}
        lang = "English"
        if settings.AppSettings["Language"] in langdict:
            lang = settings.AppSettings["Language"]
        settings.LangDirName = langdict[lang]
        self.errorPrompts = prompts.errorPrompts

        self._mgr = None
        pane = None
        if use_aui:
            pane = self
            self._mgr = aui.AuiManager()

            # tell AuiManager to manage this frame
            self._mgr.SetManagedWindow(self)
        else:
            pane = self.GetContentsPane()
            pane.SetSizerProps(expand=True, proportion=1)

        # These are used for copy and paste, and drag and drop
        self.DragItem = None
        self.CutNode = None
        self.CopyNode = None
        self.inLabelEdit = False
        self.selectedFileLastModifiedTime = 0
        
        # Note: themes are deprecated, code is left only until it can be removed safely.
        self.themes = themes.ThemeList()
        self.currentTheme = self.themes.FindTheme("epub")
        self.launchApps = []
        self.loaded = False
        
        # Modeless dialog
        self.find_dialog = None

        self.log = logging.getLogger('EClass')

        self.statusBar = None #self.CreateStatusBar()

        if sys.platform.startswith("win"):
            self.SetIcon(wx.Icon(os.path.join(settings.AppDir, "icons", "brightwriter.ico"), wx.BITMAP_TYPE_ICO))

        #load icons
        imagepath = os.path.join(settings.AppDir, "icons", "fatcow")
        icnNewProject = wx.Bitmap(os.path.join(imagepath, "book_add.png"))
        icnOpenProject = wx.Bitmap(os.path.join(imagepath, "book_open.png"))
        icnSaveProject = wx.Bitmap(os.path.join(imagepath, "book_save.png"))

        icnNewPage = wx.Bitmap(os.path.join(imagepath, "page_add.png"))
        icnSavePage = wx.Bitmap(os.path.join(imagepath, "page_save.png"))
        icnPageProps = wx.Bitmap(os.path.join(imagepath, "page_gear.png"))
        icnDeletePage = wx.Bitmap(os.path.join(imagepath, "page_delete.png"))

        icnPublishWeb = wx.Bitmap(os.path.join(imagepath, "server_go.png"))
        icnPublishCD = wx.Bitmap(os.path.join(imagepath, "cd_go.png"))
        icnHelp = wx.Bitmap(os.path.join(imagepath, "help.png"))

        self.treeimages = wx.ImageList(15, 15)

        # NOTE: We used this function to enable us to create both AUI and native toolbars with
        # the same code. We are not using AUI toolbars currently, but leaving this code for
        # later refactoring after we finalize our UI for the release.
        def AddToToolBar(self, id=-1, bitmap=wx.EmptyBitmap, label="", shortHelpString=""):
            if isinstance(self, aui.AuiToolBar):
                self.AddTool(id, label, bitmap, bitmap, kind=wx.ITEM_NORMAL, short_help_string=shortHelpString)
            else:
                self.AddSimpleTool(id, bitmap, label, shortHelpString)

        wx.ToolBar.AddToToolBar = AddToToolBar
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        #create toolbar
        self.toolbar.AddToToolBar(ID_NEW, bitmap=icnNewProject, label=_("New"), shortHelpString=_("Create a New Project"))
        self.toolbar.AddToToolBar(ID_OPEN, bitmap=icnOpenProject, label=_("Open"), shortHelpString=_("Open an Existing Project")) 
        self.toolbar.AddSeparator()
        self.toolbar.AddToToolBar(ID_ADD_MENU, bitmap=icnNewPage, label=_("New Page"), shortHelpString=_("Adds a New EClass Page"))
        self.toolbar.AddToToolBar(ID_TREE_EDIT, bitmap=icnPageProps, label=_("Page Properties"), shortHelpString=_("View and Edit Page Properties"))
        self.toolbar.AddToToolBar(ID_SAVE, bitmap=icnSavePage, label=_("Save Page"), shortHelpString=_("Save the current page"))
        self.toolbar.AddToToolBar(ID_TREE_REMOVE, bitmap=icnDeletePage, label=_("Delete Page"), shortHelpString=_("Delete Currently Selected Page"))
        self.toolbar.AddSeparator()
        self.toolbar.AddToToolBar(ID_PUBLISH_CD, bitmap=icnPublishCD, label=_("Publish to CD-ROM"), shortHelpString=_("Publish to CD-ROM"))
        self.toolbar.AddToToolBar(ID_PUBLISH, bitmap=icnPublishWeb, label=_("Publish to web site"), shortHelpString=_("Publish to web site"))
        #self.toolbar.AddToToolBar(ID_PUBLISH_PDF, icnPublishPDF, _("Publish to PDF"), _("Publish to PDF"))
        self.toolbar.AddSeparator()
        self.toolbar.AddToToolBar(ID_HELP, bitmap=icnHelp, label=_("View Help"), shortHelpString=_("View Help File"))
        self.searchCtrl = wx.SearchCtrl(self.toolbar, -1, size=(200,-1))
        self.toolbar.AddControl(self.searchCtrl)

        self.toolbar.SetToolBitmapSize(wx.Size(32,32))

        self.toolbar.Realize()

        if sys.platform.startswith("darwin"):
            wx.App.SetMacPreferencesMenuItemId(ID_SETTINGS)

        self.SetMenuBar(menus.getMenuBar())

        if not IMPORT_FROM_URL_AVAILABLE:
            self.GetMenuBar().Enable(ID_IMPORT_FROM_URL, False)

        if not KOLIBRI_EXPORT_AVAILABLE:
            self.GetMenuBar().Enable(ID_PUBLISH_KOLIBRI_STUDIO, False)

        #split the window into two - Treeview on one side, browser on the other
        parent = self
        if not self._mgr:
            self.splitter1 = wx.SplitterWindow(pane, -1, style=wx.NO_BORDER)

            # self.splitter1.SetMinSize((800, 500))
            # self.splitter1.SetSashSize(7)
            self.splitter1.SetSizerProps(expand=True, proportion=1)
            parent = self.splitter1

        # Tree Control for the XML hierachy
        self.projectTree = gui.imstree.IMSCPTreeControl(parent,
                    -1,
                    style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT | wx.SIMPLE_BORDER | wx.TR_EDIT_LABELS)
        
        if self._mgr:
            self._mgr.AddPane(self.projectTree, aui.AuiPaneInfo().Caption("Contents").Layer(1).Resizable(True).MinSize(200, -1).Left().MinimizeButton(True).CloseButton(False).Position(1).CaptionVisible(True))
        #self.projectTree.SetImageList(self.treeimages)

        #handle delete key
        accelerators = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_TREE_REMOVE)])
        self.SetAcceleratorTable(accelerators)

        if self._mgr:
            self.nb = aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP)
            parent = self.nb

        self.browser = wxbrowser.wxBrowser(parent, -1, messageHandler=self)
        self.preview_browser = wxbrowser.wxBrowser(parent, -1)

        if self._mgr:
            self.nb.AddPage(self.browser, "Edit")
            self.nb.AddPage(self.preview_browser, "Preview")
            self._mgr.AddPane(self.nb, aui.AuiPaneInfo().Center().Position(2).Layer(1).DockFixed(False).CaptionVisible(False))
        
        self.Bind(wx.EVT_MENU, self.OnCleanHTML, id=ID_CLEANUP_HTML)
        pub.subscribe(self.OnPageLoaded, 'page_load_complete')
        pub.subscribe(self.OnContentChanged, 'html_content_changed')

        if not self._mgr:
            self.splitter1.SetMinimumPaneSize(200)
            self.splitter1.SplitVertically(self.projectTree, self.browser, 300)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.OnTreeSelChanging, self.projectTree)        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged, self.projectTree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnTreeLabelChanged, self.projectTree)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.OnTreeItemContextMenu, self.projectTree)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch, self.searchCtrl)

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
        
        self.RegisterHandlers()
        
        # we make this the fallback handler in case no other handlers are set.
        self.RegisterTreeHandlers()

        app_server.start_server()

        self.save_timer = None

        self.editor_url = app_server.SERVER_URL + "app/index.html"
        self.browser.LoadPage(self.editor_url)
        self.preview_browser.LoadPage(self.editor_url)

        if self._mgr:
            self._mgr.Update()

    def OnContentChanged(self):
        if not self.save_timer:
            self.save_timer = threading.Timer(5, self.SaveWebPage)
            self.save_timer.start()

    def BrowseFiles(self, args):
        print("browseFiles called with args %r" % args)
        self.browseFilesReturnArgs = args

        dialog = wx.FileDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            path = guiutils.importFile(dialog.GetPath())
            # FIXME: Make a constant for the Content dir and use that here.
            path = path.replace(settings.ProjectDir + "\\Content\\", "").replace("\\", "/")
            js = "CKEDITOR.tools.callFunction(%r, '%s');" % (self.browseFilesReturnArgs['CKEditorFuncNum'][0], path)
            print("Running JS %s" % js)
            self.browser.EvaluateJavaScript(js)


        return True

    def OnDoSearch(self, event):
        # wx bug: event.GetString() doesn't work on Windows 
        text = event.GetEventObject().GetValue()
        pub.sendMessage(('search', 'text', 'changed'), message=text)

    def OnPageLoaded(self):
        logging.info("Page loaded callback called")
        if not self.loaded:
            self.loaded = True
            self.browser.EvaluateJavaScript("ResizeEditor()")
            self.LoadCurrentItemContent()
            if settings.AppSettings["LastOpened"] != "" and os.path.exists(settings.AppSettings["LastOpened"]):
                self.LoadEClass(settings.AppSettings["LastOpened"])
        
    def OnFindReplace(self, event):
        from . import find_replace_dialog
        
        if not self.find_dialog:
            self.find_dialog = find_replace_dialog.FindReplaceDialog(self, -1, _("Find and Replace"))
            self.find_dialog_controller = find_replace_dialog.WebViewFindReplaceController(self.browser)
        
        self.find_dialog.CentreOnScreen()
        self.find_dialog.Show()

    def OnChanged(self, event):
        self.dirty = True
        
    def OnActivityMonitor(self, evt):
        self.activityMonitor.Show()

    def OnAbout(self, event):
        EClassAboutDialog(self).ShowModal()

    def GetCommandState(self, command):
        state = self.browser.GetEditCommandState(command)
        if state and state.lower().strip() == "true":
            return True
        
        return False

    def RegisterTreeHandlers(self):
        app = wx.GetApp()
        # app.AddHandlerForID(ID_CUT, self.OnCut)
        # app.AddHandlerForID(ID_COPY, self.OnCopy)
        app.AddHandlerForID(ID_PASTE_BELOW, self.OnPaste)
        app.AddHandlerForID(ID_PASTE_CHILD, self.OnPaste)
        #app.AddHandlerForID(ID_PASTE, self.OnPaste)

    def RemoveTreeHandlers(self):
        app = wx.GetApp()
        app.RemoveHandlerForID(ID_CUT)
        app.RemoveHandlerForID(ID_COPY)
        app.RemoveHandlerForID(ID_PASTE_BELOW)
        app.RemoveHandlerForID(ID_PASTE_CHILD)
        app.RemoveHandlerForID(ID_PASTE)

    def RegisterHandlers(self):
        app = wx.GetApp()
        app.AddHandlerForID(ID_NEW, self.OnNewContentPackage)
        app.AddHandlerForID(ID_OPEN, self.OnOpen)
        app.AddHandlerForID(ID_SAVE, self.OnSave)
        app.AddHandlerForID(ID_CLOSE, self.OnCloseProject)
        app.AddHandlerForID(ID_PROPS, self.OnProjectProps)
        app.AddHandlerForID(ID_TREE_REMOVE, self.RemoveItem)
        app.AddHandlerForID(ID_TREE_EDIT, self.OnEditItemProps) 
        app.AddHandlerForID(ID_EDIT_ITEM, self.EditItem)
        app.AddHandlerForID(ID_IMPORT_PACKAGE, self.OnImportIMS)
        app.AddHandlerForID(ID_PUBLISH, self.PublishToWeb)
        app.AddHandlerForID(ID_PUBLISH_CD, self.PublishToCD)
        app.AddHandlerForID(ID_PUBLISH_KOLIBRI_STUDIO, self.PublishToKolibriStudio)
        #app.AddHandlerForID(ID_PUBLISH_PDF, self.PublishToPDF)
        app.AddHandlerForID(ID_PUBLISH_IMS, self.PublishToIMS)
        app.AddHandlerForID(ID_PUBLISH_EPUB, self.PublishToEpub)
        app.AddHandlerForID(ID_BUG, self.OnReportBug)
        app.AddHandlerForID(ID_THEME, self.OnManageThemes)
        
        app.AddHandlerForID(ID_ADD_MENU, self.OnNewItem)
        app.AddHandlerForID(ID_TREE_MOVEUP, self.OnMoveItemUp)
        app.AddHandlerForID(ID_TREE_MOVEDOWN, self.OnMoveItemDown)
        app.AddHandlerForID(ID_HELP, self.OnHelp)
        app.AddHandlerForID(ID_LINKCHECK, self.OnLinkCheck)
        app.AddHandlerForID(ID_FIND, self.OnFindReplace)
        app.AddHandlerForID(ID_IMPORT_FILE, self.OnImportFile)
        app.AddHandlerForID(ID_IMPORT_FROM_URL, self.OnImportFromURL)
        app.AddHandlerForID(ID_REFRESH_THEME, self.OnRefreshTheme)
        app.AddHandlerForID(ID_EDIT_SOURCE, self.OnEditSource)
        #wx.EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
        app.AddHandlerForID(ID_ERRORLOG, self.OnErrorLog)
        app.AddHandlerForID(ID_ACTIVITY, self.OnActivityMonitor)
        app.AddHandlerForID(ID_CONTACTS, self.OnContacts)
        
        app.AddHandlerForID(ID_SETTINGS, self.OnAppPreferences)
        app.AddHandlerForID(wx.ID_ABOUT, self.OnAbout)

        # edit commands
        #for id in command_ids:
        #    app.AddHandlerForID(id, self.OnEditCommandClicked)
        
        app.AddUIHandlerForID(ID_SAVE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_CLOSE, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PREVIEW, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_REFRESH_THEME, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH_MENU, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_PUBLISH_CD, self.UpdateProjectCommand)
        #app.AddUIHandlerForID(ID_PUBLISH_PDF, self.UpdateProjectCommand)
        
        app.AddUIHandlerForID(ID_PROPS, self.UpdateProjectCommand)
        app.AddUIHandlerForID(ID_LINKCHECK, self.UpdatePageCommand)
        
        # app.AddUIHandlerForID(ID_CUT, self.UpdatePageCommand)
        # app.AddUIHandlerForID(ID_COPY, self.UpdatePageCommand)
        # app.AddUIHandlerForID(ID_PASTE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_FIND_IN_PROJECT, self.UpdatePageCommand)
        
        app.AddUIHandlerForID(ID_ADD_MENU, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_REMOVE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_IMPORT_FILE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_EDIT_ITEM, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_MOVEUP, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_MOVEDOWN, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_UPLOAD_PAGE, self.UpdatePageCommand)
        app.AddUIHandlerForID(ID_TREE_EDIT, self.UpdatePageCommand)
        
        pagemenu = self.GetMenuBar().FindMenu(_("Page"))

        app.AddUIHandlerForID(pagemenu, self.UpdatePageCommand)
        app.AddUIHandlerForID(self.GetMenuBar().FindMenu(_("Edit")), self.UpdatePageCommand)
        #wx.EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

        app.AddHandlerForID(ID_EXIT, self.OnCloseWindow)

    def RemoveHandlers(self):
        app = wx.GetApp()
        app.RemoveHandlerForID(ID_NEW)
        app.RemoveHandlerForID(ID_OPEN)
        app.RemoveHandlerForID(ID_SAVE)
        app.RemoveHandlerForID(ID_CLOSE)
        app.RemoveHandlerForID(ID_PROPS)
        app.RemoveHandlerForID(ID_TREE_REMOVE)
        app.RemoveHandlerForID(ID_TREE_EDIT) 
        app.RemoveHandlerForID(ID_EDIT_ITEM)
        app.RemoveHandlerForID(ID_IMPORT_PACKAGE)
        app.RemoveHandlerForID(ID_PUBLISH)
        app.RemoveHandlerForID(ID_PUBLISH_CD)
        #app.RemoveHandlerForID(ID_PUBLISH_PDF, self.PublishToPDF)
        app.RemoveHandlerForID(ID_PUBLISH_IMS)
        app.RemoveHandlerForID(ID_BUG)
        app.RemoveHandlerForID(ID_THEME)
        
        app.RemoveHandlerForID(ID_ADD_MENU)
        app.RemoveHandlerForID(ID_TREE_MOVEUP)
        app.RemoveHandlerForID(ID_TREE_MOVEDOWN)
        app.RemoveHandlerForID(ID_HELP)
        app.RemoveHandlerForID(ID_LINKCHECK)
        app.RemoveHandlerForID(ID_CUT)
        app.RemoveHandlerForID(ID_COPY)
        app.RemoveHandlerForID(ID_PASTE_BELOW)
        app.RemoveHandlerForID(ID_PASTE_CHILD)
        app.RemoveHandlerForID(ID_PASTE)
        app.RemoveHandlerForID(ID_IMPORT_FILE)
        app.RemoveHandlerForID(ID_REFRESH_THEME)
        #wx.EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
        app.RemoveHandlerForID(ID_ERRORLOG)
        app.RemoveHandlerForID(ID_ACTIVITY)
        app.RemoveHandlerForID(ID_CONTACTS)
        
        app.RemoveHandlerForID(ID_SETTINGS)
        #app.RemoveHandlerForID(wx.ID_ABOUT, self.OnAbout)
        
        app.RemoveUIHandlerForID(ID_SAVE)
        app.RemoveUIHandlerForID(ID_CLOSE)
        app.RemoveUIHandlerForID(ID_PREVIEW)
        app.RemoveUIHandlerForID(ID_REFRESH_THEME)
        app.RemoveUIHandlerForID(ID_PUBLISH_MENU)
        app.RemoveUIHandlerForID(ID_PUBLISH)
        app.RemoveUIHandlerForID(ID_PUBLISH_CD)
        app.RemoveUIHandlerForID(ID_PUBLISH_EPUB)
        app.RemoveUIHandlerForID(ID_PUBLISH_IMS)
        #app.RemoveUIHandlerForID(ID_PUBLISH_PDF)
        
        app.RemoveUIHandlerForID(ID_PROPS)
        app.RemoveUIHandlerForID(ID_THEME)
        app.RemoveUIHandlerForID(ID_LINKCHECK)
        
        app.RemoveUIHandlerForID(ID_FIND_IN_PROJECT)
        
        app.RemoveUIHandlerForID(ID_ADD_MENU)
        app.RemoveUIHandlerForID(ID_TREE_REMOVE)
        app.RemoveUIHandlerForID(ID_IMPORT_FILE)
        app.RemoveUIHandlerForID(ID_EDIT_ITEM)
        app.RemoveUIHandlerForID(ID_TREE_MOVEUP)
        app.RemoveUIHandlerForID(ID_TREE_MOVEDOWN)
        app.RemoveUIHandlerForID(ID_UPLOAD_PAGE)
        app.RemoveUIHandlerForID(ID_TREE_EDIT)
        
        pagemenu = self.GetMenuBar().FindMenu(_("Page"))

        app.RemoveUIHandlerForID(pagemenu)
        app.RemoveUIHandlerForID(self.GetMenuBar().FindMenu(_("Edit")))
        #wx.EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

    def OnHelp(self, event):
        import webbrowser
        url = os.path.join(settings.AppDir, "docs", settings.LangDirName, "web", "index.htm")
        webbrowser.open_new("file://" + url)

    def OnEditSource(self, event):
        dialog = source_edit_dialog.SourceEditDialog(self, -1, _("Page Source"), size=(500, 500), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dialog.SetSource(self.browser.GetPageSource())
        dialog.ShowModal()
        
        html = dialog.GetSource()
        
        if not html == self.browser.GetPageSource():
            self.LoadCurrentItemContent()
            self.dirty = True

    def OnIdle(self, event):
        event.Skip()
        if self.selectedFileLastModifiedTime > 0:
            try:
                filename = eclassutils.getEditableFileForIMSItem(self.imscp, self.projectTree.GetCurrentTreeItemData())
                if filename:
                    fullpath = os.path.join(settings.ProjectDir, filename)
                    if os.path.exists(fullpath):
                        modifiedTime = os.path.getmtime(fullpath)
                        if not modifiedTime <= self.selectedFileLastModifiedTime:
                            self.selectedFileLastModifiedTime = modifiedTime
                            result = wx.MessageBox(_("This page has been edited outside of EClass. Would you like to load the updated page? Any changes you've made since the last save will be lost."), _("Page Change Detected"), wx.YES_NO)
                            if result == wx.YES:
                                self.Update()
            except:
                raise

    def OnEditCommandClicked(self, event):
        command = command_ids[event.GetId()]
        self.browser.ExecuteEditCommand(command)

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

    def OnCleanHTML(self, event):
        try:
            import tidylib
        except:
            wx.MessageBox(_("Your system appears not to have the HTMLTidy library installed. Cannot run HTML clean up."))
            return
        
        html, errors = htmlutils.cleanUpHTML(self.browser.GetPageSource())
    
        dialog = cleanhtmldialog.HTMLCleanUpDialog(self, -1, size=(600,400), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dialog.SetOriginalHTML(self.browser.GetPageSource())
        dialog.SetCleanedHTML(html)
        dialog.log.SetValue(errors)
        if dialog.ShowModal() == wx.ID_OK:
            html = dialog.newSource.GetText()
            self.browser.LoadCurrentItemContent()
            self.dirty = True
            
        dialog.Destroy()

    def OnRefreshTheme(self, event):
        publisher = self.currentTheme.HTMLPublisher(self)
        result = publisher.Publish()
        errors = publisher.GetErrors()
        
        if errors:
            errorString = '\n\n'.join(errors)
            publishErrorsDialog = gui.error_viewer.PublishErrorLogViewer(self, errorString)
            publishErrorsDialog.Show()

    def OnImportFromURL(self, event):
        parent = self.projectTree.GetCurrentTreeItem()
        if parent:
            parentitem = self.projectTree.GetCurrentTreeItemData()
            try:
                dialog = ImportURLDialog()
                if dialog.ShowModal() == wx.ID_OK:
                    content_dir = os.path.join(settings.ProjectDir, 'Content', 'imported_content')
                    info = archive_page(dialog.url_ctrl.GetValue(), content_dir, relative_links=True)
                    info['root_dir'] = content_dir
                    self.AddNewContentItem(info, parentitem)
            finally:
                dialog.Destroy()

    def AddNewContentItem(self, content_info, parentitem):
        main_file = content_info['index_path']
        files = []
        if 'resources' in content_info:
            files.extend(content_info['resources'])
        # TODO: if resources aren't explicitly specified and it's webcontent,
        # scan the page for references and add any that are on disk.

        new_resource = ims.contentpackage.Resource()
        new_resource.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
        if os.path.splitext(main_file)[1].lower() in ['.html', '.xhtml', '.htm']:
            new_resource.attrs["type"] = "webcontent"
        else:
            new_resource.attrs["type"] = "other"

        new_resource.setFilename(os.path.relpath(main_file, settings.ProjectDir))

        for filename in files:
            if filename.startswith('http'):
                continue
            new_file = ims.contentpackage.File()
            abs_path = filename
            if not os.path.isabs(abs_path):
                if 'root_dir' in content_info:
                    abs_path = os.path.join(content_info['root_dir'], abs_path)
                else:
                    abs_path = os.path.join(settings.ProjectDir, abs_path)
            assert os.path.exists(abs_path), "Path {} for {} doesn't exist".format(abs_path, filename)

            packagefile = os.path.relpath(abs_path, settings.ProjectDir)
            new_file.attrs['href'] = packagefile

            new_resource.files.append(new_file)

        newitem = ims.contentpackage.Item()
        assert os.path.basename(main_file) is not None and os.path.basename(main_file) != ""

        titleString = os.path.basename(main_file)

        if os.path.splitext(main_file)[1].find("htm") != -1:
            titleString = htmlutils.getTitleForPage(os.path.join(settings.ProjectDir, main_file))

        newitem.title.text = titleString
        newitem.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
        newitem.attrs["identifierref"] = new_resource.attrs["identifier"]

        self.imscp.resources.append(new_resource)

        parentitem.items.append(newitem)
        self.projectTree.AddIMSItemUnderCurrentItem(newitem)

        self.EditItemProps()

    def OnImportFile(self, event):
        parent = self.projectTree.GetCurrentTreeItem()
        if parent:
            parentitem = self.projectTree.GetCurrentTreeItemData()
            
            dialog = wx.FileDialog(self)
            if dialog.ShowModal() == wx.ID_OK:
                packagefile = guiutils.importFile(dialog.GetPath())
                content_info = {
                    'index_path': packagefile
                }
                self.AddNewContentItem(content_info, parentitem)

    def OnImportIMS(self, event):
        dialog = wx.FileDialog(self, _("Select package to import"), "", "", _("Packages") + " (*.zip)|*.zip")
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            packagefile = dialog.GetPath()
            zip = zipfile.ZipFile(packagefile)
            if "imsmanifest.xml" in zip.namelist():
                subdir = os.path.splitext(os.path.basename(packagefile))[0]
                self.log.debug("Loading %s" % subdir)
                self.OpenIMSPackage(zip, subdir)
            else:
                wx.MessageBox(_("This file does not appear to be a valid package."))
        else:
            self.log.debug("Load cancelled, result is %r" % result)

    def OpenIMSPackage(self, zip, subdir):
        eclassdir = os.path.join(settings.AppSettings["ProjectsFolder"], subdir)
        if os.path.exists(eclassdir):
            result = wx.MessageBox(_("It appears you already have imported this package. Would you like to overwrite the existing package?"), _("Overwrite Package?"), wx.YES_NO)
            if result == wx.YES:
                shutil.rmtree(eclassdir)
            else:
                return
        
        self.log.debug("Extracting files to %s" % eclassdir)
        zip.extractall(eclassdir)
        self.LoadEClass(os.path.join(eclassdir, "imsmanifest.xml"))
                
    def OnCut(self, event):
        focus = wx.Window.FindFocus()
        if not focus == self.projectTree:
            if hasattr(focus, "Cut"):
                focus.Cut()
            return
            
        sel_item = self.projectTree.GetSelection()
        self.CutNode = sel_item
        self.projectTree.SetItemTextColour(sel_item, wx.LIGHT_GREY)
        if self.CopyNode:
            self.CopyNode = None

    def OnCopy(self, event):
        focus = wx.Window.FindFocus()
        if not focus == self.projectTree:
            if hasattr(focus, "Copy"):
                focus.Copy()
            event.Skip()
            return
        sel_item = self.projectTree.GetSelection()
        self.CopyNode = sel_item
        if self.CutNode:
            self.projectTree.SetItemTextColour(self.CutNode, wx.BLACK)
            self.CutNode = None #copy automatically cancels a cut operation

    def OnLinkCheck(self, event):
        checker = LinkChecker(self)
        checker.Show()
        checker.CheckLinks(self.browser.GetPageSource())

    def OnPaste(self, event):
        focus = wx.Window.FindFocus()
        if not focus == self.projectTree:
            if hasattr(focus, "Paste"):
                focus.Paste()
            return
        dirtyNodes = []
        sel_item = self.projectTree.GetSelection()
        parent = self.projectTree.GetItemParent(sel_item)
        pastenode = self.CopyNode
        if self.CutNode:
            pastenode = self.CutNode
        
        import copy
        pasteitem = copy.copy(self.projectTree.GetPyData(pastenode))

        newparent = None

        newitem = None
        
        # we need to check this before we actually paste the item
        hasChildren = self.projectTree.GetChildrenCount(pastenode, False) > 0

        if event.GetId() in [ID_PASTE_BELOW, ID_PASTE] and not parent == self.projectTree.GetRootItem():
            newitem = self.projectTree.InsertItem(self.projectTree.GetItemParent(sel_item), 
                                         sel_item, self.projectTree.GetItemText(pastenode), 
                                       -1, -1, wx.TreeItemData(self.projectTree.GetPyData(pastenode)))

            parentitem = self.projectTree.GetPyData(parent)
            beforeitem = self.projectTree.GetPyData(sel_item)
            assert(beforeitem)
            previndex = parentitem.items.index(beforeitem) + 1
            parentitem.items.insert(previndex, pasteitem)
            

        elif event.GetId() == ID_PASTE_CHILD or parent == self.projectTree.GetRootItem():
            newitem = self.projectTree.AppendItem(sel_item, self.projectTree.GetItemText(pastenode), 
                                                -1, -1, wx.TreeItemData(self.projectTree.GetPyData(pastenode)))
            
            parentitem = self.projectTree.GetCurrentTreeItemData()
            parentitem.children.append(pasteitem)
        
        assert(newitem)
        if hasChildren:
            self.CopyChildrenRecursive(pastenode, newitem)

        dirtyNodes.append(pasteitem)

        if self.CutNode:
            cutparent = self.projectTree.GetItemParent(self.CutNode)
            cutparentitem = self.projectTree.GetPyData(cutparent)
            cutitem = self.projectTree.GetPyData(pastenode)
            if cutitem in cutparentitem.items:
                cutparentitem.items.remove(cutitem)
            else:
                print(cutitem)
            self.projectTree.Delete(self.CutNode)
            self.CutNode = None

        for item in dirtyNodes:
            self.Update(item)
            
        self.SaveProject()

    def CopyChildrenRecursive(self, sel_item, new_item):
        thisnode = self.projectTree.GetFirstChild(sel_item)[0]
        while (thisnode.IsOk()):
            thisitem = self.projectTree.AppendItem(new_item, self.projectTree.GetItemText(thisnode), 
                                 -1, -1, wx.TreeItemData(self.projectTree.GetPyData(thisnode)))
            
            if not self.projectTree.GetChildrenCount(thisnode, False) == 0:
                self.CopyChildrenRecursive(thisnode, thisitem)
            thisnode = self.projectTree.GetNextSibling(thisnode) 

    def OnCloseProject(self, event):
        if self.imscp and self.imscp.isDirty():
            answer = self.PromptToSaveExistingProject()
            if answer == wx.ID_YES:
                self.SaveProject()
            elif answer == wx.ID_CANCEL:
                return
            else:
                self.imscp.clearDirtyBit()

        self.imscp = None
        self.projectTree.DeleteAllItems()
        settings.ProjectDir = ""
        settings.ProjectSettings = conman.xml_settings.XMLSettings()
        self.LoadCurrentItemContent()

    def OnManageThemes(self, event):
        ThemeManager(self).ShowModal()

    def OnMoveItemUp(self, event):
        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()
        parent = self.projectTree.GetItemParent(selection)
        parentitem = self.projectTree.GetPyData(parent)
        
        if parentitem:
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
                    self.projectTree.AddIMSChildItemsToTree(newitem, selitem.items)
                self.projectTree.SelectItem(newitem)
                self.Update()
                
                self.SaveProject()
                
    def OnMoveItemDown(self, event):
        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()
        parent = self.projectTree.GetItemParent(selection)
        parentitem = self.projectTree.GetPyData(parent)
        
        if parentitem:        
            index = parentitem.items.index(selitem)
            if index >= 0 and index < len(parentitem.items)-1:
                parentitem.items.remove(selitem)
                parentitem.items.insert(index + 1, selitem)
    
                insertafter = self.projectTree.GetNextSibling(selection)
                haschild = self.projectTree.ItemHasChildren(selection)
                
                self.projectTree.Delete(selection)
                newitem = self.projectTree.InsertItem(parent, insertafter, 
                                         selitem.title.text,-1,-1,wx.TreeItemData(selitem))
                if haschild:
                    self.projectTree.AddIMSChildItemsToTree(newitem, selitem.items)
                self.projectTree.SelectItem(newitem)
                self.Update()
                
                self.SaveProject()

    def OnOpen(self,event):
        """
        Handler for File-Open
        """
        
        if self.imscp and self.imscp.isDirty():
            answer = self.PromptToSaveExistingProject()
            if answer == wx.ID_YES:
                self.SaveProject()
            elif answer == wx.ID_CANCEL:
                return
            else:
                self.imscp.clearDirtyBit()
        
        defaultdir = ""
        if settings.AppSettings["ProjectsFolder"] != "" and os.path.exists(settings.AppSettings["ProjectsFolder"]):
            defaultdir = settings.AppSettings["ProjectsFolder"]

        dialog = wx.DirDialog(self, _("Choose a directory."), settings.AppSettings["ProjectsFolder"], style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            manifest = os.path.join(dialog.GetPath(), "imsmanifest.xml")
            if os.path.exists(manifest):
                try:
                    self.LoadEClass(manifest)
                except Exception as e:
                    import traceback
                    logging.error(traceback.format_exc())
                    wx.MessageBox(_("Unexpected error when reading project file."), _("Error loading project"))
            else:
                wx.MessageBox(_("This directory does not contain an imsmanifest.xml project file."))
        
        dialog.Destroy()

    def OnNewContentPackage(self, event):
        self.NewContentPackage()

    def OnProjectProps(self, event):
        props = ProjectPropsDialog(self)
        props.ShowModal()
        props.Destroy()
        
    def OnReportBug(self, event):
        gui.error_viewer.showErrorDialog()

    def OnTreeSelChanging(self, event):
        self.should_change = None
        self.SaveIfNeeded(event)
        while self.should_change is None:
            wx.SafeYield()

        if self.should_change is not None and not self.should_change:
            event.Veto()

    def SaveIfNeeded(self, event):
        filename = self.GetContentFilenameForSelectedItem()
        if not filename:
            self.should_change = True
            return
        ext_type = os.path.splitext(filename)[1][1:]
        if ext_type in editable_file_types:
            # We block here because this function is called when switching pages or shutting down
            # so we don't want to continue until save completes.
            self.SaveWebPage(block=True)

        self.should_change = True

    def OnTreeSelChanged(self, event):
        self.LoadCurrentItemContent()
        event.Skip()
        
    def OnLaunchWithApp(self, event):
        appname = self.pageMenu.FindItemById(event.GetId()).GetLabel()
        appfilename = self.launchapps[appname].filename
        abspath = os.path.join(settings.ProjectDir, self.GetContentFilenameForSelectedItem())
        
        if sys.platform.startswith("darwin"):
            os.system('open -a "%s" "%s"' % (appfilename, abspath)) 
        
    def OnTreeItemContextMenu(self, event):
        pt = event.GetPoint()
        item = event.GetItem()
        if item:
            filename = self.GetContentFilenameForSelectedItem()
            
            submenu = None
            
            abspath = os.path.join(settings.ProjectDir, filename)
            if use_launch:
                self.launchapps = launch.getAppsForFilename(abspath, role = "editor")
                if len(self.launchapps) < 1:
                    self.launchapps = launch.getAppsForFilename(abspath, role = "all")
                
                # Disable this until we can figure out the packaging issues
                if len(self.launchapps) > 0:
                    submenu = wx.Menu()
                    for item in self.launchapps:
                        id = wx.NewId()
                        submenu.Append(id, item)
                        self.Bind(wx.EVT_MENU, self.OnLaunchWithApp, id = id)

                else:
                    submenu = None
            
            self.pageMenu = menus.getPageMenu(openWithMenu=submenu, isPopup=True)
            
            self.PopupMenu(self.pageMenu, pt)
            self.launchapps = None
            self.pageMenu = None
            
    def OnTreeLabelChanged(self, event):
        item = self.projectTree.GetCurrentTreeItemData()
        if item and not event.IsEditCancelled():
            label = event.GetLabel()
            item.title.text = event.GetLabel()
            self.inLabelEdit = False
            self.SaveProject()
            self.UpdateTitle(label)
        
    def SkipNotebookEvent(self, evt):
        evt.Skip()
        
    def UpdateProjectCommand(self, event):
        value = not self.imscp is None
        event.Enable(value)
        
    def UpdatePageCommand(self, event):
        selection = self.projectTree.GetCurrentTreeItem()

        value = not selection is None
        
        if selection:
            if event.Id == ID_TREE_REMOVE:
                parent = self.projectTree.GetItemParent(selection)
                if parent == self.projectTree.GetRootItem():
                    value = False
                else:
                    value = True
        
        event.Enable(value)

    def UpdateEditCommand(self, event):
        event.Enable(True)

    def OnCloseWindow(self, event):
        self.ShutDown(event)

    def PromptToSaveExistingProject(self):
        msg = wx.MessageDialog(self, _("Would you like to save the current project before continuing?"),
                                        _("Save Project?"), wx.YES_NO | wx.CANCEL)
        return msg.ShowModal()

    def PublishToWeb(self, event):
        folder = os.path.join(settings.ProjectDir, "..")
        if settings.ProjectSettings["WebSaveDir"] == "":
            result = wx.MessageDialog(self, _("You need to specify a directory in which to store the web files.\nWould you like to do so now?"), _("Specify Web Save Directory?"), wx.YES_NO).ShowModal()
            if result == wx.ID_YES:
                dialog = wx.DirDialog(self, _("Choose a folder to store web files."), style=wx.DD_NEW_DIR_BUTTON)
                if dialog.ShowModal() == wx.ID_OK:
                    if dialog.GetPath().lower().startswith(settings.ProjectDir.lower()):
                        wx.MessageDialog(self, _("The web export directory cannot be within your project directory.\nPlease choose another location and try again."), _("Export Directory Not Valid"), wx.OK).ShowModal()
                        return
                    else:
                        folder = settings.ProjectSettings["WebSaveDir"] = dialog.GetPath()

            else:
                return
        else:
            folder = settings.ProjectSettings["WebSaveDir"]
            
        self.SaveProject()
        
        callback = GUIFileCopyCallback(self)
        self.maxfiles = fileutils.getNumFiles(settings.ProjectDir)
        self.filesCopied = 0
        self.dialog = wx.ProgressDialog(_("Copying Web Files"), _("Preparing to copy Web files...") + "                            ", self.maxfiles, style=wx.PD_APP_MODAL)

        epubPackage = epub.EPubPackage(self.imscp.organizations[0].items[0].title.text)
        epubPackage.imsToEPub(self.imscp)
        epubPackage.createEPubPackage(settings.ProjectDir, output_dir=folder, callback=callback)

        self.CopyWebFiles(folder)
        
        result = wx.MessageDialog(self, "Would you like to upload the web files to the server via FTP now?", _("Upload to web site?"), wx.YES_NO).ShowModal()
        
        if result == wx.ID_YES:
            mydialog = FTPUploadDialog(self, folder)
            mydialog.ShowModal()
            mydialog.Destroy()

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

        self.SaveProject()

        callback = GUIFileCopyCallback(self)
        self.maxfiles = fileutils.getNumFiles(settings.ProjectDir)
        self.filesCopied = 0
        self.dialog = wx.ProgressDialog(_("Copying CD Files"), _("Preparing to copy CD files...") + "                            ", maxfiles, style=wx.PD_APP_MODAL)

        fileutils.CopyFiles(settings.ProjectDir, folder, 1, callback)
        
        self.dialog.Destroy()
        self.dialog = None

        self.CopyWebFiles(folder)
        self.CopyCDFiles(folder)
        message = _("A window will now appear with all files that must be published to CD-ROM. Start your CD-Recording program and copy all files in this window to that program, and your CD will be ready for burning.")
        dialog = wx.MessageBox(message, _("Export to CD Finished"))
        
        guiutils.openFolderInGUI(folder)

    def PublishToPDF(self, event):
        myPublisher = PDFPublisher(self)
        myPublisher.Publish()
        command = ""
        if os.path.exists(myPublisher.pdffile):
            command = guiutils.getOpenCommandForFilename(myPublisher.pdffile)
        else:
            wx.MessageBox(_("There was an error publishing to PDF."))
            return
        
        if command and command != "":
            mydialog = wx.MessageDialog(self, _("Publishing complete. A PDF version of your EClass can be found at %(pdffile)s. Would you like to preview it now?") % {"pdffile": myPublisher.pdffile}, _("Preview PDF?"), wx.YES_NO)
            if mydialog.ShowModal() == wx.ID_YES:
                wx.Execute(command)
        else:
            wx.MessageBox(_("Publishing complete. A PDF version of your EClass can be found at %(pdffile)s.") % {"pdffile": myPublisher.pdffile}, _("Publishing Complete."))

    def OnFileChanged(self, filename):
        self.filesCopied += 1
        if self.filesCopied == self.maxfiles:
            self.dialog.Destroy()
            self.dialog = None

        if self.dialog:
            self.keepCopying = self.dialog.Update(self.filesCopied, "Copying: " + filename)

    def OnNewItem(self, event):
        self.CreateIMSResource()
    
    def CreateIMSResource(self, name=None):
        dialog = NewPageDialog(self)
        if name:
            dialog.txtTitle.SetValue(name)

        if dialog.ShowModal() == wx.ID_OK:
            pluginName = "Web Page"
            plugin = plugins.GetPlugin(pluginName)
            if plugin:
                filename = dialog.txtFilename.GetValue()
                plugin.CreateNewFile(os.path.join(settings.ProjectDir, filename), dialog.txtTitle.GetValue())
                newresource = ims.contentpackage.Resource()

                newresource.setFilename(filename)
                
                newresource.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                newresource.attrs["type"] = plugin.plugin_info["IMS Type"]
                
                self.imscp.resources.append(newresource)
                
                newitem = ims.contentpackage.Item()
                title = dialog.txtTitle.GetValue()
                assert title is not None and title != ""
                newitem.title.text = title
                newitem.attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                newitem.attrs["identifierref"] = newresource.attrs["identifier"]
                
                parentitem = self.projectTree.GetCurrentTreeItemData()
                if parentitem:
                    parentitem.items.append(newitem)
                else: 
                    self.imscp.organizations[0].items.append(newitem)

                newtreeitem = self.projectTree.AddIMSItemUnderCurrentItem(newitem)

                if not self.projectTree.GetSelection().IsOk() and self.projectTree.GetCount() == 1:
                    self.projectTree.SelectItem(self.projectTree.GetRootItem())

                self.SaveProject()

                self.isNewCourse = False
            dialog.Destroy()
            
    def CopyCDFiles(self, pubdir):
        #cleanup after old EClass versions
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.pyd"))
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.dll"))
        fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.exe"))

        fileutils.CopyFile("autorun.inf", os.path.join(settings.AppDir, "autorun"),pubdir)

    def ShutDown(self, event):
        try:
            self.SaveIfNeeded(event)

            if self.imscp and self.imscp.isDirty():
                self.SaveProject()

            settings.AppSettings.SaveAsXML(os.path.join(settings.PrefDir,"settings.xml"))

            # TODO: Make these utility windows and have their state saved and loaded
            # at app startup, shutdown
            if self.activityMonitor:
                self.activityMonitor.SaveState("ActivityMonitor")
                self.activityMonitor.Destroy()
            if self.errorViewer:
                self.errorViewer.SaveState("ErrorLogViewer")
                self.errorViewer.Destroy()

            if self._mgr:
                self.log.info("Calling mgr.UnInit")
                self._mgr.UnInit()

            self.browser.OnClose(event)
            self.Destroy()
        finally:
            if event:
                event.Skip()
        
    def SaveProject(self, event=None):
        """
        Runs when the user selects the Save option from the File menu
        """
        filename = self.imscp.filename
        if not filename or not os.path.exists(filename):
            filename = os.path.join(settings.ProjectDir, "imsmanifest.xml")
        

        if os.path.exists(filename):
            # check for references to resources no longer in the project, so we can clean them up
            resources = self.imscp.getDanglingResources()
            
            if len(resources) > 0:
                dialog = gui.ims_dialogs.IMSCleanUpDialog(self, -1, _("References to Unused Files in Project"))
                for resource in resources:
                    for afile in resource.files:
                        if "href" in afile.attrs:
                            dialog.filelist.WriteText(afile.attrs["href"] + "\n")
                        
                dialog.CentreOnParent()
                result = dialog.ShowModal()
                if result == wx.ID_CANCEL:
                    return
                    
                elif result == wx.ID_YES:
                    for resource in resources:
                        unused_dir = os.path.join(settings.ProjectDir, "Unused Files")
                            
                        for afile in resource.files:
                            if "href" in afile.attrs:
                                filepath = os.path.join(settings.ProjectDir, afile.attrs["href"])
                                
                                if os.path.exists(filepath):
                                    if not os.path.exists(unused_dir):
                                        os.makedirs(unused_dir)
                            
                                    destpath = os.path.join(unused_dir, afile.attrs["href"])
                                    destdir = os.path.dirname(destpath)
                                    if not os.path.exists(destdir):
                                        os.makedirs(destdir)
                                    
                                    os.rename(filepath, destpath)
                            
                        self.imscp.resources.remove(resource)
        
        try:
            if not self.imscp.saveAsXML(filename):
                wx.MessageBox(_("Unable to save project file. Make sure you have permission to write to the project directory."))
                
            if settings.ProjectSettings:
                settings.ProjectSettings.SaveAsXML(os.path.join(settings.ProjectDir, "settings.xml"))
        except IOError as e:
            message = _("Could not save EClass project file. Error Message is:")
            self.log.error(message)
            wx.MessageBox(message + str(e), _("Could Not Save File"))

    def OnSave(self, event):
        self.SaveWebPage()

    def SaveWebPage(self, block=False):
        if self.save_timer:
            self.save_timer.cancel()
            self.save_timer = None

        self.page_saved = False
        self.browser.EvaluateJavaScript("GetContents()", callback=self.DoSaveWebPage)
        if block:
            timeout = 10
            elapsed = 0
            import time
            start = time.time()
            while not self.page_saved:
                wx.GetApp().Yield(True)
                if time.time() - start > 10:
                    raise Exception("Page failed to save")

            if not self.page_saved:
                raise Exception("Error saving page.")

    def DoSaveWebPage(self, data):
        source = htmlutils.ensureValidXHTML(data)

        if self.filename.endswith(".xhtml"):
            wx.MessageBox("Internet Explorer will ask users to download HTML files with the XHTML extension. To resolve this issue, EClass will change the extension to .html.")
            basename, ext = os.path.splitext(self.filename)
            newfile = basename + ".html"
            
            os.rename(self.filename, newfile)
            self.filename = newfile
            
        if self.projectTree:
            imsitem = self.projectTree.GetCurrentTreeItemData()
            if imsitem:
                import ims.utils
                resource = ims.utils.getIMSResourceForIMSItem(self.imscp, imsitem)
                eclassutils.updateManifestLinkedFiles(resource, self.filename, source)
                if resource:
                    resource.setFilename(self.filename.replace(settings.ProjectDir + os.sep, "").replace("\\", "/"))

        encoding = htmlutils.GetEncoding(source)
        try:
            if not encoding:
                encoding = htmlutils.getCurrentEncoding()
            source = source.encode(encoding)
        except:
            raise
                
        afile = open(self.filename, "wb")
        afile.write(source)
        afile.close()
        
        self.selectedFileLastModifiedTime = os.path.getmtime(self.filename)
        self.dirty = False
        self.page_saved = True
        wx.CallAfter(self.PreviewCurrentItem)

    def NewContentPackage(self):
        """
        Routine to create a new project. 
        """
        if self.imscp and self.imscp.isDirty():
            answer = self.PromptToSaveExistingProject()
            if answer == wx.ID_YES:
                self.SaveProject()
            elif answer == wx.ID_CANCEL:
                return

        defaultdir = ""
        if settings.AppSettings["ProjectsFolder"] == "" or not os.path.exists(settings.AppSettings["ProjectsFolder"]):
            msg = wx.MessageBox(_("You need to specify a folder to store your course packages. To do so, select Options->Preferences from the main menu."),_("Course Folder not specified"))
            return
        else:
            newdialog = NewPubDialog(self)
            result = newdialog.ShowModal()
            if result == wx.ID_OK:
                self.imscp = ims.contentpackage.ContentPackage() # conman.ConMan()
                appdata.currentPackage = self.imscp
                settings.ProjectSettings = xml_settings.XMLSettings()
                self.projectTree.DeleteAllItems()
                self.browser.LoadPage("about:blank")
        
                settings.ProjectDir = newdialog.eclassdir.strip()
                contentDir = os.path.join(settings.ProjectDir, "Content")
                if not os.path.exists(contentDir):
                    os.makedirs(contentDir)
                
                filename = os.path.join(settings.ProjectDir, "imsmanifest.xml")
                lang = appdata.projectLanguage = "en-US"
                settings.ProjectSettings["Theme"] = "Default (frames)"
                
                self.imscp.metadata.lom.general.title[lang] = newdialog.txtTitle.GetValue()
                self.imscp.metadata.lom.general.description[lang] = newdialog.txtDescription.GetValue()
                self.imscp.metadata.lom.general.keyword[lang] = newdialog.txtKeywords.GetValue()
                
                self.imscp.organizations.append(ims.contentpackage.Organization())
                self.imscp.organizations[0].attrs["identifier"] = eclassutils.getItemUUIDWithNamespace()
                self.CreateIMSResource(self.imscp.metadata.lom.general.title[lang])
                if not self.imscp.saveAsXML(filename):
                    wx.MessageBox(_("Unable to save project file. Make sure you have permission to write to the project directory."))
                
                settings.AppSettings["LastOpened"] = filename

            newdialog.Destroy()
        
    def LoadEClass(self, filename):
        busy = wx.BusyCursor()
        if not os.path.exists(filename):
            self.errorPrompts.displayError(_("Could not find EClass file: %s") % filename)
            return
            
        try:
            self.selectedFileLastModifiedTime = 0
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
                appdata.currentPackage = self.imscp
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
                    self.projectTree.AddIMSItemsToTree(self.imscp.organizations[0])
                else:
                    raise Exception(_("No content tree found in project file."))
                
                self.currentTheme = self.themes.FindTheme("epub")
    
                self.SetFocus()
                settings.AppSettings["LastOpened"] = filename
                settings.ProjectSettings = settings.ProjectSettings
                viddir = os.path.join(settings.ProjectDir, "Video")
                auddir = os.path.join(settings.ProjectDir, "Audio")
                
                if os.path.exists(viddir) or os.path.exists(auddir):
                    self.errorPrompts.displayInformation(_("Due to new security restrictions in some media players, video and audio files need to be moved underneath of the 'pub' directory. EClass will now do this automatically and update your pages. Sorry for any inconvenience!"), _("Moving media files"))
                    if os.path.exists(viddir):
                        os.rename(viddir, os.path.join(settings.ProjectDir, "pub", "Video"))
                    
                    if os.path.exists(auddir):
                        os.rename(auddir, os.path.join(settings.ProjectDir, "pub", "Audio"))
                        
                if self.projectTree.GetCount() > 0:
                    self.projectTree.SetFocus()
                    firstItem = self.projectTree.GetFirstChild(self.projectTree.GetRootItem())[0]
                    self.projectTree.Expand(firstItem)
                    self.projectTree.SelectItem(firstItem, True)

                # Remove EClass files from the project or convert any without pub files.
                # Disabled because it needs more work, and this may be a very uncommonly needed feature.
                # Will revisit if there is a lot of need for this.
                # Without this, the old EClass files are simply ignored.
                # if eclassutils.IMSHasEClassPages(self.imscp):
                #     result = wx.MessageDialog(self,
                #         _("In order to support modern formats such as ePub, the EClass Page format used in previous versions has been replaced with an inline document editor. This EClass needs to be converted to use the new format."), _("EClass Page Format No Longer Supported"),
                #         wx.YES_NO | wx.ICON_INFORMATION).ShowModal()
                #
                #     if result == wx.ID_NO:
                #         wx.MessageBox(_("App will continue using the latest published version of the page."))
                #         return
                #
                #     publisher = self.currentTheme.HTMLPublisher(self)
                #     result = publisher.Publish()
                #     errors = publisher.GetErrors()
                #
                #     if errors:
                #         errorString = '\n\n'.join(errors)
                #         publishErrorsDialog = gui.error_viewer.PublishErrorLogViewer(self, errorString)
                #         publishErrorsDialog.Show()
                #
                #     shutil.copy(os.path.join(settings.ProjectDir, "imsmanifest.xml"), os.path.join(settings.ProjectDir, "imsmanifest-backup.xml"))
                #
                #     eclassutils.IMSRemoveEClassPages(self.imscp)
                
                self.LoadCurrentItemContent()
                    
        
        finally:
            del busy
    
    def EditItem(self, event=None):
        selitem = self.projectTree.GetCurrentTreeItemData()
        
        if selitem:
            filename = eclassutils.getEditableFileForIMSItem(self.imscp, selitem)
            isplugin = False
            result = wx.ID_CANCEL
            plugin = plugins.GetPluginForFilename(filename)
            if plugin:
                mydialog = plugin.EditorDialog(self, selitem)
                mydialog.ShowModal()
        
    def EditItemProps(self):
        selitem = self.projectTree.GetCurrentTreeItemData()
        seltreeitem = self.projectTree.GetCurrentTreeItem()
        if selitem:
            result = PagePropertiesDialog(self, selitem, None, os.path.join(settings.ProjectDir, "Text")).ShowModal()
            self.projectTree.SetItemText(seltreeitem, selitem.title.text)
            self.Update()
            self.UpdateTitle(selitem.title.text)

            self.SaveProject()

    def UpdateTitle(self, title):
        self.browser.EvaluateJavaScript("document.getElementById('page_title').innerText = '%s'; dirty=true;" % title)

    def RemoveItem(self, event):
        if not self.projectTree.HasFocus():
            event.Skip()
            return

        selection = self.projectTree.GetCurrentTreeItem()
        selitem = self.projectTree.GetCurrentTreeItemData()        
        
        if selection:
            parent = self.projectTree.GetItemParent(selection)
            parentitem = self.projectTree.GetPyData(parent)
            assert parentitem
            
            mydialog = wx.MessageDialog(self, _("Are you sure you want to delete this page? Deleting this page also deletes any sub-pages or terms assigned to this page."), 
                                             _("Delete Page?"), wx.YES_NO)

            if mydialog.ShowModal() == wx.ID_YES:                
                # FIXME: how are we hitting a situation where this isn't true?
                if selitem in parentitem.items:
                    resourceid = selitem.attrs["identifierref"]
                    parentitem.items.remove(selitem)
                    for resource in self.imscp.resources:
                        if resource.attrs["identifier"] == resourceid:
                            datadialog = wx.MessageDialog(self, _("Would you like to delete the data files associated with this page?"), _("Delete data files?"), wx.YES_NO)
                            # TODO: recurse to handle child items
                            if datadialog.ShowModal() == wx.ID_YES:
                                for afile in resource.files:
                                    if "href" in afile.attrs:
                                        fullpath = os.path.join(settings.ProjectDir, afile.attrs["href"])
                                        if os.path.exists(fullpath):
                                            os.remove(fullpath)
                            
                            self.imscp.resources.remove(resource)
                            break
                next_focus = self.projectTree.GetNextSibling(selection)
                if not next_focus:
                    next_focus = self.projectTree.GetPrevSibling(selection)
                
                self.projectTree.Delete(selection)
                self.SaveProject()

                if next_focus:
                    self.projectTree.SelectItem(next_focus)
                    self.Update()

    def GetIMSResourceForSelectedItem(self):
        resource = None
        if self.projectTree:
            imsitem = self.projectTree.GetCurrentTreeItemData()
            if imsitem:
                import ims.utils
                resource = ims.utils.getIMSResourceForIMSItem(self.imscp, imsitem)

        return resource

    def GetContentFilenameForSelectedItem(self):
        resource = self.GetIMSResourceForSelectedItem()
        if resource:
            return resource.getFilename().replace("\\", "/")
        
        return None

    def GetDiskPathForSelectedItem(self):
        filename = self.GetContentFilenameForSelectedItem()
        if filename:
            return os.path.join(settings.ProjectDir, filename)

        return None

    def LoadCurrentItemContent(self):
        filename = self.GetDiskPathForSelectedItem()
        settings.current_project_file = filename
        self.log.info("LoadCurrentItemContent called for {}".format(filename))

        js = None
        if filename:
            try:
                self.selectedFileLastModifiedTime = os.path.getmtime(filename)
            except:
                self.selectedFileLastModifiedTime = 0

            ext = os.path.splitext(filename)[1][1:]
            if os.path.exists(filename):
                if not ext in editable_file_types:
                    js = "ShowEditError('{}')".format(filename)

                if ext.find("htm") != -1:
                    html = htmlutils.getUnicodeHTMLForFile(filename)
                    self.contents_on_load = html
                    baseurl = os.path.dirname(filename).replace(settings.ProjectDir, '')
                    js = 'SetEditorContents(%s);' % json.dumps({"content": html, "basehref": baseurl})
                    self.filename = filename

                self.PreviewCurrentItem(filename)
            else:
                js = 'ShowErrorMessage("<h3>The file {} cannot be found.</h3>")'.format(filename)
        else:
            js = 'ShowErrorMessage("This item has no file associated with it.")'
        if js:
            self.log.info(f"Running JS {js[:100]}")
            self.browser.EvaluateJavaScript(js)

    def PreviewCurrentItem(self, filename=None):
        if not filename:
            filename = self.GetDiskPathForSelectedItem()
        relative_path = filename.replace(settings.ProjectDir, '')
        flask_url = app_server.SERVER_URL + urllib.parse.quote(relative_path)

        ext = os.path.splitext(filename)[1][1:]
        preview_js = 'PreviewFile("{}")'.format(flask_url)
        if not ext in previewable_file_types:
            preview_js = 'ShowErrorMessage("<h3>Unable to preview file {}</h3>")'.format(filename)

        self.preview_browser.EvaluateJavaScript(preview_js)

    def Update(self, imsitem = None):
        if imsitem == None:
            imsitem = self.projectTree.GetCurrentTreeItemData()

        self.PreviewCurrentItem()
        self.dirtyNodes.append(imsitem)
            
    def CopyWebFiles(self, output_dir):
        result = False
        busy = wx.BusyCursor()
        # utils.CreateJoustJavascript(self.imscp.organizations[0].items[0], output_dir)
        # utils.CreateiPhoneNavigation(self.imscp.organizations[0].items[0], output_dir)
        self.currentTheme = self.themes.FindTheme("epub")
        if self.currentTheme:
            self.currentTheme.HTMLPublisher(self, output_dir).CopySupportFiles()
            
        del busy

        return True

    def PublishToEpub(self, event):
        deffilename = fileutils.MakeFileName2(self.imscp.organizations[0].items[0].title.text) + ".epub"
        dialog = wx.FileDialog(self, _("Export ePub package"), "", deffilename, _("ePub Files") + " (*.epub)|*.epub", wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.GetPath().lower().startswith(settings.ProjectDir.lower()):
                wx.MessageBox(_("ePub file cannot be saved inside of the project directory. Please choose another location"), _("Invalid Save Directory"))
                return

            import epub
            epubPackage = epub.EPubPackage(self.imscp.organizations[0].items[0].title.text)
            epubPackage.imsToEPub(self.imscp)
            epubPackage.createEPubPackage(settings.ProjectDir, dialog.GetPath())
            
            wx.MessageBox(_("Finished exporting!"))

    def PublishToIMS(self, event):
        #zipname = os.path.join(settings.ProjectDir, "myzip.zip")
        if self.DoIMSExport():
            wx.MessageBox("Finished exporting!")

    def PublishToKolibriStudio(self, event):
        def export_studio_task(data):
            try:
                zip_file = ims.zip_packaging.export_package_as_zip(os.path.dirname(self.imscp.filename))
                export.kolibri.export_project_to_kolibri_studio(zip_file, data['studio_token'], handler)
                os.remove(zip_file)
                wx.PostEvent(dialog, wxDoneEvent(message="Task complete!"))
            except Exception as e:
                logging.error(e)

        def export_local_task(data):
            zip_file = ims.zip_packaging.export_package_as_zip(os.path.dirname(self.imscp.filename))
            export.kolibri.export_project_to_kolibri_db(zip_file, data['directory'], handler)
            os.remove(zip_file)
            wx.PostEvent(dialog, wxDoneEvent(message="Task complete!"))

        with KolibriExportDialog() as export_dialog:
            if export_dialog.ShowModal() == wx.ID_OK:
                export_data = {}
                if export_dialog.export_studio_radio.GetValue() == True:
                    token = export_dialog.studio_token.GetValue().strip()
                    if not token:
                        wx.MessageBox("Please enter a valid API token in order to upload to Studio.")
                        return
                    settings.AppSettings['StudioAPIToken'] = token
                    settings.AppSettings.SaveAsXML()
                    export_data['task_func'] = export_studio_task
                    export_data['task_args'] = {
                        'studio_token': token
                    }
                elif export_dialog.export_kolibri_radio.GetValue() == True:
                    export_data['task_func'] = export_local_task
                    export_data['task_args'] = {
                        'directory': export_dialog.dir_picker.GetPath()
                    }
                with TaskDialog(task_data=export_data, parent=self) as dialog:
                    handler = wxLogHandler(dialog)
                    dialog.ShowModal()

    def DoIMSExport(self):
        deffilename = fileutils.MakeFileName2(self.imscp.organizations[0].items[0].title.text) + ".zip"
        dialog = wx.FileDialog(self, _("Export IMS Content Package"), "", deffilename, _("IMS Content Package Files") + " (*.zip)|*.zip", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK: 
            return ims.zip_packaging.export_package_as_zip(os.path.dirname(self.imscp.filename), dialog.GetPath())

        return None
