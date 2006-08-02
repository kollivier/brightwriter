#!/usr/bin/env python

import sys, urllib2, cPickle
import string, time, cStringIO, os, re, glob, csv, shutil

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
	rootdir = os.path.dirname(rootdir)

# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
			"en": gettext.translation('eclass', localedir, languages=['en']), 
			"es": gettext.translation('eclass', localedir, languages=['es']),
			"fr": gettext.translation('eclass', localedir, languages=['fr'])
			}

import wx
import wxaddons.persistence
import wxaddons.sized_controls as sc

hasmozilla = True
try:
	from wxPython.mozilla import *
except:
	hasmozilla = False

import settings
settings.AppDir = rootdir

import xml.dom.minidom

import ftplib
import themes.themes as themes
import conman.xml_settings as xml_settings
import conman.vcard as vcard
from convert.PDF import PDFPublisher
import wxbrowser

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

# Import the gui dialogs. They used to be embedded in editor.py
# so we will just import their contents for now to avoid conflicts.
# In the future, I'd like to not do things this way so that we can
# examine the code to find module dependencies.
import wx.lib.mixins.listctrl
import wx.lib.newevent
import taskrunner

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

ID_NEW = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_EXIT = wx.NewId()
ID_CUT = wx.NewId()
ID_COPY = wx.NewId()
ID_PASTE = wx.NewId()
ID_PASTE_BELOW = wx.NewId()
ID_PASTE_CHILD = wx.NewId()
ID_EDIT_AUTHORS = wxNewId()
ID_PROPS = wx.NewId()
ID_NEW_CONTACT = wx.NewId()
ID_TREE_ADD = wx.NewId()
ID_TREE_REMOVE = wx.NewId()
ID_TREE_EDIT = wx.NewId()
ID_SETTINGS = wx.NewId()
ID_EDIT_ITEM = wx.NewId()
ID_PREVIEW = wx.NewId()
ID_CREATE_ECLS_LINK = wx.NewId()
ID_TREE_ADD_ECLASS = wx.NewId()
ID_ADD_MENU = wx.NewId()
ID_IMPORT_FILE = wx.NewId()
ID_PUBLISH = wx.NewId()
ID_PUBLISH_CD = wx.NewId()
ID_PUBLISH_PDF = wx.NewId()
ID_PUBLISH_IMS = wx.NewId()
ID_PUBLISH_MENU = wx.NewId()
ID_TREE_MOVEUP = wx.NewId()
ID_TREE_MOVEDOWN = wx.NewId()
ID_HELP = wx.NewId()
ID_CLOSE = wx.NewId()
ID_BUG = wx.NewId()
ID_THEME = wx.NewId()
ID_LINKCHECK = wx.NewId()
ID_REFRESH_THEME = wx.NewId()
ID_UPLOAD_PAGE = wx.NewId()
ID_CONTACTS = wx.NewId()
ID_ERRORLOG = wx.NewId()
ID_ACTIVITY = wx.NewId()
ID_FIND_IN_PROJECT = wxNewId()

from constants import *

try:
	import win32api
	import win32pipe
except:
	pass

try:
	import pythoncom
except:
	pass

#----------------------------- MainFrame Class ----------------------------------------------

