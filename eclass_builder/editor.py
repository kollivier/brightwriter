#!/usr/bin/env python

import sys, urllib2, cPickle
import string, time, cStringIO, os, re, glob, csv, shutil

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
	rootdir = os.path.dirname(rootdir)

print "root is: " + rootdir
# do this first because other modules may rely on _()
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
			"en": gettext.translation('eclass', localedir, languages=['en']), 
			"es": gettext.translation('eclass', localedir, languages=['es']),
			"fr": gettext.translation('eclass', localedir, languages=['fr'])
			}

from wxPython.wx import *
from wxPython.lib import newevent

hasmozilla = True
try:
	from wxPython.mozilla import *
except:
	hasmozilla = False

import settings
settings.AppDir = rootdir

from wxPython.stc import * #this is for the HTML plugin

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

# Import the gui dialogs. They used to be embedded in editor.py
# so we will just import their contents for now to avoid conflicts.
# In the future, I'd like to not do things this way so that we can
# examine the code to find module dependencies.
import wxaddons.persistence
import wxaddons.sized_controls
import wx.lib.mixins.listctrl
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
except:
	pass

#dynamically import any plugin in the plugins folder and add it to the 'plugin registry'
import plugins
plugins.LoadPlugins() 

settings.plugins = plugins.pluginList

ID_NEW = wxNewId()
ID_OPEN = wxNewId()
ID_SAVE = wxNewId()
ID_EXIT = wxNewId()
ID_CUT = wxNewId()
ID_COPY = wxNewId()
ID_PASTE = wxNewId()
#ID_PASTE_ABOVE = wxNewId()
ID_PASTE_BELOW = wxNewId()
ID_PASTE_CHILD = wxNewId()
ID_EDIT_AUTHORS = wxNewId()
ID_PROPS = wxNewId()
ID_NEW_CONTACT = wxNewId()
ID_TREE_ADD = wxNewId()
ID_TREE_REMOVE = wxNewId()
ID_TREE_EDIT = wxNewId()
ID_SETTINGS = wxNewId()
ID_EDIT_ITEM = wxNewId()
ID_PREVIEW = wxNewId()
ID_CREATE_ECLS_LINK = wxNewId()
ID_TREE_ADD_ECLASS = wxNewId()
ID_ADD_MENU = wxNewId()
ID_IMPORT_FILE = wxNewId()
ID_PUBLISH = wxNewId()
ID_PUBLISH_CD = wxNewId()
ID_PUBLISH_PDF = wxNewId()
ID_PUBLISH_IMS = wxNewId()
ID_PUBLISH_MENU = wxNewId()
ID_TREE_MOVEUP = wxNewId()
ID_TREE_MOVEDOWN = wxNewId()
#ID_ABOUT = wxNewId()
ID_HELP = wxNewId()
ID_CLOSE = wxNewId()
ID_BUG = wxNewId()
ID_THEME = wxNewId()
ID_LINKCHECK = wxNewId()
ID_REFRESH_THEME = wxNewId()
ID_UPLOAD_PAGE = wxNewId()
ID_CONTACTS = wxNewId()
ID_ERRORLOG = wxNewId()
ID_ACTIVITY = wxNewId()
ID_FIND_IN_PROJECT = wxNewId()

eclassdirs = ["EClass", "Text", "pub", "Graphics", "File", "Present"]

useie = True
try:
	import win32api
	import win32pipe
	from wx.lib.iewin import *
except:
	pass

try:
	import pythoncom
except:
	pass

#----------------------------- MainFrame Class ----------------------------------------------

class MainFrame2(wxFrame): 
	def __init__(self, parent, ID, title):
		busy = wxBusyCursor()
		wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, wxSize(780,580), style=wxDEFAULT_FRAME_STYLE|wxCLIP_CHILDREN|wxNO_FULL_REPAINT_ON_RESIZE)
		self.CurrentFilename = ""
		self.isDirty = False
		self.isNewCourse = False
		self.CurrentItem = None #current node
		self.ProjectDir = ""
		self.CurrentTreeItem = None
		self.pub = conman.ConMan()
		#dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
		if wx.Platform == "__WXMAC__":
			wx.SetDefaultPyEncoding("utf-8")
		self.dirtyNodes = []
		self.version = version.asString()
		self.AppDir = os.path.abspath(sys.path[0])
		#if wxPlatform == '__WXMSW__':
		#	self.AppDir = win32api.GetShortPathName(self.AppDir)
		settings.AppDir = self.AppDir
		self.Platform = "win32"
		if wxPlatform == '__WXMSW__':
			self.Platform = "win32"
		elif wxPlatform == '__WXMAC__':
			self.Platform = "mac"
		else:
			self.Platform = "linux"
		self.ThirdPartyDir = os.path.join(self.AppDir, "3rdparty", self.Platform)
		#if wxPlatform == '__WXMSW__':
		#	self.ThirdPartyDir = win32api.GetShortPathName(self.ThirdPartyDir)
		settings.ThirdPartyDir = self.ThirdPartyDir

		self.PrefDir = self.AppDir
		self.DragItem = None
		self.CutNode = None
		self.CopyNode = None
		self.ftppass = ""
		self.themes = themes.ThemeList(os.path.join(self.AppDir, "themes"))
		self.currentTheme = self.themes.FindTheme("Default (no frames)")
		self.settings = xml_settings.XMLSettings()
		
		wxInitAllImageHandlers()

		import errors
		self.log = errors.appErrorLog

		self.PrefDir = guiutils.getAppDataDir()
		oldprefdir = guiutils.getOldAppDataDir()

		# Move old AppDataDir if it exists.
		if oldprefdir and os.path.exists(oldprefdir) and not oldprefdir == self.PrefDir:
			try:
				fileutils.CopyFiles(oldprefdir, self.PrefDir, 1)
				shutil.rmtree(oldprefdir)
			except:
				#self.PrefDir = oldprefdir
				self.log.write(_("Error moving preferences."))

		if os.path.exists(os.path.join(self.PrefDir, "settings.xml")):
			self.settings.LoadFromXML(os.path.join(self.PrefDir, "settings.xml"))
		
		settings.PrefDir = self.PrefDir
		settings.options = self.settings

		contactsdir = os.path.join(self.PrefDir, "Contacts")
		if not os.path.exists(contactsdir):
			os.mkdir(contactsdir)
		
		self.LoadLanguage()

		#check settings and if blank, apply defaults
		coursefolder = self.settings["CourseFolder"]
		gsdlfolder = self.settings["GSDL"]
		htmleditor = self.settings["HTMLEditor"]

		if coursefolder == "":
			self.settings["CourseFolder"] = guiutils.getEClassProjectsDir()

		if gsdlfolder == "":
			if wxPlatform == '__WXMSW__':
				gsdlfolder = "C:\Program Files\gsdl"
			
			if os.path.exists(gsdlfolder):
				self.settings["GSDL"] = gsdlfolder		

		if htmleditor == "":
			if wxPlatform == '__WXMSW__':
				htmleditor = "C:\Program Files\OpenOffice.org1.0\program\oooweb.exe"
			
			if os.path.exists(htmleditor):
				self.settings["HTMLEditor"] = htmleditor
		
		#load the VCards
		self.vcardlist = {}
		vcards = glob.glob(os.path.join(self.PrefDir, "Contacts", "*.vcf"))
		errOccurred = False
		errCards = []
		for card in vcards:
			try:
				myvcard = vcard.VCard()
				myvcard.parseFile(os.path.join(self.PrefDir, "Contacts", card))
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
			wxMessageBox(message)

		self.statusBar = self.CreateStatusBar()

		if self.Platform == "win32":
			self.SetIcon(wxIcon(os.path.join(self.AppDir, "icons", "eclass_builder.ico"), wxBITMAP_TYPE_ICO))
		#load icons
		icnNewProject = wxBitmap(os.path.join(self.AppDir, "icons", "book_green16.gif"), wxBITMAP_TYPE_GIF)
		icnOpenProject = wxBitmap(os.path.join(self.AppDir, "icons", "open16.gif"), wxBITMAP_TYPE_GIF)
		icnSaveProject = wxBitmap(os.path.join(self.AppDir, "icons", "save16.gif"), wxBITMAP_TYPE_GIF)

		icnNewPage = wxBitmap(os.path.join(self.AppDir, "icons", "new16.gif"), wxBITMAP_TYPE_GIF)
		icnEditPage = wxBitmap(os.path.join(self.AppDir, "icons", "edit16.gif"), wxBITMAP_TYPE_GIF)
		icnPageProps = wxBitmap(os.path.join(self.AppDir, "icons", "properties16.gif"), wxBITMAP_TYPE_GIF)
		icnDeletePage = wxBitmap(os.path.join(self.AppDir, "icons", "delete16.gif"), wxBITMAP_TYPE_GIF)

		icnPreview = wxBitmap(os.path.join(self.AppDir, "icons", "doc_map16.gif"), wxBITMAP_TYPE_GIF)
		icnPublishWeb = wxBitmap(os.path.join(self.AppDir, "icons", "ftp_upload16.gif"), wxBITMAP_TYPE_GIF)
		icnPublishCD = wxBitmap(os.path.join(self.AppDir, "icons", "cd16.gif"), wxBITMAP_TYPE_GIF)
		icnPublishPDF = wxBitmap(os.path.join(self.AppDir, "icons", "pdf.gif"), wxBITMAP_TYPE_GIF)
		#icnBug = wxBitmap(os.path.join(self.AppDir, "icons", "bug.gif"), wxBITMAP_TYPE_GIF)
		icnHelp = wxBitmap(os.path.join(self.AppDir, "icons", "help16.gif"), wxBITMAP_TYPE_GIF)

		self.treeimages = wxImageList(15, 15)
		imagepath = os.path.join(self.AppDir, "icons")
		#self.treeimages.Add(wxBitmap(os.path.join(imagepath, "bookclosed.gif"), wxBITMAP_TYPE_GIF))
		#self.treeimages.Add(wxBitmap(os.path.join(imagepath, "chapter.gif"), wxBITMAP_TYPE_GIF))
		#self.treeimages.Add(wxBitmap(os.path.join(imagepath, "page.gif"), wxBITMAP_TYPE_GIF))

		#create toolbar
		self.toolbar = self.CreateToolBar(wxTB_HORIZONTAL | wxNO_BORDER | wxTB_FLAT)
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

		if wxPlatform != "__WXMAC__":
			self.toolbar.SetToolBitmapSize(wxSize(16,16))
		self.toolbar.Realize()

		EditMenu = wxMenu()
		EditMenu.Append(ID_CUT, _("Cut")+"\tCTRL+X")
		EditMenu.Append(ID_COPY, _("Copy")+"\tCTRL+C")
		PasteMenu = wxMenu()
		PasteMenu.Append(ID_PASTE_BELOW, _("Paste After")+"\tCTRL+V")
		PasteMenu.Append(ID_PASTE_CHILD, _("Paste As Child"))
		#self.PasteMenu = PasteMenu
		EditMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu)
		#EditMenu.AppendSeparator()
		#EditMenu.Append(ID_FIND_IN_PROJECT, _("Find in Project"))

		#create the PopUp Menu used when a user right-clicks on an item
		self.PopMenu = wxMenu()
		self.PopMenu.Append(ID_ADD_MENU, _("Add New"))
		self.PopMenu.Append(ID_TREE_REMOVE, _("Remove Page"), _("Remove the current page"))
		PasteMenu2 = wxMenu()
		PasteMenu2.Append(ID_PASTE_BELOW, _("Paste Below")+"\tCTRL+V")
		PasteMenu2.Append(ID_PASTE_CHILD, _("Paste As Child"))
		#self.PopMenu.Append(ID_CREATE_ECLS_LINK, _("Link to EClass"), _("Create a link to another EClass"))
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_IMPORT_FILE, _("Import file..."))
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_CUT, _("Cut"))
		self.PopMenu.Append(ID_COPY, _("Copy"))
		self.PopMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu2)
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_EDIT_ITEM, _("Edit Page"), _("Edit the currently selected page"))	
		self.PopMenu.Append(ID_TREE_MOVEUP, _("Move Page Up"), _("Move the selected page higher in the tree"))
		self.PopMenu.Append(ID_TREE_MOVEDOWN, _("Move Page Down"), _("Move the selected page lower in the tree"))	
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_UPLOAD_PAGE, _("Upload Page"), _("Upload Page to FTP Server"))
		self.PopMenu.AppendSeparator()
		self.PopMenu.Append(ID_TREE_EDIT, _("Page Properties"), _("Edit Page Properties"))

		FileMenu = wxMenu()
		FileMenu.Append(ID_NEW, "&" + _("New"), _("Create a New Project"))
		FileMenu.Append(ID_OPEN, "&" +_("Open"), _("Open an Existing Project"))
		FileMenu.Append(ID_SAVE, "&" + _("Save"), _("Save the Current Project"))
		FileMenu.Append(ID_CLOSE, "&" + _("Close"), _("Close the Current Project"))
		FileMenu.AppendSeparator()
		PrevMenu = wxMenu()
		PrevMenu.Append(ID_PREVIEW, _("Web Browser"),  _("Preview EClass in web browser"))
		
		FileMenu.AppendMenu(wxNewId(), _("Preview"), PrevMenu)
		FileMenu.Append(ID_REFRESH_THEME, _("Refresh Theme"), "Reapply current theme to pages.")
		FileMenu.AppendSeparator()
		PubMenu = wxMenu()
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
		
		ToolsMenu = wxMenu()
		ToolsMenu.Append(ID_THEME, _("Change Theme"))
		ToolsMenu.Append(ID_LINKCHECK, _("Check Links"))
		ToolsMenu.Append(ID_CONTACTS, _("Manage Contacts"))
		
		ToolsMenu.Append(ID_ERRORLOG, _("Error Viewer"))
		ToolsMenu.Append(ID_ACTIVITY, _("Activity Monitor"), _("View status of background activties."))
		ToolsMenu.AppendSeparator()
		ToolsMenu.Append(ID_SETTINGS, _("Options"), _("Modify Program Options"))
		if wxPlatform == "__WXMAC__":
			wxApp_SetMacPreferencesMenuItemId(ID_SETTINGS)


		HelpMenu = wxMenu()
		HelpMenu.Append(wxID_ABOUT, _("About Eclass"), _("About Eclass.Builder"))
		HelpMenu.Append(ID_HELP, _("Help"), _("EClass.Builder Help"))
		HelpMenu.Append(ID_BUG, _("Provide Feedback"), _("Submit feature requests or bugs"))


		menuBar = wxMenuBar()
		menuBar.Append(FileMenu, "&"+ _("File"))
		menuBar.Append(EditMenu, _("Edit"))
		#menuBar.Append(AuthorsMenu, "&" + _("Authors"))
		menuBar.Append(self.PopMenu, "&" + _("Page"))
		#menuBar.Append(OptionsMenu, "&" + _("Options"))
		menuBar.Append(ToolsMenu, "&" + _("Tools"))
		menuBar.Append(HelpMenu, "&" + _("Help"))
		
		
		self.menuBar = menuBar
		self.SetMenuBar(menuBar)
		self.SwitchMenus(False)

		#self.sizer = wxBoxSizer(wxVERTICAL)
		
		#split the window into two - Treeview on one side, browser on the other
		self.splitter1 = wxSplitterWindow (self, -1, style=wxSP_3D | wxNO_3D) #wxSize(760, 500))	

		# Tree Control for the XML hierachy
		self.wxTree = wxTreeCtrl (self.splitter1,
								   -1 ,
								   wxDefaultPosition, wxDefaultSize,
								   wxTR_HAS_BUTTONS | wxTR_LINES_AT_ROOT | wxSIMPLE_BORDER | wxTR_HAS_VARIABLE_ROW_HEIGHT)

		#self.wxTree.SetImageList(self.treeimages)
		droptarget = wxTreeDropTarget(self, self.wxTree)
		self.wxTree.SetDropTarget(droptarget)

		#handle delete key
		accelerators = wxAcceleratorTable([(wxACCEL_NORMAL, WXK_DELETE, ID_TREE_REMOVE)])
		self.SetAcceleratorTable(accelerators)

		#self.splitter1.sizer.Add(self.wxTree, 1) 

		self.previewbook = wxNotebook(self.splitter1, -1, style=wxCLIP_CHILDREN)
		
		self.splitter1.SplitVertically(self.wxTree, self.previewbook, 200)

		# load all browsers that we can use for previewing
		self.browsers = {}
		browsers = wxbrowser.browserlist
		if len(browsers) == 1 and browsers[0] == "htmlwindow":
			self.browsers["htmlwin"] = self.browser = wxHtmlWindow(self.previewbook, -1, wxDefaultPosition, wxDefaultSize)
			self.previewbook.AddPage(self.browser, _("HTML Preview"))
		else:
			if "htmlwindow" in browsers:
				browsers.remove("htmlwindow")
			default = "mozilla"
			if sys.platform == "win32" and "ie" in browsers:
				default = "ie"
			elif sys.platform == "darwin" and "webkit" in browsers:
				default = "webkit"
			
			for browser in browsers:
				panel = wxPanel(self.previewbook, -1)
				self.browser = self.browsers[browser] = wxbrowser.wxBrowser(panel, -1, browser)
				self.previewbook.AddPage(panel, self.browsers[browser].GetBrowserName())
				
				panelsizer = wxBoxSizer(wxHORIZONTAL)
				panelsizer.Add(self.browsers[browser].browser, 1, wxEXPAND)
				panel.SetAutoLayout(True)
				panel.SetSizerAndFit(panelsizer)
				
		self.mysizer = wxBoxSizer(wxHORIZONTAL)
		self.mysizer.Add(self.splitter1, 1, wxEXPAND)
		self.SetSizer(self.mysizer)
		self.SetAutoLayout(True)
		self.Layout()

		EVT_MENU(self, ID_NEW, self.NewProject)
		EVT_MENU(self, ID_SAVE, self.SaveProject)
		EVT_MENU(self, ID_OPEN, self.OnOpen)
		EVT_MENU(self, ID_CLOSE, self.OnClose)
		EVT_MENU(self, ID_EXIT, self.TimeToQuit)
		#EVT_MENU(self, ID_EDIT_AUTHORS, self.EditAuthors)
		EVT_MENU(self, ID_PROPS, self.LoadProps)
		#EVT_MENU(self, ID_TREE_ADD, self.AddNewItem)
		EVT_MENU(self, ID_TREE_REMOVE, self.RemoveItem)
		EVT_MENU(self, ID_TREE_EDIT, self.EditItem) 
		EVT_MENU(self, ID_EDIT_ITEM, self.EditFile) 
		EVT_MENU(self, ID_PREVIEW, self.PublishIt) 
		EVT_MENU(self, ID_PUBLISH, self.PublishToWeb)
		EVT_MENU(self, ID_PUBLISH_CD, self.PublishToCD)
		EVT_MENU(self, ID_PUBLISH_PDF, self.PublishToPDF)
		EVT_MENU(self, ID_PUBLISH_IMS, self.PublishToIMS)
		#EVT_MENU(self, ID_CREATE_ECLS_LINK, self.CreateCourseLink)
		EVT_MENU(self, ID_BUG, self.ReportBug)
		EVT_MENU(self, ID_THEME, self.ManageThemes)
		
		EVT_MENU(self, ID_ADD_MENU, self.AddNewEClassPage)
		EVT_MENU(self, ID_SETTINGS, self.EditPreferences)
		EVT_MENU(self, ID_TREE_MOVEUP, self.MoveItemUp)
		EVT_MENU(self, ID_TREE_MOVEDOWN, self.MoveItemDown)
		EVT_MENU(self, wxID_ABOUT, self.OnAbout)
		EVT_MENU(self, ID_HELP, self.OnHelp)
		EVT_MENU(self, ID_LINKCHECK, self.OnLinkCheck)
		EVT_MENU(self, ID_CUT, self.OnCut)
		EVT_MENU(self, ID_COPY, self.OnCopy)
		EVT_MENU(self, ID_PASTE_BELOW, self.OnPaste)
		EVT_MENU(self, ID_PASTE_CHILD, self.OnPaste)
		EVT_MENU(self, ID_PASTE, self.OnPaste)
		EVT_MENU(self, ID_IMPORT_FILE, self.AddNewItem)
		EVT_MENU(self, ID_REFRESH_THEME, self.OnRefreshTheme)
		EVT_MENU(self, ID_UPLOAD_PAGE, self.UploadPage)
		EVT_MENU(self, ID_ERRORLOG, self.OnErrorLog)
		EVT_MENU(self, ID_CONTACTS, self.OnContacts)
		EVT_MENU(self, ID_ACTIVITY, self.OnActivityMonitor)
		EVT_MENU(self, ID_FIND_IN_PROJECT, self.OnFindInProject)

		EVT_CLOSE(self, self.TimeToQuit)

		#EVT_LIST_ITEM_SELECTED(self, self.List.GetId(), self.OnAttributeItemSelected)
		#EVT_TREE_BEGIN_DRAG(self.wxTree, self.wxTree.GetId(), self.OnTreeDrag)
		EVT_RIGHT_DOWN(self.wxTree, self.OnTreeRightClick)
		EVT_LEFT_DOWN(self.wxTree, self.OnTreeLeftClick)
		EVT_LEFT_DCLICK(self.wxTree, self.OnTreeDoubleClick)
		#EVT_LIST_DELETE_ITEM(self, self.List.GetId(), self.OnDeleteItem)

		#EVT_SIZE(self.splitter1, self.SplitterSize)
		self.Show()
		
		self.activityMonitor = ActivityMonitor(self)
		self.activityMonitor.LoadState("ActivityMonitor")
		
		self.errorViewer = gui.error_viewer.ErrorLogViewer(self)
		self.errorViewer.LoadState("ErrorLogViewer")
		
		#EVT_NOTEBOOK_PAGE_CHANGED(self.previewbook, self.previewbook.GetId(), self.OnPageChanged)
		if wxPlatform == '__WXMSW__':
			EVT_CHAR(self.previewbook, self.SkipNotebookEvent)

		if self.settings["LastOpened"] != "" and os.path.exists(self.settings["LastOpened"]):
			self.LoadEClass(self.settings["LastOpened"])
			
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
		if self.activityMonitor:
			self.activityMonitor.Show()
		else:
			self.activityMonitor = ActivityMonitor(self, -1, _("Activity Monitor"))
			self.activityMonitor.Show()

	def OnFindInProject(self, evt):
		dlg = pfdlg.ProjectFindDialog(self)
		dlg.Show()
		
	def SkipNotebookEvent(self, evt):
		evt.Skip()

	def LoadLanguage(self):
		self.langdir = "en"
		if self.settings["Language"] == "English":
			self.langdir = "en"
		elif self.settings["Language"] == "Espanol":
			self.langdir = "es"
		elif self.settings["Language"] == "Francais":
			self.langdir = "fr"
		lang_dict[self.langdir].install()
	
	def OnErrorLog(self, evt):
		if not self.errorViewer:	
			self.errorViewer = gui.error_viewer.ErrorLogViewer(self)
			self.errorViewer.Show()			
		else:
			self.errorViewer.Show()

	def OnCut(self, event):
		sel_item = self.wxTree.GetSelection()
		self.CutNode = sel_item
		self.wxTree.SetItemTextColour(sel_item, wxLIGHT_GREY)
		if self.CopyNode:
			self.CopyNode = None

	def OnCopy(self, event):
		sel_item = self.wxTree.GetSelection()
		self.CopyNode = sel_item
		if self.CutNode:
			self.wxTree.SetItemTextColour(self.CutNode, wxBLACK)
			self.CutNode = None #copy automatically cancels a cut operation

	def OnPaste(self, event):
		dirtyNodes = []
		sel_item = self.wxTree.GetSelection()
		pastenode = self.CopyNode
		if self.CutNode:
			pastenode = self.CutNode
		
		import copy
		pasteitem = copy.copy(self.wxTree.GetPyData(pastenode))
		pasteitem.content = conman.CopyContent(pasteitem.content)
		self.pub.content.append(pasteitem.content)
		newparent = None
		if event.GetId() == ID_PASTE_BELOW or event.GetId() == ID_PASTE:
			newitem = self.wxTree.InsertItem(self.wxTree.GetItemParent(sel_item), sel_item, self.wxTree.GetItemText(pastenode), -1, -1, wxTreeItemData(self.wxTree.GetPyData(pastenode)))
			beforenode = self.wxTree.GetPyData(sel_item)
			newparent = beforenode.parent
			beforenode.parent.children.insert(beforenode.parent.children.index(beforenode) + 1, pasteitem)

		elif event.GetId() == ID_PASTE_CHILD:
			newitem = self.wxTree.AppendItem(sel_item, self.wxTree.GetItemText(pastenode), -1, -1, wxTreeItemData(self.wxTree.GetPyData(pastenode)))
			parentnode = self.wxTree.GetPyData(sel_item)
			newparent = parentnode
			parentnode.children.append(pasteitem)
			
		if not self.wxTree.GetChildrenCount(pastenode, False) == 0:
			self.CopyChildrenRecursive(pastenode, newitem)

		dirtyNodes.append(pasteitem)

		if self.CutNode:
			if pasteitem.parent.children.count(pasteitem) > 0:
				pasteitem.parent.children.remove(pasteitem)
			else:
				self.log.write("Item's parent doesn't have it as a child?!")

			self.wxTree.Delete(self.CutNode)
			dirtyNodes.append(pasteitem.back())
			dirtyNodes.append(pasteitem.next())
			self.CutNode = None

		pasteitem.parent = newparent
		dirtyNodes.append(pasteitem.back())
		dirtyNodes.append(pasteitem.next())

		for item in dirtyNodes:
			self.Update(item)

	def CopyChildrenRecursive(self, sel_item, new_item):
		thisnode = self.wxTree.GetFirstChild(sel_item)[0]
		while (thisnode.IsOk()):
			thisitem = self.wxTree.AppendItem(new_item, self.wxTree.GetItemText(thisnode), -1, -1, wxTreeItemData(self.wxTree.GetPyData(thisnode)))
			if not self.wxTree.GetChildrenCount(thisnode, False) == 0:
				self.CopyChildrenRecursive(thisnode, thisitem)
			thisnode = self.wxTree.GetNextSibling(thisnode) 

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
		sel_item, flags = self.wxTree.HitTest(event.GetPoint())
		self.wxTree.SelectItem(sel_item)
		self.DragItem = sel_item
		#data = wxTextDataObject()
		#data.SetText(self.wxTree.GetItemText(self.CurrentTreeItem))
		data = wxCustomDataObject(wxCustomDataFormat('EClassPage'))
		data.SetData(cPickle.dumps(self.CurrentItem, 1)) 
		
		dropsource = wxTreeDropSource(self.wxTree)
		dropsource.SetData(data) 
		result = dropsource.DoDragDrop(wxDrag_AllowMove)
		if result == wxDragMove or result == wxDragCopy:
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
		self.toolbar.EnableTool(ID_PUBLISH_PDF, value)
		self.toolbar.EnableTool(ID_TREE_ADD_ECLASS, value)
		self.toolbar.EnableTool(ID_TREE_EDIT, value)
		self.toolbar.EnableTool(ID_EDIT_ITEM, value)
		self.toolbar.EnableTool(ID_TREE_REMOVE, value)

		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Page")), value)
		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Edit")), value)
		self.menuBar.EnableTop(self.menuBar.FindMenu(_("Tools")), value)
		if wxPlatform == "__WXMAC__":
			#still needed?
			self.menuBar.Refresh()

	def OnClose(self, event):
		if self.isDirty:
			answer = self.CheckSave()
			if answer == wxID_YES:
				self.SaveProject(event)
			elif answer == wxID_CANCEL:
				return
			else:
				self.isDirty = False

		self.pub = None
		self.wxTree.DeleteAllItems()
		self.CurrentItem = None
		self.CurrentFilename = ""
		self.CurrentTreeItem = None
		settings.ProjectDir = self.ProjectDir = ""
		settings.ProjectSettings = {}
		if wxPlatform == "__WXMSW__":
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
		url = os.path.join(self.AppDir, "docs", self.langdir, "index.htm")
		if not os.path.exists(url):
			url = os.path.join(self.AppDir, "docs", "en", "manual", "index.htm")
		webbrowser.open_new("file://" + url)

	def NewProject(self, event):
		"""
		Routine to create a new project. 
		"""
		if self.CurrentFilename != "":
			answer = self.CheckSave()
			if answer == wxID_YES:
				self.SaveProject(event)
			elif answer == wxID_CANCEL:
				return
			else:
				self.isDirty = False

		defaultdir = ""
		if self.settings["CourseFolder"] == "" or not os.path.exists(self.settings["CourseFolder"]):
			msg = wxMessageDialog(self, _("You need to specify a folder to store your course packages. To do so, select Options->Preferences from the main menu."),_("Course Folder not specified"), wxOK)
			msg.ShowModal()
			msg.Destroy()
			return
		else:
			self.pub = conman.ConMan()
			result = NewPubDialog(self).ShowModal()
			if result == wxID_OK:
				self.isNewCourse = True
				self.wxTree.DeleteAllItems()
				self.CurrentFilename = os.path.join(settings.ProjectDir, "imsmanifest.xml")
				self.CurrentItem = self.pub.NewPub(self.pub.name, "English", self.ProjectDir)
				settings.ProjectSettings = self.pub.settings
				self.isDirty = True
				global eclassdirs
				for dir in eclassdirs:
					if not os.path.exists(os.path.join(self.ProjectDir, dir)):
						os.mkdir(os.path.join(self.ProjectDir, dir))
				#if wxPlatform == '__WXMSW__':
					#self.ProjectDir = win32api.GetShortPathName(self.ProjectDir)
					#settings.ProjectDir = self.ProjectDir
				self.BindTowxTree(self.pub.nodes[0])	
				self.CurrentTreeItem = self.wxTree.GetRootItem()
				
				self.currentTheme = self.themes.FindTheme("Default (frames)")
				self.AddNewEClassPage(None, self.pub.name, True)

				self.SaveProject(event)	 
				publisher = self.currentTheme.HTMLPublisher(self)
				publisher.CopySupportFiles()
				publisher.CreateTOC()
				self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
				self.Preview()
				self.SwitchMenus(True)
	
	def TimeToQuit(self, event):
		self.ShutDown(event)

	def ShutDown(self, event):
		if self.isDirty:
			answer = self.CheckSave()
			if answer == wxID_YES:
				self.SaveProject(event)
			elif answer == wxID_CANCEL:
				return
		
		self.settings.SaveAsXML(os.path.join(self.PrefDir,"settings.xml"))
		if self.activityMonitor:
			self.activityMonitor.SaveState("ActivityMonitor")
			self.activityMonitor.Destroy()
		if self.errorViewer:
			self.errorViewer.SaveState("ErrorLogViewer")
			self.errorViewer.Destroy()
		self.Destroy()	

	def PublishToWeb(self, event):
		# Turn off search features before uploading.
		value = self.pub.settings["SearchEnabled"]
		self.pub.settings["SearchEnabled"] = ""
		self.UpdateTextIndex()
		self.UpdateContents()
		mydialog = FTPUploadDialog(self)
		mydialog.ShowModal()
		mydialog.Destroy()
		self.pub.settings["SearchEnabled"] = value
		self.UpdateContents()

	def PublishToPDF(self, event):
		myPublisher = PDFPublisher(self)
		myPublisher.Publish()
		command = ""
		if os.path.exists(myPublisher.pdffile):
			command = guiutils.getOpenCommandForFilename(myPublisher.pdffile)
		else:
			wxMessageBox(_("There was an error publishing to PDF."))
			return
		
		if command and command != "":
			mydialog = wxMessageDialog(self, _("Publishing complete. A PDF version of your EClass can be found at %(pdffile)s. Would you like to preview it now?") % {"pdffile": myPublisher.pdffile}, _("Preview PDF?"), wxYES_NO)
			if mydialog.ShowModal() == wxID_YES:
				wxExecute(command)
		else:
			wxMessageBox(_("Publishing complete. A PDF version of your EClass can be found at %(pdffile)s.") % {"pdffile": myPublisher.pdffile}, _("Publishing Complete."))

	def PublishToIMS(self, event):
		import zipfile
		import tempfile
		#zipname = os.path.join(self.ProjectDir, "myzip.zip")
		deffilename = fileutils.MakeFileName2(self.pub.name) + ".zip"
		dialog = wxFileDialog(self, _("Export IMS Content Package"), "", deffilename, _("IMS Content Package Files") + " (*.zip)|*.zip", wxSAVE)
		if dialog.ShowModal() == wxID_OK: 
			oldtheme = self.currentTheme
			imstheme = self.themes.FindTheme("IMS Package")
			self.currentTheme = imstheme
			publisher = imstheme.HTMLPublisher(self)
			publisher.Publish() 

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

			self.currentTheme = oldtheme
			publisher = self.currentTheme.HTMLPublisher(self)
			publisher.Publish()

		wxMessageBox("Finished exporting!")
		
	def _DirToZipFile(self, dir, myzip):
		mydir = os.path.join(self.ProjectDir, dir)
		if not os.path.basename(dir) in ["installers", "cgi-bin"]:
			for file in os.listdir(mydir):
				mypath = os.path.join(mydir, file)
				if os.path.isfile(mypath) and string.find(file, "imsmanifest.xml") == -1:
					myzip.write(mypath, os.path.join(dir, file))
				elif os.path.isdir(mypath):
					self._DirToZipFile(os.path.join(dir, file), myzip)
		
	def UpdateTextIndex(self):
		searchEnabled = 0
		print "in index method"
		if not self.pub.settings["SearchEnabled"] == "":
			searchEnabled = self.pub.settings["SearchEnabled"]
		if int(searchEnabled) == 1:
			if self.pub.settings["SearchProgram"] == "Lucene" and hasLucene:
				engine = indexer.SearchEngine(self, os.path.join(settings.ProjectDir, "index.lucene"), settings.ProjectDir)
				maxfiles = engine.numFiles
				#import threading
				dialog = wxProgressDialog(_("Updating Index"), _("Preparing to update Index...") + "							 ", maxfiles, style=wxPD_CAN_ABORT | wxPD_APP_MODAL) 
				engine.IndexFiles(self.pub.nodes[0], dialog)

				dialog.Destroy()
				dialog = None

			elif self.pub.settings["SearchProgram"] == "Greenstone":
				gsdl = self.settings["GSDL"]
				collect = os.path.join(gsdl, "collect")
				if wxPlatform == "__WXMSW__":	
					wxYield()
					if True:
						cddialog = UpdateIndexDialog(self, True)
						if not self.pub.pubid == "":
							eclassdir = os.path.join(collect, self.pub.pubid)
						else:
							message = _("You must enter a publication ID to enable the search function. You can specify a publication ID by selecting 'File->Project Settings' from the menu.")
							dialog = wxMessageDialog(self, message, _("Publication ID Not Set"), wxOK).ShowModal()
							return
						try:
							cddialog.UpdateIndex(gsdl, eclassdir)
						except: 
							message = _("There was an unexpected error publishing your course. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
							self.log.write(message)
							dialog = wxMessageDialog(self, message, _("Could Not Publish EClass"), wxOK).ShowModal()
							cddialog.Destroy()
						result = self.UpdateEClassDataFiles(self.pub.pubid)
				else:
					dialog = wxMessageDialog(self, _("Sorry, building a Greenstone CD from EClass is not yet supported on this platform."), _("Cannot build Greenstone collection."), wxOK)
					dialog.ShowModal()
					dialog.Destroy()

	def PublishToCD(self,event):
		folder = self.ProjectDir
		if self.pub.settings["CDSaveDir"] == "":
			result = wxMessageDialog(self, _("You need to specify a directory in which to store the CD files for burning.\nWould you like to do so now?"), _("Specify CD Save Directory?"), wxYES_NO).ShowModal()
			if result == wxID_YES:
				dialog = wxDirDialog(self, _("Choose a folder to store CD files."), style=wxDD_NEW_DIR_BUTTON)
				if dialog.ShowModal() == wxID_OK:
					folder = self.pub.settings["CDSaveDir"] = dialog.GetPath()
			else:
				return
		else:
			folder = self.pub.settings["CDSaveDir"]

		self.UpdateContents()
		self.UpdateEClassDataFiles(self.pub.pubid)
		self.UpdateTextIndex()
		self.CopyCDFiles()
		message = _("A window will now appear with all files that must be published to CD-ROM. Start your CD-Recording program and copy all files in this window to that program, and your CD will be ready for burning.")
		dialog = wxMessageDialog(self, message, _("Export to CD Finished"), wxOK)
		dialog.ShowModal()
		dialog.Destroy()

		#Open the explorer/finder window
		if wxPlatform == "__WXMSW__":
			if self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
				folder = os.path.join(self.settings["GSDL"], "tmp", "exported_collections")
		
		guiutils.openFolderInGUI(folder)

	def CopyCDFiles(self):
		try:
			#cleanup after old EClass versions
			fileutils.DeleteFiles(os.path.join(self.ProjectDir, "*.pyd"))
			fileutils.DeleteFiles(os.path.join(self.ProjectDir, "*.dll"))
			fileutils.DeleteFiles(os.path.join(self.ProjectDir, "*.exe"))

			pubdir = self.ProjectDir
			if self.pub.settings["CDSaveDir"] != "":
				pubdir = self.pub.settings["CDSaveDir"]

			if pubdir != self.ProjectDir:
				fileutils.CopyFiles(self.ProjectDir, pubdir, 1)

			# copy the server program
			if self.pub.settings["SearchProgram"] != "Greenstone":
				fileutils.CopyFile("autorun.inf", os.path.join(self.AppDir, "autorun"),pubdir)
				fileutils.CopyFile("loader.exe", os.path.join(self.AppDir, "autorun"),pubdir)
				if self.pub.settings["ServerProgram"] == "Documancer":
					installerdir = os.path.join(pubdir, "installers")
					if not os.path.exists(installerdir):
						os.mkdir(installerdir)
					fileutils.CopyFile("documancer-0.2.6-setup.exe", os.path.join(self.AppDir, "installers"), os.path.join(pubdir, "installers"))

			if self.pub.settings["SearchProgram"] == "Greenstone":
				cddir = os.path.join(self.settings["GSDL"], "tmp", "exported_collections")
				if not os.path.exists(os.path.join(cddir, "gsdl", "eclass")):
					os.mkdir(os.path.join(cddir, "gsdl", "eclass"))
				fileutils.CopyFiles(self.ProjectDir, os.path.join(cddir, "gsdl", "eclass"), True)
				fileutils.CopyFile("home.dm", os.path.join(self.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
				fileutils.CopyFile("style.dm", os.path.join(self.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
			elif self.pub.settings["SearchProgram"] == "Lucene":
				pass
		except:
			message = _("Unable to copy CD support files to your publication directory. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
			self.log.write(message)
			wxMessageDialog(self, message, _("Could Not Copy CD Files"), wxOK).ShowModal()
			return False
										
	def PublishIt(self, event):
		self.UpdateEClassDataFiles()
		import webbrowser
		webbrowser.open_new("file://" + os.path.join(self.ProjectDir, "index.htm")) 
		
	def UpdateEClassDataFiles(self, pubid=""):
		result = False
		busy = wxBusyCursor()
		wxYield()
		try:
			self.CreateDocumancerBook()
			self.CreateDevHelpBook()
			utils.CreateJoustJavascript(self.pub)

		except:
			message = _("There was an unexpected error publishing your course. For more details, check the Error Viewer from the 'Tools->Error Viewer' menu.")
			self.log.write(message)
			wxMessageDialog(self, message, _("Could Not Publish EClass"), wxOK).ShowModal()
			return False
		del busy

		return True

	def UploadFiles(self, files):
		ftp = FTPUpload(self)
		dialog = wxMessageDialog(self, _("Would you like to upload files associated with these pages?"), _("Upload Dependent Files?"), wxYES_NO)
		if dialog.ShowModal() == wxID_YES:
			import htmlutils as importer
			for file in files[:]:
				if os.path.splitext(file)[1] == ".htm" or os.path.splitext(file)[1] == ".html":
					myimporter = importer.HTMLImporter(os.path.join(self.ProjectDir, file))
					#html = open(os.path.join(self.ProjectDir, file), "r").read()
					depFiles = myimporter.GetDocInfo()[3]
					for dep in depFiles:
						depFile = string.replace(dep, "../", "")
						if os.path.exists(os.path.join(self.ProjectDir, depFile)) and not depFile in files:
							files.append(depFile)
				
		ftp.filelist = files
		self.SetStatusText(_("Uploading files..."))
		
		busy = wxBusyCursor()
		try:
			ftp.GetUploadDirs(ftp.filelist)
			ftp.UploadFiles()
		except ftplib.all_errors, e:
			message = ftp.getFtpErrorMessage(e)
			self.log.write(message)
			wxMessageBox(message)
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
			if self.settings["CourseFolder"] != "" and os.path.exists(self.settings["CourseFolder"]):
				defaultdir = self.settings["CourseFolder"]
			
			f = wxFileDialog(self, _("Select a file"), defaultdir, "", "XML Files (*.xml)|*.xml", wxSAVE)
			if f.ShowModal() == wxID_OK:
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
			wxMessageDialog(self, message + str(e), _("Could Not Save File"), wxOK).ShowModal() 

	def CreateDevHelpBook(self):
		import devhelp
		converter = devhelp.DevHelpConverter(self.pub)
		converter.ExportDevHelpFile(os.path.join(self.ProjectDir, "eclass.devhelp"))

	def CreateDocumancerBook(self):
		#update the Documancer book file
		filename = os.path.join(self.ProjectDir, "eclass.dmbk")
		bookdata = utils.openFile(os.path.join(self.AppDir,"bookfile.book.in")).read()
		bookdata = string.replace(bookdata, "<!-- insert title here-->", self.pub.name)
		if self.pub.settings["SearchEnabled"] == "1" and self.pub.settings["SearchProgram"] == "Lucene":
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
			wxMessageBox(message, _("Could Not Save File"), wxICON_ERROR)

	def ReloadThemes(self):
		self.themes = []
		for item in os.listdir(os.path.join(self.AppDir, "themes")):
			if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
				theme = string.replace(item, ".py", "")
				if theme != "BaseTheme":
					exec("import themes." + theme)
					exec("self.themes.append([themes." + theme + ".themename, '" + theme + "'])")		
		
	def RemoveItem(self, event):
		if not self.CurrentItem == self.pub.nodes[0] and self.wxTree.IsSelected(self.CurrentTreeItem):
			mydialog = wxMessageDialog(self, _("Are you sure you want to delete this page? Deleting this page also deletes any sub-pages or terms assigned to this page."), _("Delete Page?"), wxYES_NO)
			result = mydialog.ShowModal()
			if result == wxID_YES:
				#backitem = self.CurrentItem.back()
				self.CurrentItem.parent.children.remove(self.CurrentItem)
				itemtodelete = self.CurrentTreeItem
				self.CurrentTreeItem = self.wxTree.GetItemParent(itemtodelete)
				self.wxTree.Delete(itemtodelete)
				#self.CurrentItem = backitem
				self.CurrentTreeItem = self.wxTree.GetSelection()
				self.CurrentItem = self.wxTree.GetPyData(self.CurrentTreeItem)
				self.UpdateContents()
				self.Update()
				self.isDirty = True
				
	def AddNewItem(self, event):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
			parent = self.CurrentTreeItem
			newnode = conman.ConNode(conman.GetUUID(),None, self.pub.CurrentNode)
			try:
				dlg = PagePropertiesDialog(self, newnode, newnode.content, os.path.join(self.ProjectDir, "File"))
				if dlg.ShowModal() == wxID_OK:
					self.pub.CurrentNode.children.append(newnode)
					self.pub.content.append(newnode.content)
					self.CurrentItem = newnode
					newitem = self.wxTree.AppendItem(self.CurrentTreeItem, self.CurrentItem.content.metadata.name, -1, -1, wxTreeItemData(self.CurrentItem))
					if not self.wxTree.IsExpanded(self.CurrentTreeItem):
						self.wxTree.Expand(self.CurrentTreeItem)
					self.CurrentTreeItem = newitem
					self.wxTree.SelectItem(newitem)
					self.Update()
					self.Preview()
					self.isDirty = True				
				dlg.Destroy()
			except:
				message = constants.createPageErrorMsg
				self.log.write(message)
				wxMessageBox(message + constants.errorInfoMsg)
	
	def AddNewEClassPage(self, event, name="", isroot=False):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem) or self.isNewCourse:
			dialog = NewPageDialog(self)
			if name != "":
				dialog.txtTitle.SetValue(name)

			if dialog.ShowModal() == wxID_OK:
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
					
					try:
						file = plugin.CreateNewFile(newnode.content.metadata.name, os.path.join(settings.ProjectDir, newnode.content.filename))
						if file: 
							if not isroot:
								newitem = self.wxTree.AppendItem(self.CurrentTreeItem, self.CurrentItem.content.metadata.name, -1, -1, wxTreeItemData(self.CurrentItem))
								if not self.wxTree.IsExpanded(self.CurrentTreeItem):
									self.wxTree.Expand(self.CurrentTreeItem)
								self.CurrentTreeItem = newitem
								self.wxTree.SelectItem(newitem)
							else:
								self.wxTree.SetPyData(self.CurrentTreeItem, newnode)
							self.EditFile(None)
							self.UpdateContents()
						else:
							self.CurrentItem.parent.children.remove(self.CurrentItem)
					except:
						message = constants.createPageErrorMsg
						self.log.write(message)
						wxMessageBox(message + constants.errorInfoMsg)
	
				self.isNewCourse = False
			dialog.Destroy()

	def EditItem(self, event):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
			result = PagePropertiesDialog(self, self.CurrentItem, self.CurrentItem.content, os.path.join(self.ProjectDir, "Text")).ShowModal()
			self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
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
			if string.lower(self.pub.settings["UploadOnSave"]) == "yes":
				self.UploadPage()
		except:
			message = _("Error updating page.") + constants.errorInfoMsg
			self.log.write(message)
			wxMessageBox(message)

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
			wxMessageBox(message, _("Could Not Save File"), wxICON_ERROR)
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
		if self.settings["CourseFolder"] != "" and os.path.exists(self.settings["CourseFolder"]):
			defaultdir = self.settings["CourseFolder"]
		
		f = wxDirDialog(self, _("Please select a course"), defaultdir)
		#f = wxFileDialog(self, _("Please select a course"), defaultdir, "", "E-Class Files (imsmanifest.xml)|imsmanifest.xml", wxOPEN)
		if f.ShowModal() == wxID_OK:
			if os.path.exists(os.path.join(f.GetPath(), "imsmanifest.xml")):
				nodeid = "node" + str(len(self.CurrentItem.children) + 1)
				newnode = self.pub.AddChild(nodeid, "content" + str(len(self.pub.content) + 1))
				self.CurrentItem = newnode
				newpub = conman.ConMan()
				newpub.directory = f.GetPath()	
				newpub.LoadFromXML(os.path.join(f.GetPath(), "imsmanifest.xml"))
				newnode.pub = newpub
				newnode.content.filename = os.path.join(f.GetPath(), "imsmanifest.xml")
			#newitem = self.wxTree.AppendItem(self.CurrentTreeItem,newpub.nodes[0].content.metadata.name, -1, -1, wxTreeItemData(newnode))

			#self.CurrentItem.children.append(newpub)
				self.InsertwxTreeChildren(self.CurrentTreeItem, [newpub.nodes[0]]) 
				self.isDirty = True
			else:
				wxMessageDialog(self, _("The folder you selected does not seem to contain an EClass Project."), _("Not a Valid EClass Project"), wxOK).ShowModal()
		f.Destroy()
	
	def EditFile(self, event):
		try:
			if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
				isplugin = False
				result = wxID_CANCEL
				plugin = plugins.GetPluginForFilename(self.CurrentItem.content.filename)
				if plugin:
					mydialog = plugin.EditorDialog(self, self.CurrentItem)
					result = mydialog.ShowModal()
	
				# This should never happen, but leave it in as a fallback
				#if not plugin:
				#	result = 0
				#	import guiutils
				#	myFilename = os.path.join(settings.ProjectDir, self.CurrentItem.content.filename)
				#	started_app = guiutils.sendCommandToApplication(myFilename, "open")
				#	if not started_app:
				#		result = PagePropertiesDialog(self, self.CurrentItem, self.CurrentItem.content, os.path.join(self.ProjectDir, "Text")).ShowModal()
	
				if result == wxID_OK:
					self.Update()
					self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
					self.isDirty = True
		except:
			message = _("There was an unknown error when attempting to start the page editor.")
			self.log.write(message)
			wxMessageBox(message + constants.errorInfoMsg)
		
	def OnOpen(self,event):
		"""
		Handler for File-Open
		"""
		
		if self.isDirty:
			answer = self.CheckSave()
			if answer == wxID_YES:
				self.SaveProject(event)
			elif answer == wxID_CANCEL:
				return
			else:
				self.isDirty = False
		
		defaultdir = ""
		if self.settings["CourseFolder"] != "" and os.path.exists(self.settings["CourseFolder"]):
			defaultdir = self.settings["CourseFolder"]

		dialog = OpenPubDialog(self)
		if dialog.ShowModal() == wxID_OK:
			self.LoadEClass(dialog.GetPath())
		
		dialog.Destroy()
		
	def LoadEClass(self, filename):
		busy = wxBusyCursor()
		if not os.path.exists(filename):
			wxMessageDialog(self, result, _("Could not find EClass file:") + filename, wxOK).ShowModal()
			return 
		
		settings.ProjectDir = self.ProjectDir = os.path.dirname(filename)
		#if sys.platform == "win32":
		#	settings.ProjectDir = self.ProjectDir = win32api.GetShortPathName(settings.ProjectDir)
		self.wxTree.DeleteAllItems()
		self.CurrentFilename = filename
		self.pub = conman.ConMan()
		result = self.pub.LoadFromXML(self.CurrentFilename)
		if result != "":
			wxMessageDialog(self, result, _("Error loading XML file."), wxOK).ShowModal()
		else:
			self.pub.directory = settings.ProjectDir
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
			self.CurrentTreeItem = self.wxTree.GetRootItem()
			mytheme = self.pub.settings["Theme"]
			self.currentTheme = self.themes.FindTheme(mytheme)
			if not self.currentTheme:
				self.currentTheme = self.themes.FindTheme("Default (frames)")

			if self.pub.settings["SearchProgram"] == "Swish-e":
				self.pub.settings["SearchProgram"] = "Lucene"
				wxMessageBox(_("The SWISH-E search program is no longer supported. This project has been updated to use the Lucene search engine instead. Run the Publish to CD function to update the index."))

			self.isDirty = False	 
			self.Preview()
			self.wxTree.SelectItem(self.wxTree.GetRootItem())
			
			self.SetFocus()
			self.SwitchMenus(True)
			self.settings["LastOpened"] = filename
			settings.ProjectSettings = self.pub.settings
			viddir = os.path.join(settings.ProjectDir, "Video")
			auddir = os.path.join(settings.ProjectDir, "Audio")
			
			if os.path.exists(viddir) or os.path.exists(auddir):
				wxMessageBox(_("Due to new security restrictions in some media players, video and audio files need to be moved underneath of the 'pub' directory. EClass will now do this automatically and update your pages. Sorry for any inconvenience!"), _("Moving media files"))
				os.rename(viddir, os.path.join(settings.ProjectDir, "pub", "Video"))
				os.rename(auddir, os.path.join(settings.ProjectDir, "pub", "Audio"))
				#busy2 = wxBusyCursor()
				self.PublishPageAndChildren(self.pub.nodes[0])
				#del busy2
				
			#self.PopMenu.Enable(ID_TREE_REMOVE, False)
			#self.toolbar.EnableTool(ID_TREE_REMOVE, False)
		del busy
		

	def OnTreeRightClick(self, event):
		pt = event.GetPosition()
		item = self.wxTree.HitTest(pt)
		if item[1] & wxTREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.wxTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem 
			self.wxTree.SelectItem(item[0])
			self.toolbar.EnableTool(ID_EDIT_ITEM, True)
			self.toolbar.EnableTool(ID_TREE_EDIT, True)
			self.toolbar.EnableTool(ID_ADD_MENU, True)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, True)

			if self.CurrentTreeItem == self.wxTree.GetRootItem():
				self.PopMenu.Enable(ID_TREE_REMOVE, False)
				self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			else:
				self.PopMenu.Enable(ID_TREE_REMOVE, True)
				self.toolbar.EnableTool(ID_TREE_REMOVE, True)

			self.PopupMenu(self.PopMenu, pt)
		elif not self.wxTree.GetSelection():
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
		item = self.wxTree.HitTest(pt)

		if item[1] & wxTREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.wxTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem 
			self.EditFile(event)
			#if wxPlatform == '__WXMSW__':
			self.Preview()

	def OnTreeLeftClick(self, event):
		if event.Dragging():
			event.Skip()
			return 

		pt = event.GetPosition()
		item = self.wxTree.HitTest(pt)
		
		if item[1] & wxTREE_HITTEST_ONITEMLABEL:
			self.CurrentTreeItem = item[0]
			self.CurrentItem = self.wxTree.GetPyData(item[0])
			self.pub.CurrentNode = self.CurrentItem			 
			self.wxTree.SelectItem(item[0]) 
			self.toolbar.EnableTool(ID_EDIT_ITEM, True)
			self.toolbar.EnableTool(ID_TREE_EDIT, True)
			self.toolbar.EnableTool(ID_ADD_MENU, True)
			pageMenu = self.menuBar.FindMenu("&" + _("Page"))
			self.menuBar.EnableTop(pageMenu, True)

			if self.CurrentTreeItem == self.wxTree.GetRootItem():
				self.PopMenu.Enable(ID_TREE_REMOVE, False)
				self.toolbar.EnableTool(ID_TREE_REMOVE, False)
			else:
				self.PopMenu.Enable(ID_TREE_REMOVE, True)
				self.toolbar.EnableTool(ID_TREE_REMOVE, True)

			self.Preview()
		elif not self.wxTree.GetSelection():
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
		print "Filename is: " + `filename`	
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
		wxBeginBusyCursor()
		#treeimages = wxImageList(15, 15)
		#imagepath = os.path.join(self.AppDir, "icons")
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "bookclosed.gif"), wxBITMAP_TYPE_GIF))
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "chapter.gif"), wxBITMAP_TYPE_GIF))
		#treeimages.Add(wxBitmap(os.path.join(imagepath, "page.gif"), wxBITMAP_TYPE_GIF))
		#self.wxTree.AssignImageList(treeimages)
		self.wxTree.DeleteAllItems()
		#print root.content.metadata.name
		wxTreeNode = self.wxTree.AddRoot(
			root.content.metadata.name,
			-1,-1,
			wxTreeItemData(root))
		if len(root.children) > 0:
			self.InsertwxTreeChildren(wxTreeNode, root.children)
		self.wxTree.Expand(wxTreeNode)
		wxEndBusyCursor()
		
	def InsertwxTreeChildren(self,wxTreeNode, nodes):
		"""
		Given an xTree, create a branch beneath the current selection
		using an xTree
		"""
		for child in nodes:
			if child.pub:
				child = child.pub.nodes[0]
			myname = child.content.metadata.name
			NewwxNode = self.wxTree.AppendItem(wxTreeNode,
					myname,
					-1,-1,
					wxTreeItemData(child))
			# Recurisive call to insert children of each child
			self.InsertwxTreeChildren(NewwxNode,child.children)
			#self.wxTree.Expand(NewwxNode)
		self.wxTree.Refresh()

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

			treeparent = self.wxTree.GetItemParent(self.CurrentTreeItem)
			haschild = self.wxTree.ItemHasChildren(self.CurrentTreeItem)
			nextsibling = self.wxTree.GetPrevSibling(self.CurrentTreeItem)
			nextsibling = self.wxTree.GetPrevSibling(nextsibling)
			self.wxTree.Delete(self.CurrentTreeItem)
			self.CurrentTreeItem = self.wxTree.InsertItem(treeparent, nextsibling, self.CurrentItem.content.metadata.name,-1,-1,wxTreeItemData(item))
			if haschild:
				self.InsertwxTreeChildren(self.CurrentTreeItem, self.CurrentItem.children)
			self.wxTree.Refresh()
			self.wxTree.SelectItem(self.CurrentTreeItem)
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

			treeparent = self.wxTree.GetItemParent(self.CurrentTreeItem)
			nextsibling = self.wxTree.GetNextSibling(self.CurrentTreeItem)
			haschild = self.wxTree.ItemHasChildren(self.CurrentTreeItem)
		
			self.wxTree.Delete(self.CurrentTreeItem)
			self.CurrentTreeItem = self.wxTree.InsertItem(treeparent, nextsibling, self.CurrentItem.content.metadata.name,-1,-1,wxTreeItemData(item))
			if haschild:
				self.InsertwxTreeChildren(self.CurrentTreeItem, self.CurrentItem.children)
			self.wxTree.Refresh()
			self.wxTree.SelectItem(self.CurrentTreeItem)
			self.Update()
			self.Update(previtem)
			self.Update(nextitem)

			self.dirtyNodes.append(self.CurrentItem)
			self.dirtyNodes.append(previtem)
			self.dirtyNodes.append(nextitem)

	def CheckSave(self):
		msg = wxMessageDialog(self, _("Would you like to save the current project before continuing?"),	 _("Save Project?"), wxYES_NO | wxCANCEL)
		answer = msg.ShowModal()
		return answer