class MainFrame2(sc.SizedFrame): 
	def __init__(self, parent, ID, title):
		busy = wx.BusyCursor()
		sc.SizedFrame.__init__(self, parent, ID, title, size=wxSize(780,580), 
		              style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN)
		
		# the default encoding isn't correct for Mac.
		if wx.Platform == "__WXMAC__":
			wx.SetDefaultPyEncoding("utf-8")
		
		self.CurrentFilename = ""
		self.isDirty = False
		self.isNewCourse = False
		self.CurrentItem = None #current node
		self.CurrentTreeItem = None
		self.pub = conman.ConMan()
		#dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
		self.dirtyNodes = []

		settings.ThirdPartyDir = os.path.join(settings.AppDir, "3rdparty", utils.getPlatformName())

		# These are used for copy and paste, and drag and drop
		self.DragItem = None
		self.CutNode = None
		self.CopyNode = None
		
		self.themes = themes.ThemeList(os.path.join(settings.AppDir, "themes"))
		self.currentTheme = self.themes.FindTheme("Default (no frames)")
		
		wx.InitAllImageHandlers()

		import errors
		self.log = errors.appErrorLog

		settings.PrefDir = guiutils.getAppDataDir()
		oldprefdir = guiutils.getOldAppDataDir()

		# Move old AppDataDir if it exists.
		if oldprefdir and os.path.exists(oldprefdir) and not oldprefdir == settings.PrefDir:
			try:
				fileutils.CopyFiles(oldprefdir, settings.PrefDir, 1)
				shutil.rmtree(oldprefdir)
			except:
				self.log.write(_("Error moving preferences."))

		settings.AppSettings = xml_settings.XMLSettings()
		if os.path.exists(os.path.join(settings.PrefDir, "settings.xml")):
			settings.AppSettings.LoadFromXML(os.path.join(settings.PrefDir, "settings.xml"))

		contactsdir = os.path.join(settings.PrefDir, "Contacts")
		if not os.path.exists(contactsdir):
			os.mkdir(contactsdir)
		
		self.LoadLanguage()		
		self.LoadVCards()
		self.SetDefaultDirs()

		self.statusBar = self.CreateStatusBar()

		if sys.platform.startswith("win"):
			self.SetIcon(wx.Icon(os.path.join(settings.AppDir, "icons", "eclass_builder.ico"), wx.BITMAP_TYPE_ICO))

		#load icons
		icnNewProject = wx.Bitmap(os.path.join(settings.AppDir, "icons", "book_green16.gif"), wx.BITMAP_TYPE_GIF)
		icnOpenProject = wx.Bitmap(os.path.join(settings.AppDir, "icons", "open16.gif"), wx.BITMAP_TYPE_GIF)
		icnSaveProject = wx.Bitmap(os.path.join(settings.AppDir, "icons", "save16.gif"), wx.BITMAP_TYPE_GIF)

		icnNewPage = wx.Bitmap(os.path.join(settings.AppDir, "icons", "new16.gif"), wx.BITMAP_TYPE_GIF)
		icnEditPage = wx.Bitmap(os.path.join(settings.AppDir, "icons", "edit16.gif"), wx.BITMAP_TYPE_GIF)
		icnPageProps = wx.Bitmap(os.path.join(settings.AppDir, "icons", "properties16.gif"), wx.BITMAP_TYPE_GIF)
		icnDeletePage = wx.Bitmap(os.path.join(settings.AppDir, "icons", "delete16.gif"), wx.BITMAP_TYPE_GIF)

		icnPreview = wx.Bitmap(os.path.join(settings.AppDir, "icons", "doc_map16.gif"), wx.BITMAP_TYPE_GIF)
		icnPublishWeb = wx.Bitmap(os.path.join(settings.AppDir, "icons", "ftp_upload16.gif"), wx.BITMAP_TYPE_GIF)
		icnPublishCD = wx.Bitmap(os.path.join(settings.AppDir, "icons", "cd16.gif"), wx.BITMAP_TYPE_GIF)
		icnPublishPDF = wx.Bitmap(os.path.join(settings.AppDir, "icons", "pdf.gif"), wx.BITMAP_TYPE_GIF)
		icnHelp = wx.Bitmap(os.path.join(settings.AppDir, "icons", "help16.gif"), wx.BITMAP_TYPE_GIF)

		self.treeimages = wx.ImageList(15, 15)
		imagepath = os.path.join(settings.AppDir, "icons")
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

		# File menu
		FileMenu = wx.Menu()
		FileMenu.Append(ID_NEW, "&" + _("New"), _("Create a New Project"))
		FileMenu.Append(ID_OPEN, "&" +_("Open"), _("Open an Existing Project"))
		FileMenu.Append(ID_SAVE, "&" + _("Save"), _("Save the Current Project"))
		FileMenu.Append(ID_CLOSE, "&" + _("Close"), _("Close the Current Project"))
		FileMenu.AppendSeparator()
		
		PrevMenu = wx.Menu()
		PrevMenu.Append(ID_PREVIEW, _("Web Browser"),  _("Preview EClass in web browser"))
		FileMenu.AppendMenu(wx.NewId(), _("Preview"), PrevMenu)
		
		FileMenu.Append(ID_REFRESH_THEME, _("Refresh Theme"), "Reapply current theme to pages.")
		FileMenu.AppendSeparator()
		
		PubMenu = wx.Menu()
		PubMenu.Append(ID_PUBLISH, _("To web site"), _("Publish EClass to a web server"))
		PubMenu.Append(ID_PUBLISH_CD, _("To CD-ROM"), _("Publish EClass to a CD-ROM"))
		PubMenu.Append(ID_PUBLISH_PDF, _("To PDF"))
		PubMenu.Append(ID_PUBLISH_IMS, _("IMS Package"))
		FileMenu.AppendMenu(ID_PUBLISH_MENU, "&" + _("Publish"), PubMenu, "")
		
		FileMenu.AppendSeparator()
		FileMenu.Append(ID_PROPS, _("Project Settings"), _("View and edit project settings"))
		FileMenu.AppendSeparator()
		FileMenu.Append(ID_EXIT, "&" + _("Exit"), _("Exit this Application"))
		self.FileMenu = FileMenu

		# Edit menu
		EditMenu = wx.Menu()
		EditMenu.Append(ID_CUT, _("Cut")+"\tCTRL+X")
		EditMenu.Append(ID_COPY, _("Copy")+"\tCTRL+C")

		PasteMenu = wx.Menu()
		PasteMenu.Append(ID_PASTE_BELOW, _("Paste After")+"\tCTRL+V")
		PasteMenu.Append(ID_PASTE_CHILD, _("Paste As Child"))
		EditMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu)
		
		#EditMenu.AppendSeparator()
		#EditMenu.Append(ID_FIND_IN_PROJECT, _("Find in Project"))

		#create the PopUp Menu used when a user right-clicks on an item
		self.PopMenu = wx.Menu()
		self.PopMenu.Append(ID_ADD_MENU, _("Add New"))
		self.PopMenu.Append(ID_TREE_REMOVE, _("Remove Page"), _("Remove the current page"))		
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_IMPORT_FILE, _("Import file..."))
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_CUT, _("Cut"))
		self.PopMenu.Append(ID_COPY, _("Copy"))
		
		PasteMenu2 = wx.Menu()
		PasteMenu2.Append(ID_PASTE_BELOW, _("Paste Below")+"\tCTRL+V")
		PasteMenu2.Append(ID_PASTE_CHILD, _("Paste As Child"))
		self.PopMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu2)
		
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_EDIT_ITEM, _("Edit Page"), _("Edit the currently selected page"))	
		self.PopMenu.Append(ID_TREE_MOVEUP, _("Move Page Up"), _("Move the selected page higher in the tree"))
		self.PopMenu.Append(ID_TREE_MOVEDOWN, _("Move Page Down"), _("Move the selected page lower in the tree"))	
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_UPLOAD_PAGE, _("Upload Page"), _("Upload Page to FTP Server"))
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_TREE_EDIT, _("Page Properties"), _("Edit Page Properties"))
		
		ToolsMenu = wx.Menu()
		ToolsMenu.Append(ID_THEME, _("Change Theme"))
		ToolsMenu.Append(ID_LINKCHECK, _("Check Links"))
		ToolsMenu.Append(ID_CONTACTS, _("Manage Contacts"))
		ToolsMenu.Append(ID_ERRORLOG, _("Error Viewer"))
		ToolsMenu.Append(ID_ACTIVITY, _("Activity Monitor"), _("View status of background activties."))
		ToolsMenu.AppendSeparator()
		ToolsMenu.Append(ID_SETTINGS, _("Options"), _("Modify Program Options"))
		if sys.platform.startswith("darwin"):
			wx.App.SetMacPreferencesMenuItemId(ID_SETTINGS)

		HelpMenu = wx.Menu()
		HelpMenu.Append(wx.ID_ABOUT, _("About Eclass"), _("About Eclass.Builder"))
		HelpMenu.Append(ID_HELP, _("Help"), _("EClass.Builder Help"))
		HelpMenu.Append(ID_BUG, _("Provide Feedback"), _("Submit feature requests or bugs"))


		menuBar = wx.MenuBar()
		menuBar.Append(FileMenu, "&"+ _("File"))
		menuBar.Append(EditMenu, _("Edit"))
		menuBar.Append(self.PopMenu, "&" + _("Page"))
		menuBar.Append(ToolsMenu, "&" + _("Tools"))
		menuBar.Append(HelpMenu, "&" + _("Help"))
		
		self.menuBar = menuBar
		self.SetMenuBar(menuBar)
		self.SwitchMenus(False)
		
		pane = self.GetContentsPane()
		#split the window into two - Treeview on one side, browser on the other
		self.splitter1 = wx.SplitterWindow(pane, -1)
		self.splitter1.SetSizerProps({"expand":True, "proportion":1})

		# Tree Control for the XML hierachy
		self.projectTree = wx.TreeCtrl(self.splitter1,
					-1 ,
					style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.SIMPLE_BORDER)

		#self.projectTree.SetImageList(self.treeimages)
		droptarget = wxTreeDropTarget(self, self.projectTree)
		self.projectTree.SetDropTarget(droptarget)

		#handle delete key
		accelerators = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_TREE_REMOVE)])
		self.SetAcceleratorTable(accelerators)

		self.previewbook = wx.Notebook(self.splitter1, -1, style=wx.CLIP_CHILDREN)
		
		self.splitter1.SplitVertically(self.projectTree, self.previewbook, 200)

		# TODO: This really needs fixed once webkit issues are worked out
		self.browsers = {}
		browsers = wxbrowser.browserlist
		if len(browsers) == 1 and browsers[0] == "htmlwindow":
			self.browsers["htmlwin"] = self.browser = wx.HtmlWindow(self.previewbook, -1)
			self.previewbook.AddPage(self.browser, _("HTML Preview"))
		else:
			if "htmlwindow" in browsers:
				browsers.remove("htmlwindow")
			default = "mozilla"
			if sys.platform.startswith("win") and "ie" in browsers:
				default = "ie"
			elif sys.platform.startswith("darwin") and "webkit" in browsers:
				default = "webkit"
			
			for browser in browsers:
				#panel = sc.SizedPanel(self.previewbook, -1)
				self.browser = self.browsers[browser] = wxbrowser.wxBrowser(self.previewbook, -1, browser)
				#self.browser.browser.SetSizerProps({"expand": True, "proportion":1})
				self.previewbook.AddPage(self.browser.browser, self.browsers[browser].GetBrowserName())

		wx.EVT_MENU(self, ID_NEW, self.NewProject)
		wx.EVT_MENU(self, ID_SAVE, self.SaveProject)
		wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
		wx.EVT_MENU(self, ID_CLOSE, self.OnClose)
		wx.EVT_MENU(self, ID_EXIT, self.TimeToQuit)
		wx.EVT_MENU(self, ID_PROPS, self.LoadProps)
		wx.EVT_MENU(self, ID_TREE_REMOVE, self.RemoveItem)
		wx.EVT_MENU(self, ID_TREE_EDIT, self.EditItem) 
		wx.EVT_MENU(self, ID_EDIT_ITEM, self.EditFile) 
		wx.EVT_MENU(self, ID_PREVIEW, self.PublishIt) 
		wx.EVT_MENU(self, ID_PUBLISH, self.PublishToWeb)
		wx.EVT_MENU(self, ID_PUBLISH_CD, self.PublishToCD)
		wx.EVT_MENU(self, ID_PUBLISH_PDF, self.PublishToPDF)
		wx.EVT_MENU(self, ID_PUBLISH_IMS, self.PublishToIMS)
		wx.EVT_MENU(self, ID_BUG, self.ReportBug)
		wx.EVT_MENU(self, ID_THEME, self.ManageThemes)
		
		wx.EVT_MENU(self, ID_ADD_MENU, self.AddNewEClassPage)
		wx.EVT_MENU(self, ID_SETTINGS, self.EditPreferences)
		wx.EVT_MENU(self, ID_TREE_MOVEUP, self.MoveItemUp)
		wx.EVT_MENU(self, ID_TREE_MOVEDOWN, self.MoveItemDown)
		wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
		wx.EVT_MENU(self, ID_HELP, self.OnHelp)
		wx.EVT_MENU(self, ID_LINKCHECK, self.OnLinkCheck)
		wx.EVT_MENU(self, ID_CUT, self.OnCut)
		wx.EVT_MENU(self, ID_COPY, self.OnCopy)
		wx.EVT_MENU(self, ID_PASTE_BELOW, self.OnPaste)
		wx.EVT_MENU(self, ID_PASTE_CHILD, self.OnPaste)
		wx.EVT_MENU(self, ID_PASTE, self.OnPaste)
		wx.EVT_MENU(self, ID_IMPORT_FILE, self.AddNewItem)
		wx.EVT_MENU(self, ID_REFRESH_THEME, self.OnRefreshTheme)
		wx.EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
		wx.EVT_MENU(self, ID_ERRORLOG, self.OnErrorLog)
		wx.EVT_MENU(self, ID_CONTACTS, self.OnContacts)
		wx.EVT_MENU(self, ID_ACTIVITY, self.OnActivityMonitor)
		wx.EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

		wx.EVT_CLOSE(self, self.TimeToQuit)

		wx.EVT_RIGHT_DOWN(self.projectTree, self.OnTreeRightClick)
		wx.EVT_LEFT_DOWN(self.projectTree, self.OnTreeLeftClick)
		wx.EVT_LEFT_DCLICK(self.projectTree, self.OnTreeDoubleClick)
		
		self.SetMinSize(self.GetSizer().GetMinSize())

		if sys.platform.startswith("win"):
			# this nasty hack is needed because on Windows, the controls won't
			# properly layout until the frame is resized. 
			self.SetSize((self.GetSize()[0]+1, self.GetSize()[1]+1))
			
		if sys.platform.startswith("darwin"):
			self.FileMenu.FindItemById(ID_PUBLISH_PDF).Enable(False)
			self.toolbar.EnableTool(ID_PUBLISH_PDF, False)
		self.Show()
		
		self.activityMonitor = ActivityMonitor(self)
		self.activityMonitor.LoadState("ActivityMonitor")
		
		self.errorViewer = gui.error_viewer.ErrorLogViewer(self)
		self.errorViewer.LoadState("ErrorLogViewer")
		
		if wx.Platform == '__WXMSW__':
			EVT_CHAR(self.previewbook, self.SkipNotebookEvent)

		if settings.AppSettings["LastOpened"] != "" and os.path.exists(settings.AppSettings["LastOpened"]):
			self.LoadEClass(settings.AppSettings["LastOpened"])
			
		else:
			dlgStartup = StartupDialog(self)
			result = dlgStartup.ShowModal()
			dlgStartup.Destroy()
			
			if result == 0:
				self.NewProject(None)
			if result == 1:
				self.OnOpen(None)
			if result == 2:
				self.OnHelp(None)
				
	def OnActivityMonitor(self, evt):
		self.activityMonitor.Show()

	def OnFindInProject(self, evt):
		dlg = pfdlg.ProjectFindDialog(self)
		dlg.Show()
		
	def SkipNotebookEvent(self, evt):
		evt.Skip()

	def LoadLanguage(self):
		self.langdir = "en"
		if settings.AppSettings["Language"] == "English":
			self.langdir = "en"
		elif settings.AppSettings["Language"] == "Espanol":
			self.langdir = "es"
		elif settings.AppSettings["Language"] == "Francais":
			self.langdir = "fr"
		lang_dict[self.langdir].install()
		
	def LoadVCards(self):
		#load the VCards
		self.vcardlist = {}
		vcards = glob.glob(os.path.join(settings.PrefDir, "Contacts", "*.vcf"))
		errOccurred = False
		errCards = []
		for card in vcards:
			try:
				myvcard = vcard.VCard()
				myvcard.parseFile(os.path.join(settings.PrefDir, "Contacts", card))
				# accomodate for missing fields EClass expects
				if myvcard.fname.value == "":
					myvcard.fname.value = myvcard.name.givenName + " "
					if myvcard.name.middleName != "":
						myvcard.fname.value = myvcard.fname.value + myvcard.name.middleName + " "
					myvcard.fname.value = myvcard.fname.value + myvcard.name.familyName
				self.vcardlist[myvcard.fname.value] = myvcard
			except:
				self.log.write("Error loading vCard '%s'" % (card))
				errOccurred = True
				errCards.append(card)

		if errOccurred:
			message = _("EClass could not load the following vCards from your Contacts folder: %(badCards)s. You may want to try deleting these cards and re-creating or re-importing them.") % {"badCards":`errCards`}
			wx.MessageBox(message)
			
	def SetDefaultDirs(self):
		#check settings and if blank, apply defaults
		coursefolder = settings.AppSettings["CourseFolder"]
		gsdlfolder = settings.AppSettings["GSDL"]
		htmleditor = settings.AppSettings["HTMLEditor"]

		if coursefolder == "":
			settings.AppSettings["CourseFolder"] = guiutils.getEClassProjectsDir()

		if gsdlfolder == "":
			if sys.platform.startswith("win"):
				gsdlfolder = "C:\Program Files\gsdl"
			
			if os.path.exists(gsdlfolder):
				settings.AppSettings["GSDL"] = gsdlfolder		

		if htmleditor == "":
			if wxPlatform == '__WXMSW__':
				htmleditor = "C:\Program Files\OpenOffice.org1.0\program\oooweb.exe"
			
			if os.path.exists(htmleditor):
				settings.AppSettings["HTMLEditor"] = htmleditor
	
	def OnErrorLog(self, evt):
		self.errorViewer.Show()

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

	def OnPaste(self, event):
		dirtyNodes = []
		sel_item = self.projectTree.GetSelection()
		pastenode = self.CopyNode
		if self.CutNode:
			pastenode = self.CutNode
		
		import copy
		pasteitem = copy.copy(self.projectTree.GetPyData(pastenode))
		pasteitem.content = conman.CopyContent(pasteitem.content)
		self.pub.content.append(pasteitem.content)
		newparent = None
		if event.GetId() == ID_PASTE_BELOW or event.GetId() == ID_PASTE:
			newitem = self.projectTree.InsertItem(self.projectTree.GetItemParent(sel_item), 
			                             sel_item, self.projectTree.GetItemText(pastenode), 
			                           -1, -1, wx.TreeItemData(self.projectTree.GetPyData(pastenode)))
			
			beforenode = self.projectTree.GetPyData(sel_item)
			newparent = beforenode.parent
			beforenode.parent.children.insert(beforenode.parent.children.index(beforenode) + 1, pasteitem)

		elif event.GetId() == ID_PASTE_CHILD:
			newitem = self.projectTree.AppendItem(sel_item, self.projectTree.GetItemText(pastenode), 
			                                    -1, -1, wxTreeItemData(self.projectTree.GetPyData(pastenode)))
			
			parentnode = self.projectTree.GetPyData(sel_item)
			newparent = parentnode
			parentnode.children.append(pasteitem)
			
		if not self.projectTree.GetChildrenCount(pastenode, False) == 0:
			self.CopyChildrenRecursive(pastenode, newitem)

		dirtyNodes.append(pasteitem)

		if self.CutNode:
			if pasteitem.parent.children.count(pasteitem) > 0:
				pasteitem.parent.children.remove(pasteitem)
			else:
				self.log.write("Item's parent doesn't have it as a child?!")

			self.projectTree.Delete(self.CutNode)
			dirtyNodes.append(pasteitem.back())
			dirtyNodes.append(pasteitem.next())
			self.CutNode = None

		pasteitem.parent = newparent
		dirtyNodes.append(pasteitem.back())
		dirtyNodes.append(pasteitem.next())

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

	def OnPageChanged(self, evt):
		pagename = self.previewbook.GetPageText(evt.GetSelection())
		if pagename == "Mozilla/Netscape":
			self.browser = self.mozilla
		elif pagename == "Internet Explorer":
			self.browser = self.ie
		else:
			pass #leave self.browser alone
		self.Preview()
		evt.Skip()

	def OnContacts(self, event):
		ContactsDialog(self).ShowModal()

	def ManageThemes(self, event):
		ThemeManager(self).ShowModal()

	def ReportBug(self, event):
		import webbrowser
		webbrowser.open_new("http://sourceforge.net/tracker/?group_id=67634")

	def OnLinkCheck(self, event):
		LinkChecker(self).ShowModal()

	def OnTreeDrag(self, event):
		#event.Allow()
		sel_item, flags = self.projectTree.HitTest(event.GetPoint())
		self.projectTree.SelectItem(sel_item)
		self.DragItem = sel_item
		#data = wxTextDataObject()
		#data.SetText(self.projectTree.GetItemText(self.CurrentTreeItem))
		data = wx.CustomDataObject(wx.CustomDataFormat('EClassPage'))
		data.SetData(cPickle.dumps(self.CurrentItem, 1)) 
		
		dropsource = wxTreeDropSource(self.projectTree)
		dropsource.SetData(data) 
		result = dropsource.DoDragDrop(wx.Drag_AllowMove)
		if result == wx.DragMove or result == wx.DragCopy:
			print "Drag event occurred!"
		else:
			print "No drag event occurred!"

	def SwitchMenus(self, enable=True):
		value = 1
		if not enable:
			value = 0
		
		self.FileMenu.FindItemById(ID_SAVE).Enable(value)
		self.FileMenu.FindItemById(ID_CLOSE).Enable(value)
		self.FileMenu.FindItemById(ID_PREVIEW).Enable(value)
		self.FileMenu.FindItemById(ID_REFRESH_THEME).Enable(value)
		self.FileMenu.FindItemById(ID_PUBLISH_MENU).Enable(value)
		self.FileMenu.FindItemById(ID_PROPS).Enable(value)

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

		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Page")), value)
		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Edit")), value)
		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Tools")), value)
		if sys.platform.startswith("darwin"):
			#still needed?
			self.menuBar.Refresh()

	def OnClose(self, event):
		if self.isDirty:
			answer = self.CheckSave()
			if answer == wx.ID_YES:
				self.SaveProject(event)
			elif answer == wx.ID_CANCEL:
				return
			else:
				self.isDirty = False

		self.pub = None
		self.projectTree.DeleteAllItems()
		self.CurrentItem = None
		self.CurrentFilename = ""
		self.CurrentTreeItem = None
		settings.ProjectDir = ""
		settings.ProjectSettings = {}
		if sys.platform.startswith("win"):
			self.ie.Navigate("about:blank")
			self.mozilla.Navigate("about:blank")
		else:
			self.browser.SetPage("<HTML><BODY></BODY></HTML")
		self.SwitchMenus(False)

	def OnRefreshTheme(self, event):
		publisher = self.currentTheme.HTMLPublisher(self)
		result = publisher.Publish()

	def LoadProps(self, event):
		props = ProjectPropsDialog(self)
		props.ShowModal()
		props.Destroy()

	def EditAuthors(self, event):
		auth = EditAuthorsDialog(self)
		auth.ShowModal()
		auth.Destroy()

	def EditPreferences(self, event):
		PreferencesEditor(self).ShowModal()

	def OnAbout(self, event):
		EClassAboutDialog(self).ShowModal()

	def OnHelp(self, event):
		import webbrowser
		url = os.path.join(settings.AppDir, "docs", self.langdir, "index.htm")
		if not os.path.exists(url):
			url = os.path.join(settings.AppDir, "docs", "en", "manual", "index.htm")
		webbrowser.open_new("file://" + url)

	def NewProject(self, event):
		"""
		Routine to create a new project. 
		"""
		if self.CurrentFilename != "":
			answer = self.CheckSave()
			if answer == wx.ID_YES:
				self.SaveProject(event)
			elif answer == wx.ID_CANCEL:
				return
			else:
				self.isDirty = False

		defaultdir = ""
		if settings.AppSettings["CourseFolder"] == "" or not os.path.exists(settings.AppSettings["CourseFolder"]):
			msg = wx.MessageBox(_("You need to specify a folder to store your course packages. To do so, select Options->Preferences from the main menu."),_("Course Folder not specified"))
			return
		else:
			self.pub = conman.ConMan()
			result = NewPubDialog(self).ShowModal()
			if result == wx.ID_OK:
				self.isNewCourse = True
				self.projectTree.DeleteAllItems()
				self.CurrentFilename = os.path.join(settings.ProjectDir, "imsmanifest.xml")
				self.CurrentItem = self.pub.NewPub(self.pub.name, "English", settings.ProjectDir)
				settings.ProjectSettings = settings.ProjectSettings
				self.isDirty = True
				
				global eclassdirs
				for dir in eclassdirs:
					if not os.path.exists(os.path.join(settings.ProjectDir, dir)):
						os.mkdir(os.path.join(settings.ProjectDir, dir))

				self.BindTowxTree(self.pub.nodes[0])
				self.CurrentTreeItem = self.projectTree.GetRootItem()
				
				self.currentTheme = self.themes.FindTheme("Default (frames)")
				self.AddNewEClassPage(None, self.pub.name, True)

				self.SaveProject(event)	 
				publisher = self.currentTheme.HTMLPublisher(self)
				publisher.CopySupportFiles()
				publisher.CreateTOC()
				self.projectTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
				self.Preview()
				self.SwitchMenus(True)
	
	def TimeToQuit(self, event):
		self.ShutDown(event)

	def ShutDown(self, event):
		if self.isDirty:
			answer = self.CheckSave()
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

	def PublishToWeb(self, event):
		# Turn off search features before uploading.
		value = settings.ProjectSettings["SearchEnabled"]
		settings.ProjectSettings["SearchEnabled"] = ""
		self.UpdateTextIndex()
		self.UpdateContents()
		mydialog = FTPUploadDialog(self)
		mydialog.ShowModal()
		mydialog.Destroy()
		settings.ProjectSettings["SearchEnabled"] = value
		self.UpdateContents()

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

	def PublishToIMS(self, event):
		import zipfile
		import tempfile
		#zipname = os.path.join(settings.ProjectDir, "myzip.zip")
		deffilename = fileutils.MakeFileName2(self.pub.name) + ".zip"
		dialog = wx.FileDialog(self, _("Export IMS Content Package"), "", deffilename, _("IMS Content Package Files") + " (*.zip)|*.zip", wx.SAVE)
		if dialog.ShowModal() == wx.ID_OK: 
			imsdir = os.path.dirname(os.path.join(os.tempnam(), "IMSPackage"))
			imstheme = self.themes.FindTheme("IMS Package")
			publisher = imstheme.HTMLPublisher(self, imsdir)
			publisher.Publish()
			fileutils.CopyFiles(os.path.join(settings.ProjectDir, "File"), os.path.join(imsdir, "File"), 1)

			handle, zipname = tempfile.mkstemp()
			os.close(handle)
			if os.path.exists(dialog.GetPath()):
				os.remove(dialog.GetPath())
		
			myzip = zipfile.ZipFile(zipname, "w")
			self._DirToZipFile("", myzip)
			handle, imsfile = tempfile.mkstemp()
			os.close(handle)
			oldfile = self.pub.filename
			self.pub.SaveAsXML(imsfile, exporting=True)
			self.pub.filename = oldfile
			myzip.write(imsfile, "imsmanifest.xml")
			myzip.close()
			os.rename(zipname, dialog.GetPath())

		wx.MessageBox("Finished exporting!")
		
	def _DirToZipFile(self, dir, myzip):
		mydir = os.path.join(settings.ProjectDir, dir)
		if not os.path.basename(dir) in ["installers", "cgi-bin"]:
			for file in os.listdir(mydir):
				mypath = os.path.join(mydir, file)
				print 'dir: %s' % dir
				if os.path.isfile(mypath) and string.find(file, "imsmanifest.xml") == -1 and file[0] != ".":
					print "mypath %s, file %s" % (mypath, os.path.join(dir, file))
					myzip.write(str(mypath), str(os.path.join(dir, file)))
				elif os.path.isdir(mypath):
					self._DirToZipFile(os.path.join(dir, file), myzip)
		
	def UpdateTextIndex(self):
		searchEnabled = 0
		print "in index method"
		if not settings.ProjectSettings["SearchEnabled"] == "":
			searchEnabled = settings.ProjectSettings["SearchEnabled"]
		if int(searchEnabled) == 1:
			if settings.ProjectSettings["SearchProgram"] == "Lucene" and hasLucene:
				engine = indexer.SearchEngine(self, os.path.join(settings.ProjectDir, "index.lucene"), settings.ProjectDir)
				maxfiles = engine.numFiles - 1
				#import threading
				dialog = wx.ProgressDialog(_("Updating Index"), _("Preparing to update Index...") + "							 ", maxfiles, style=wx.PD_CAN_ABORT | wx.PD_APP_MODAL) 
				engine.IndexFiles(self.pub.nodes[0], dialog)

				dialog.Destroy()
				dialog = None

			elif settings.ProjectSettings["SearchProgram"] == "Greenstone":
				gsdl = settings.AppSettings["GSDL"]
				collect = os.path.join(gsdl, "collect")
				if sys.platform.startswith("win"):
					cddialog = UpdateIndexDialog(self, True)
					if not self.pub.pubid == "":
						eclassdir = os.path.join(collect, self.pub.pubid)
					else:
						message = _("You must enter a publication ID to enable the search function. You can specify a publication ID by selecting 'File->Project Settings' from the menu.")
						dialog = wx.MessageDialog(message, _("Publication ID Not Set"))
						return
					
					try:
						cddialog.UpdateIndex(eclassdir)
					except: 
						message = _("There was an unexpected error publishing your course. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
						self.log.write(message)
						dialog = wx.MessageBox(message, _("Could Not Publish EClass"), wx.OK).ShowModal()
						cddialog.Destroy()
					result = self.UpdateEClassDataFiles(self.pub.pubid)
				else:
					dialog = wx.MessageBox(_("Sorry, building a Greenstone CD from EClass is not yet supported on this platform."), 
					                               _("Cannot build Greenstone collection."))
					dialog.ShowModal()
					dialog.Destroy()

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
		self.UpdateEClassDataFiles(self.pub.pubid)
		self.UpdateTextIndex()
		self.CopyCDFiles()
		message = _("A window will now appear with all files that must be published to CD-ROM. Start your CD-Recording program and copy all files in this window to that program, and your CD will be ready for burning.")
		dialog = wx.MessageBox(message, _("Export to CD Finished"))

		#Open the explorer/finder window
		if sys.platform.startswith("win"):
			if settings.ProjectSettings["SearchProgram"] == "Greenstone":
				folder = os.path.join(settings.AppSettings["GSDL"], "tmp", "exported_collections")
		
		guiutils.openFolderInGUI(folder)

	def CopyCDFiles(self):
		try:
			#cleanup after old EClass versions
			fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.pyd"))
			fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.dll"))
			fileutils.DeleteFiles(os.path.join(settings.ProjectDir, "*.exe"))

			pubdir = settings.ProjectDir
			if settings.ProjectSettings["CDSaveDir"] != "":
				pubdir = settings.ProjectSettings["CDSaveDir"]

			if pubdir != settings.ProjectDir:
				fileutils.CopyFiles(settings.ProjectDir, pubdir, 1)

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

		except:
			message = _("Unable to copy CD support files to your publication directory. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
			self.log.write(message)
			wx.MessageBox(message, _("Could Not Copy CD Files"))
			return False
										
	def PublishIt(self, event):
		self.UpdateEClassDataFiles()
		import webbrowser
		webbrowser.open_new("file://" + os.path.join(settings.ProjectDir, "index.htm")) 
		
	def UpdateEClassDataFiles(self, pubid=""):
		result = False
		busy = wx.BusyCursor()
		wxYield()
		try:
			self.CreateDocumancerBook()
			self.CreateDevHelpBook()
			utils.CreateJoustJavascript(self.pub)

		except:
			message = _("There was an unexpected error publishing your course. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
			self.log.write(message)
			wx.MessageBox(message, _("Could Not Publish EClass"))
			return False
		del busy

		return True

	def UploadFiles(self, files):
		ftp = FTPUpload(self)
		dialog = wx.MessageDialog(self, _("Would you like to upload files associated with these pages?"), 
		                          _("Upload Dependent Files?"), wx.YES_NO)

		if dialog.ShowModal() == wx.ID_YES:
			for file in files[:]:
				if os.path.splitext(file)[1] == ".htm" or os.path.splitext(file)[1] == ".html":
					linkFinder = analyzer.ContentAnalyzer() 
					linkFinder.AnalyzeFile(os.path.join(settings.ProjectDir, file))
					for dep in linkFinder.fileLinks:
						depFile = dep.replace("file://", "")
						depFile = depFile.replace("../", "")
						if os.path.exists(os.path.join(settings.ProjectDir, depFile)) and not depFile in files:
							files.append(depFile)
				
		ftp.filelist = files
		self.SetStatusText(_("Uploading files..."))
		
		busy = wx.BusyCursor()
		try:
			ftp.GetUploadDirs(ftp.filelist)
			ftp.UploadFiles()
		except ftplib.all_errors, e:
			message = ftp.getFtpErrorMessage(e)
			self.log.write(message)
			wx.MessageBox(message)
		except:
			message = _("Unknown error uploading file(s).")
			self.SetStatusText(message)
			self.log.write(message)
		self.SetStatusText("")
		del busy

	def SaveProject(self, event):
		"""
		Runs when the user selects the Save option from the File menu
		"""
		if self.CurrentFilename == "":
			defaultdir = ""
			if settings.AppSettings["CourseFolder"] != "" and os.path.exists(settings.AppSettings["CourseFolder"]):
				defaultdir = settings.AppSettings["CourseFolder"]
			
			f = wx.FileDialog(self, _("Select a file"), defaultdir, "", "XML Files (*.xml)|*.xml", wx.SAVE)
			if f.ShowModal() == wx.ID_OK:
				self.CurrentFilename = f.GetPath()
				self.isDirty = False
			f.Destroy()
		
		self.CreateDocumancerBook()
		self.CreateDevHelpBook()

		try:
			self.pub.SaveAsXML(self.CurrentFilename)
			self.isDirty = False
		except IOError, e:
			message = _("Could not save EClass project file. Error Message is:")
			self.log.write(message)
			wx.MessageBox(message + str(e), _("Could Not Save File"))

	def CreateDevHelpBook(self):
		import devhelp
		converter = devhelp.DevHelpConverter(self.pub)
		converter.ExportDevHelpFile(os.path.join(settings.ProjectDir, "eclass.devhelp"))

	def CreateDocumancerBook(self):
		#update the Documancer book file
		filename = os.path.join(settings.ProjectDir, "eclass.dmbk")
		bookdata = utils.openFile(os.path.join(settings.AppDir,"bookfile.book.in")).read()
		bookdata = string.replace(bookdata, "<!-- insert title here-->", self.pub.name)
		if settings.ProjectSettings["SearchEnabled"] == "1" and settings.ProjectSettings["SearchProgram"] == "Lucene":
			bookdata = string.replace(bookdata, "<!-- insert index info here -->", "<attr name='indexed'>1</attr>\n	   <attr name='cachedir'>.</attr>")
		else: 
			bookdata = string.replace(bookdata, "<!-- insert index info here -->", "")
		try:
			myfile = utils.openFile(filename, "w")
			myfile.write(bookdata)
			myfile.close()
		except:
			message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":filename})
			self.log.write(message)
			wx.MessageBox(message, _("Could Not Save File"), wx.ICON_ERROR)

	def ReloadThemes(self):
		self.themes = []
		for item in os.listdir(os.path.join(settings.AppDir, "themes")):
			if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
				theme = string.replace(item, ".py", "")
				if theme != "BaseTheme":
					exec("import themes." + theme)
					exec("self.themes.append([themes." + theme + ".themename, '" + theme + "'])")		
		
	def RemoveItem(self, event):
		if not self.CurrentItem == self.pub.nodes[0] and self.projectTree.IsSelected(self.CurrentTreeItem):
			mydialog = wx.MessageDialog(self, _("Are you sure you want to delete this page? Deleting this page also deletes any sub-pages or terms assigned to this page."), 
			                                 _("Delete Page?"), wx.YES_NO)

			if mydialog.ShowModal() == wx.ID_YES:
				self.CurrentItem.parent.children.remove(self.CurrentItem)
				itemtodelete = self.CurrentTreeItem
				self.CurrentTreeItem = self.projectTree.GetItemParent(itemtodelete)
				self.projectTree.Delete(itemtodelete)
				self.CurrentTreeItem = self.projectTree.GetSelection()
				self.CurrentItem = self.projectTree.GetPyData(self.CurrentTreeItem)
				self.UpdateContents()
				self.Update()
				self.isDirty = True
				
	def AddNewItem(self, event):
		if self.CurrentItem and self.projectTree.IsSelected(self.CurrentTreeItem):
			parent = self.CurrentTreeItem
			newnode = conman.ConNode(conman.GetUUID(),None, self.pub.CurrentNode)
			try:
				dlg = PagePropertiesDialog(self, newnode, newnode.content, os.path.join(settings.ProjectDir, "File"))
				if dlg.ShowModal() == wx.ID_OK:
					self.pub.CurrentNode.children.append(newnode)
					self.pub.content.append(newnode.content)
					self.CurrentItem = newnode
					newitem = self.projectTree.AppendItem(self.CurrentTreeItem, 
					                   self.CurrentItem.content.metadata.name, -1, -1, 
					                   wx.TreeItemData(self.CurrentItem))
					
					if not self.projectTree.IsExpanded(self.CurrentTreeItem):
						self.projectTree.Expand(self.CurrentTreeItem)
					self.CurrentTreeItem = newitem
					self.projectTree.SelectItem(newitem)
					self.Update()
					self.Preview()
					self.isDirty = True
				dlg.Destroy()
			except:
				message = constants.createPageErrorMsg
				self.log.write(message)
				wx.MessageBox(message + constants.errorInfoMsg)
	
	def AddNewEClassPage(self, event, name="", isroot=False):
		if self.CurrentItem and self.projectTree.IsSelected(self.CurrentTreeItem) or self.isNewCourse:
			dialog = NewPageDialog(self)
			if name != "":
				dialog.txtTitle.SetValue(name)

			if dialog.ShowModal() == wx.ID_OK:
				pluginName = dialog.cmbType.GetStringSelection()
				plugin = plugins.GetPlugin(pluginName)
				if plugin and self.CurrentItem and self.CurrentTreeItem:
					if not isroot:
						parent = self.CurrentTreeItem
						newnode = self.pub.AddChild("", "")
					else:
						parent = None
						newnode = self.CurrentItem
					self.CurrentItem = newnode
					newnode.content.metadata.name = dialog.txtTitle.GetValue()
					newnode.content.filename = os.path.join(plugin.plugin_info["Directory"], dialog.txtFilename.GetValue())
					print "filename is: " + newnode.content.filename
					
					
					try:
						file = plugin.CreateNewFile(newnode.content.metadata.name, os.path.join(settings.ProjectDir, newnode.content.filename))
						if file: 
							if not isroot:
								newitem = self.projectTree.AppendItem(self.CurrentTreeItem, self.CurrentItem.content.metadata.name, 
								                                       -1, -1, wx.TreeItemData(self.CurrentItem))
								
								if not self.projectTree.IsExpanded(self.CurrentTreeItem):
									self.projectTree.Expand(self.CurrentTreeItem)
								self.CurrentTreeItem = newitem
								self.projectTree.SelectItem(newitem)
							else:
								self.projectTree.SetPyData(self.CurrentTreeItem, newnode)
							self.EditFile(None)
							self.UpdateContents()
						else:
							self.CurrentItem.parent.children.remove(self.CurrentItem)
					except:
						message = constants.createPageErrorMsg
						self.log.write(message)
						wx.MessageBox(message + constants.errorInfoMsg)
	
				self.isNewCourse = False
			dialog.Destroy()

	def EditItem(self, event):
		if self.CurrentItem and self.projectTree.IsSelected(self.CurrentTreeItem):
			result = PagePropertiesDialog(self, self.CurrentItem, self.CurrentItem.content, os.path.join(settings.ProjectDir, "Text")).ShowModal()
			self.projectTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
			self.Update()
			self.isDirty = True

	def PublishPage(self, page):
		if page != None:
			publisher = self.GetPublisher(page.content.filename)
			if publisher:
				publisher.Publish(self, page, settings.ProjectDir)
				
	def PublishPageAndChildren(self, page):
		self.PublishPage(page)
		for child in page.children:
			self.PublishPageAndChildren(child)

	def Update(self, myitem = None):
		if myitem == None:
			myitem = self.CurrentItem
		self.UpdateContents()
		try:
			self.PublishPage(myitem)

			self.Preview()
			self.dirtyNodes.append(myitem)
			if string.lower(settings.ProjectSettings["UploadOnSave"]) == "yes":
				self.UploadPage()
		except:
			message = _("Error updating page.") + constants.errorInfoMsg
			self.log.write(message)
			wx.MessageBox(message)

	def UploadPage(self, event = None):
		ftpfiles = []
		myitem = self.CurrentItem
		publisher = self.GetPublisher(myitem.content.filename)
		if publisher: 
			ftpfiles.append(publisher.GetFileLink(myitem.content.filename))
		else:
			ftpfiles.append(myitem.content.filename)

		#exec("mytheme = themes." + self.currentTheme[1])
		publisher = self.currentTheme.HTMLPublisher(self)
		if publisher.GetContentsPage() != "":
			ftpfiles.append(publisher.GetContentsPage())
		self.UploadFiles(ftpfiles)

	def UpdateContents(self):
		self.statusBar.SetStatusText(_("Updating table of contents..."))
		if not self.currentTheme:
			self.currentTheme = self.themes.FindTheme("Default (frames)")
		try:
			publisher = self.currentTheme.HTMLPublisher(self)
			result = publisher.CreateTOC()
		except IOError, e:
			message = utils.getStdErrorMessage("IOError", {"filename": e.filename, "type":"write"})
			self.log.write(message)
			wx.MessageBox(message, _("Could Not Save File"), wx.ICON_ERROR)
		except:
			pass #we shouldn't do this, but there may be non-fatal errors we shouldn't
				 #catch
		self.statusBar.SetStatusText("")

	def GetPublisher(self, filename):
		publisher = None
		plugin = plugins.GetPluginForFilename(filename)
		publisher = plugin.HTMLPublisher()
		return publisher

	def CreateCourseLink(self, event):
		defaultdir = ""
		if settings.AppSettings["CourseFolder"] != "" and os.path.exists(settings.AppSettings["CourseFolder"]):
			defaultdir = settings.AppSettings["CourseFolder"]
		
		f = wx.DirDialog(self, _("Please select a course"), defaultdir)
		#f = wxFileDialog(self, _("Please select a course"), defaultdir, "", "E-Class Files (imsmanifest.xml)|imsmanifest.xml", wxOPEN)
		if f.ShowModal() == wx.ID_OK:
			if os.path.exists(os.path.join(f.GetPath(), "imsmanifest.xml")):
				nodeid = "node" + str(len(self.CurrentItem.children) + 1)
				newnode = self.pub.AddChild(nodeid, "content" + str(len(self.pub.content) + 1))
				self.CurrentItem = newnode
				newpub = conman.ConMan()
				newpub.directory = f.GetPath()	
				newpub.LoadFromXML(os.path.join(f.GetPath(), "imsmanifest.xml"))
				newnode.pub = newpub
				newnode.content.filename = os.path.join(f.GetPath(), "imsmanifest.xml")

				self.InsertwxTreeChildren(self.CurrentTreeItem, [newpub.nodes[0]]) 
				self.isDirty = True
			else:
				wx.MessageBox(_("The folder you selected does not seem to contain an EClass Project."), 
				                _("Not a Valid EClass Project"))
		f.Destroy()
	
	def EditFile(self, event):
		try:
			if self.CurrentItem and self.projectTree.IsSelected(self.CurrentTreeItem):
				isplugin = False
				result = wx.ID_CANCEL
				plugin = plugins.GetPluginForFilename(self.CurrentItem.content.filename)
				if plugin:
					mydialog = plugin.EditorDialog(self, self.CurrentItem)
					result = mydialog.ShowModal()

				if result == wx.ID_OK:
					self.Update()
					self.projectTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
					self.isDirty = True
		except:
			message = _("There was an unknown error when attempting to start the page editor.")
			self.log.write(message)
			wx.MessageBox(message + constants.errorInfoMsg)
		
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
		
	def LoadEClass(self, filename):
		busy = wx.BusyCursor()
		if not os.path.exists(filename):
			wx.MessageBox(result, _("Could not find EClass file:") + filename)
			return
		
		settings.ProjectDir = os.path.dirname(filename)
		self.projectTree.DeleteAllItems()
		self.CurrentFilename = filename
		self.pub = conman.ConMan()
		result = self.pub.LoadFromXML(self.CurrentFilename)
		if result != "":
			wx.MessageDialog(self, result, _("Error loading XML file."))
		else:
			self.pub.directory = settings.ProjectDir
			settings.ProjectSettings = self.pub.settings
			global eclassdirs
			for dir in eclassdirs:
				subdir = os.path.join(self.pub.directory, dir)
				if not os.path.exists(subdir):
					os.mkdir(subdir)
			pylucenedir = os.path.join(self.pub.directory, "index.pylucene")
			if os.path.exists(pylucenedir):
				os.rename(pylucenedir, os.path.join(self.pub.directory, "index.lucene"))

			self.BindTowxTree(self.pub.nodes[0])
			self.CurrentItem = self.pub.nodes[0]
			self.CurrentTreeItem = self.projectTree.GetRootItem()
			mytheme = settings.ProjectSettings["Theme"]
			self.currentTheme = self.themes.FindTheme(mytheme)
			if not self.currentTheme:
				self.currentTheme = self.themes.FindTheme("Default (frames)")

			if settings.ProjectSettings["SearchProgram"] == "Swish-e":
				settings.ProjectSettings["SearchProgram"] = "Lucene"
				wx.MessageBox(_("The SWISH-E search program is no longer supported. This project has been updated to use the Lucene search engine instead. Run the Publish to CD function to update the index."))

			self.isDirty = False	 
			self.Preview()
			self.projectTree.SelectItem(self.projectTree.GetRootItem())
			
			self.SetFocus()
			self.SwitchMenus(True)
			settings.AppSettings["LastOpened"] = filename
			settings.ProjectSettings = settings.ProjectSettings
			viddir = os.path.join(settings.ProjectDir, "Video")
			auddir = os.path.join(settings.ProjectDir, "Audio")
			
			if os.path.exists(viddir) or os.path.exists(auddir):
				wx.MessageBox(_("Due to new security restrictions in some media players, video and audio files need to be moved underneath of the 'pub' directory. EClass will now do this automatically and update your pages. Sorry for any inconvenience!"), _("Moving media files"))
				os.rename(viddir, os.path.join(settings.ProjectDir, "pub", "Video"))
				os.rename(auddir, os.path.join(settings.ProjectDir, "pub", "Audio"))
				self.PublishPageAndChildren(self.pub.nodes[0])
				
		del busy
		

	def OnTreeRightClick(self, event):
		pt = event.GetPosition()
		item = self.projectTree.HitTest(pt)
		if item[1] & wx.TREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.projectTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem 
			self.projectTree.SelectItem(item[0])
			self.toolbar.EnableTool(ID_EDIT_ITEM, True)
			self.toolbar.EnableTool(ID_TREE_EDIT, True)
			self.toolbar.EnableTool(ID_ADD_MENU, True)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, True)

			if self.CurrentTreeItem == self.projectTree.GetRootItem():
				self.PopMenu.Enable(ID_TREE_REMOVE, False)
				self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			else:
				self.PopMenu.Enable(ID_TREE_REMOVE, True)
				self.toolbar.EnableTool(ID_TREE_REMOVE, True)

			self.PopupMenu(self.PopMenu, pt)
		elif not self.projectTree.GetSelection():
			self.CurrentItem = None
			self.CurrentTreeItem = None
			self.toolbar.EnableTool(ID_EDIT_ITEM, False)
			self.toolbar.EnableTool(ID_TREE_EDIT, False)
			self.toolbar.EnableTool(ID_ADD_MENU, False)
			self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, False)

	def OnTreeDoubleClick(self, event):
		pt = event.GetPosition()
		item = self.projectTree.HitTest(pt)

		if item[1] & wx.TREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.projectTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem 
			self.EditFile(event)
			self.Preview()

	def OnTreeLeftClick(self, event):
		if event.Dragging():
			event.Skip()
			return 

		pt = event.GetPosition()
		item = self.projectTree.HitTest(pt)
		
		if item[1] & wx.TREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.projectTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem
			self.projectTree.SelectItem(item[0]) 
			self.toolbar.EnableTool(ID_EDIT_ITEM, True)
			self.toolbar.EnableTool(ID_TREE_EDIT, True)
			self.toolbar.EnableTool(ID_ADD_MENU, True)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, True)

			if self.CurrentTreeItem == self.projectTree.GetRootItem():
				self.PopMenu.Enable(ID_TREE_REMOVE, False)
				self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			else:
				self.PopMenu.Enable(ID_TREE_REMOVE, True)
				self.toolbar.EnableTool(ID_TREE_REMOVE, True)

			self.Preview()
		elif not self.projectTree.GetSelection():
			self.CurrentItem = None
			self.CurrentTreeItem = None 
			self.toolbar.EnableTool(ID_EDIT_ITEM, False)
			self.toolbar.EnableTool(ID_TREE_EDIT, False)
			self.toolbar.EnableTool(ID_ADD_MENU, False)
			self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, False)
		event.Skip()

	def Preview(self):
		filename = self.CurrentItem.content.filename
		plugin = plugins.GetPluginForFilename(filename)
		publisher = plugin.HTMLPublisher()
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

	def BindTowxTree(self, root):
		wx.BeginBusyCursor()
		#treeimages = wxImageList(15, 15)
		#imagepath = os.path.join(settings.AppDir, "icons")
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "bookclosed.gif"), wxBITMAP_TYPE_GIF))
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "chapter.gif"), wxBITMAP_TYPE_GIF))
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "page.gif"), wxBITMAP_TYPE_GIF))
		#self.projectTree.AssignImageList(treeimages)
		self.projectTree.DeleteAllItems()
		#print root.content.metadata.name
		wxTreeNode = self.projectTree.AddRoot(
			root.content.metadata.name,
			-1,-1,
			wx.TreeItemData(root))
		if len(root.children) > 0:
			self.InsertwxTreeChildren(wxTreeNode, root.children)
		self.projectTree.Expand(wxTreeNode)
		wx.EndBusyCursor()
		
	def InsertwxTreeChildren(self,wxTreeNode, nodes):
		"""
		Given an xTree, create a branch beneath the current selection
		using an xTree
		"""
		for child in nodes:
			if child.pub:
				child = child.pub.nodes[0]
			myname = child.content.metadata.name
			NewwxNode = self.projectTree.AppendItem(wxTreeNode,
					myname,
					-1,-1,
					wx.TreeItemData(child))
			# Recurisive call to insert children of each child
			self.InsertwxTreeChildren(NewwxNode,child.children)
			#self.projectTree.Expand(NewwxNode)
		self.projectTree.Refresh()

	def MoveItemUp(self, event):
		item = self.CurrentItem
		previtem = self.CurrentItem.back()
		nextitem = self.CurrentItem.next()
		parent = self.CurrentItem.parent
		index = parent.children.index(self.CurrentItem)
		if index > 0:
			parent.children.remove(self.CurrentItem)
			self.CurrentItem = item
			parent.children.insert(index - 1, self.CurrentItem)

			treeparent = self.projectTree.GetItemParent(self.CurrentTreeItem)
			haschild = self.projectTree.ItemHasChildren(self.CurrentTreeItem)
			nextsibling = self.projectTree.GetPrevSibling(self.CurrentTreeItem)
			nextsibling = self.projectTree.GetPrevSibling(nextsibling)
			self.projectTree.Delete(self.CurrentTreeItem)
			self.CurrentTreeItem = self.projectTree.InsertItem(treeparent, nextsibling, 
			                         self.CurrentItem.content.metadata.name,-1,-1,wx.TreeItemData(item))
			if haschild:
				self.InsertwxTreeChildren(self.CurrentTreeItem, self.CurrentItem.children)
			self.projectTree.Refresh()
			self.projectTree.SelectItem(self.CurrentTreeItem)
			self.Update()
			self.Update(previtem)
			self.Update(nextitem)
				
	def MoveItemDown(self, event):
		item = self.CurrentItem
		parent = self.CurrentItem.parent
		previtem = self.CurrentItem.back()
		nextitem = self.CurrentItem.next()
		index = parent.children.index(self.CurrentItem)
		if index + 1 < len(parent.children):
			parent.children.remove(self.CurrentItem)
			self.CurrentItem = item
			parent.children.insert(index + 1, self.CurrentItem)

			treeparent = self.projectTree.GetItemParent(self.CurrentTreeItem)
			nextsibling = self.projectTree.GetNextSibling(self.CurrentTreeItem)
			haschild = self.projectTree.ItemHasChildren(self.CurrentTreeItem)
		
			self.projectTree.Delete(self.CurrentTreeItem)
			self.CurrentTreeItem = self.projectTree.InsertItem(treeparent, nextsibling, 
			                             self.CurrentItem.content.metadata.name,-1,-1,wx.TreeItemData(item))
			
			if haschild:
				self.InsertwxTreeChildren(self.CurrentTreeItem, self.CurrentItem.children)
			self.projectTree.Refresh()
			self.projectTree.SelectItem(self.CurrentTreeItem)
			self.Update()
			self.Update(previtem)
			self.Update(nextitem)

			self.dirtyNodes.append(self.CurrentItem)
			self.dirtyNodes.append(previtem)
			self.dirtyNodes.append(nextitem)

	def CheckSave(self):
		msg = wx.MessageDialog(self, _("Would you like to save the current project before continuing?"),
		                                _("Save Project?"), wx.YES_NO | wx.CANCEL)
		return msg.ShowModal()