class wxTreeDropSource(wxDropSource):
	def __init__(self, tree):
		# Create a Standard wxDropSource Object
		wxDropSource.__init__(self)
		# Remember the control that initiate the Drag for later use
		self.tree = tree

	def SetData(self, obj):
		wxDropSource.SetData(self, obj)

	def GiveFeedback(self,effect):
		try:
			(windowx, windowy) = wxGetMousePosition()
			(x, y) = self.tree.ScreenToClientXY(windowx, windowy)
			item = self.tree.HitTest((x, y))
		except:
			import traceback
			print traceback.print_exc()
		return False

class wxTreeDropTarget(wxPyDropTarget):
	def __init__(self, parent, window):
		wxPyDropTarget.__init__(self)
		self.wxTree = window
		self.parent = parent
		
		self.data = wxCustomDataObject(wxCustomDataFormat('EClassPage'))
		self.SetDataObject(self.data)

	def OnDragOver(self, x, y, result):
		item = self.wxTree.HitTest(wxPoint(x,y))
		#print "x, y = " + `x` + "," + `y` + ", result = " + `item[1]`
		if item[1] == wxTREE_HITTEST_ONITEMLABEL or (wxPlatform == "__WXMAC__" and item[1] == 4160):
			#print "Select item called..."
			self.wxTree.SelectItem(item[0])
			return wxDragMove
		else:
			return True

	def OnDrag(self, x, y):
		return True

	def OnData(self, x, y, result):
		item = self.wxTree.HitTest(wxPoint(x,y))

		if not item[1] == wxTREE_HITTEST_ONITEMLABEL and not (wxPlatform == "__WXMAC__" and item[1] == 4160):
			print "not a legal drop spot..."
			return False

		if not item[0] == self.parent.DragItem and not item[0] == self.wxTree.GetRootItem():
			newtreeitem = None
			newitem = None
			previtem = None
			#oldtreeitem = self.parent.CurrentTreeItem
			#oldtreeitemparent = self.wxTree.GetItemParent(oldtreeitem)
			#oldtreeitemsibling = self.wxTree.GetPrevSibling(oldtreeitem)
			#olditem = self.parent.CurrentItem
			#olditemindex = olditem.parent.children.index(olditem)
			try:
				self.GetData()
				currentitem = cPickle.loads(self.data.GetData())
				#currentitem = self.parent.CurrentItem
				#if not self.parent.IsCtrlDown:
				self.wxTree.InsertItem(self.wxTree.GetItemParent(item[0]), item[0], currentitem.content.metadata.name, -1, -1, wxTreeItemData(currentitem))
				#else:
				#	self.wxTree.InsertItem(item[0], -1, currentitem.content.metadata.name, -1, -1, wxTreeItemData(currentitem))
				previtem = self.wxTree.GetPyData(item[0])
				newitem = currentitem
				newitem.parent = previtem.parent
				previtem.parent.children.insert(previtem.parent.children.index(previtem) + 1, newitem)
				currentitem.parent.children.remove(currentitem)
				self.wxTree.Delete(self.parent.DragItem)
		
				self.parent.isDirty = True
			except: 
				#if not newtreeitem == None:
				#	self.wxTree.Delete(newtreeitem)
				#if not newitem == None and not previtem == None:
				#	previtem.parent.children.remove(newitem)

				message = "There was an error while moving the page. Please contact your systems administrator or send email to kevino@tulane.edu if this error continues to occur."
				self.parent.log.write(message)
				dialog = wxMessageDialog(self.parent, message, "Error moving page", wxOK)
				dialog.ShowModal()
				dialog.Destroy()
				#self.wxTree.InsertItem(olditemparent, olditemsibling, self.wxTree.GetItemText(oldtreeitem), -1, -1, wxTreeItemData(olditem))
				#olditem
		#print text
		return wxDragCopy