class wxTreeDropSource(wx.DropSource):
	def __init__(self, tree):
		# Create a Standard wxDropSource Object
		wx.DropSource.__init__(self)
		# Remember the control that initiate the Drag for later use
		self.tree = tree

	def SetData(self, obj):
		wx.DropSource.SetData(self, obj)

	def GiveFeedback(self,effect):
		try:
			(windowx, windowy) = wx.GetMousePosition()
			(x, y) = self.tree.ScreenToClientXY(windowx, windowy)
			item = self.tree.HitTest((x, y))
		except:
			import traceback
			print traceback.print_exc()
		return False

class wxTreeDropTarget(wx.PyDropTarget):
	def __init__(self, parent, window):
		wx.PyDropTarget.__init__(self)
		self.projectTree = window
		self.parent = parent
		
		self.data = wx.CustomDataObject(wx.CustomDataFormat('EClassPage'))
		self.SetDataObject(self.data)

	def OnDragOver(self, x, y, result):
		item = self.projectTree.HitTest(wxPoint(x,y))
		#print "x, y = " + `x` + "," + `y` + ", result = " + `item[1]`
		if item[1] == wx.TREE_HITTEST_ONITEMLABEL or (wx.Platform == "__WXMAC__" and item[1] == 4160):
			#print "Select item called..."
			self.projectTree.SelectItem(item[0])
			return wx.DragMove
		else:
			return True

	def OnDrag(self, x, y):
		return True

	def OnData(self, x, y, result):
		item = self.projectTree.HitTest(wxPoint(x,y))

		if not item[1] == wx.TREE_HITTEST_ONITEMLABEL and not (wx.Platform == "__WXMAC__" and item[1] == 4160):
			print "not a legal drop spot..."
			return False

		if not item[0] == self.parent.DragItem and not item[0] == self.projectTree.GetRootItem():
			newtreeitem = None
			newitem = None
			previtem = None
			
			try:
				self.GetData()
				currentitem = cPickle.loads(self.data.GetData())

				self.projectTree.InsertItem(self.projectTree.GetItemParent(item[0]), item[0],
				                    currentitem.content.metadata.name, -1, -1, wx.TreeItemData(currentitem))

				previtem = self.projectTree.GetPyData(item[0])
				newitem = currentitem
				newitem.parent = previtem.parent
				previtem.parent.children.insert(previtem.parent.children.index(previtem) + 1, newitem)
				currentitem.parent.children.remove(currentitem)
				self.projectTree.Delete(self.parent.DragItem)
		
				self.parent.isDirty = True
			except: 

				message = "There was an error while moving the page. Please contact your systems administrator or send email to kevino@tulane.edu if this error continues to occur."
				self.parent.log.write(message)
				dialog = wx.MessageBox(message, "Error moving page")

		return wx.DragCopy
