#!/usr/bin/env python
from wxPython.wx import *
from wxPython.lib import newevent

hasmozilla = True
try:
	from wxPython.mozilla import *
except:
	hasmozilla = False
if wxPlatform != '__WXMSW__':
	from wxPython.html import wxHtmlWindow

#from wxbrowser import *

from conman.validate import *
from wxPython.stc import * #this is for the HTML plugin
import sys, urllib2, cPickle
import string, time, cStringIO, os, re, glob, csv
import conman
import version
import utils
import indexer

import xml.dom.minidom

#these 2 are needed for McMillan Installer to find these modules
import conman.plugins
import conman.HTMLTemplates

import ftplib
#import themes
import themes.themes as themes
import conman.HTMLFunctions
import conman.xml_settings as xml_settings
import conman.file_functions as files
import conman.vcard as vcard
from conman.validate import *
from convert.PDF import PDFPublisher

#for indexing
import PyLucene

rootdir = os.path.abspath(sys.path[0])
if not os.path.isdir(rootdir):
	rootdir = os.path.dirname(rootdir)
localedir = os.path.join(rootdir, 'locale')
import gettext
gettext.install('eclass', localedir)
lang_dict = {
			"en": gettext.translation('eclass', localedir, languages=['en']), 
			"es": gettext.translation('eclass', localedir, languages=['es']),
			"fr": gettext.translation('eclass', localedir, languages=['fr'])
			}

#dynamically import any plugin in the plugins folder and add it to the 'plugin registry'
myplugins = []
for item in os.listdir(os.path.join(rootdir, "plugins")):
	if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
		if string.find(item, "html.py") == -1 or hasmozilla:
			plugin = string.replace(item, ".py", "")
			exec("import plugins." + plugin)
			exec("myplugins.append(plugins." + plugin + ".plugin_info)") 

#eventually we will load all publishers, like plugins, dynamically
#mypublishers = []
#for item in os.listdir(os.path.join(os.path.abspath(sys.path[0]), "convert")):
#	if item[-3:] == ".py" and string.find(item, "__init__.py") == -1 and not item[0] == ".":
#		plugin = string.replace(item, ".py", "")
#		exec("import convert." + plugin)
#		exec("mypublishers.append(plugins." + plugin + ".plugin_info)") 

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

eclassdirs = ["EClass", "Audio", "Video", "Text", "pub", "Graphics", "includes", "File", "Present"]

useie = True
try:
	import win32api
	import win32pipe
	from wxPython.iewin import *
except:
	pass

try:
	import pythoncom
except:
	pass
#A function to provide simple password encryption
#not meant to deter hackers, but just to deter
#people looking in config files.
def munge(string, pad):
	pad_length = len(pad)
	s = ""
	for i in range(len(string)):
		c = ord(string[i]) ^ ord(pad[i % pad_length])
		s = s + chr(c)
	return s

#----------------------------- MainFrame Class ----------------------------------------------
class MsgPopup(wxDialog):
	def __init__(self, parent,message,accept):
		wxDialog.__init__ (self, parent, -1, _("Message"), wxPoint(200,200),wxSize(200,80), wxCAPTION|wxDEFAULT_DIALOG_STYLE|wxCLIP_CHILDREN)
		label=wxStaticText(self, -1, message, wxPoint(35,10))
		if accept == 1:
			self.btnOK = wxButton(self,-1,_("OK"))#,wxPoint(62, 30),wxSize(76, 24))
			EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.close)
	def close(self,event):
		self.Destroy()

class MainFrame2(wxFrame): 
	def __init__(self, parent, ID, title):
		busy = wxBusyCursor()
		wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, wxSize(780,580), style=wxDEFAULT_FRAME_STYLE|wxCLIP_CHILDREN|wxNO_FULL_REPAINT_ON_RESIZE)
		self.encoding = "iso8859-1"
		import sys
		reload(sys)
		sys.setdefaultencoding(self.encoding)
		self.CurrentFilename = ""
		self.isDirty = False
		self.isNewCourse = False
		self.CurrentItem = None #current node
		self.CurrentDir = ""
		self.CurrentTreeItem = None
		self.myplugins = myplugins
		self.pub = conman.ConMan()
		#dirtyNodes are ones that need to be uploaded to FTP after a move operation is performed
		self.dirtyNodes = []
		self.version = version.asString()
		self.AppDir = os.path.abspath(sys.path[0])
		self.Platform = "win32"
		if wxPlatform == '__WXMSW__':
			self.Platform = "win32"
		elif wxPlatform == '__WXMAC__':
			self.Platform = "mac"
		else:
			self.Platform = "linux"
		self.ThirdPartyDir = os.path.join(self.AppDir, "3rdparty", self.Platform)
		if wxPlatform == '__WXMSW__':
			self.ThirdPartyDir = win32api.GetShortPathName(self.ThirdPartyDir)
		self.PrefDir = self.AppDir
		self.DragItem = None
		self.IsCtrlDown = False
		self.CutNode = None
		self.CopyNode = None
		self.ftppass = ""
		self.themes = themes.ThemeList(os.path.join(self.AppDir, "themes"))
		self.currentTheme = self.themes.FindTheme("Default (no frames)")
		self.settings = xml_settings.XMLSettings()
		wxInitAllImageHandlers()

		self.log = utils.LogFile("errlog.txt")
		self.log.write(time.strftime("%B %d, %Y %H:%M:%S - starting EClass.Builder...\n\n", time.localtime()))

		if wxPlatform == '__WXMSW__':
			import _winreg as wreg
			key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") 
		
		if wxPlatform == '__WXMSW__':
			prefdir = wreg.QueryValueEx(key,'Local AppData')[0]
			if not os.path.exists(prefdir):
				prefdir = self.AppDir
			else:
				if not os.path.exists(os.path.join(prefdir, "EClass")):
					os.mkdir(os.path.join(prefdir, "EClass"))
				prefdir = os.path.join(prefdir, "EClass")

		elif wxPlatform == '__WXMAC__':
			prefdir = os.path.join(os.path.expanduser("~"), "Library", "Preferences", "EClass")
			if not os.path.exists(prefdir):
				os.mkdir(prefdir)

		else: #Assume we're UNIX-based
			prefdir = os.path.join(os.path.expanduser("~"), ".eclass")
			if not os.path.exists(prefdir):
				os.mkdir(prefdir)

		self.PrefDir = prefdir

		if os.path.exists(os.path.join(self.PrefDir, "settings.xml")):
			self.settings.LoadFromXML(os.path.join(self.PrefDir, "settings.xml"))
		
		contactsdir = os.path.join(self.PrefDir, "Contacts")
		if not os.path.exists(contactsdir):
			os.mkdir(contactsdir)

		self.langdir = "en"
		if self.settings["Language"] == "English":
			self.langdir = "en"
		elif self.settings["Language"] == "Espanol":
			self.langdir = "es"
		elif self.settings["Language"] == "Francais":
			self.langdir = "fr"
		
		if self.settings["Language"] != "":
			self.LoadLanguage()
		#self.templates = {_("Default"): "default.tpl"}

		#check settings and if blank, apply defaults
		coursefolder = self.settings["CourseFolder"]
		gsdlfolder = self.settings["GSDL"]
		htmleditor = self.settings["HTMLEditor"]
		
		#tempfolder = os.path.join(os.getcwd(), "temp")
		#if not os.path.exists(tempfolder):
		#	os.mkdir(tempfolder)

		if coursefolder == "":
			if wxPlatform == '__WXMSW__':
				try:
					my_documents_dir = wreg.QueryValueEx(key,'Personal')[0] 
					key.Close() 
					coursefolder = os.path.join(my_documents_dir, "EClass Projects")
				except:
					key.Close()
				
			elif wxPlatform == '__WXMAC__':
				coursefolder = os.path.join(os.path.expanduser("~"),"Documents","EClass Projects")
			else:
				coursefolder = os.path.join(os.path.expanduser("~"), "eclass_projects")

			if not os.path.exists(coursefolder):
				os.mkdir(coursefolder)
		
			self.settings["CourseFolder"] = coursefolder

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
				import traceback
				self.log.write(traceback.print_exc())
				errOccurred = True
				errCards.append(card)

		if errOccurred:
			message = _("EClass could not load the following vCards from your Contacts folder: " + `errCards` + ". You may want to try deleting these cards and re-creating or re-importing them.")
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
		#self.toolbar.AddSimpleTool(ID_BUG, icnBug, _("Send Feedback"), _("Send Feedback"))
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
		FileMenu.Append(ID_PREVIEW, _("Preview"), _("Preview EClass in web browser"))
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

		#AuthorsMenu = wxMenu()
		#AuthorsMenu.Append(ID_EDIT_AUTHORS, "&" + _("Edit Authors"), _("Edit authors database"))
		#self.AuthorsMenu = AuthorsMenu

		OptionsMenu = wxMenu()
		OptionsMenu.Append(ID_SETTINGS, _("System Preferences"), _("Edit Application Settings"))
		if wxPlatform == "__WXMAC__":
			wxApp_SetMacPreferencesMenuItemId(ID_SETTINGS)
		
		ToolsMenu = wxMenu()
		ToolsMenu.Append(ID_THEME, _("Theme Manager"))
		ToolsMenu.Append(ID_LINKCHECK, _("Link Checker"))
		ToolsMenu.Append(ID_CONTACTS, _("Contact Manager"))

		HelpMenu = wxMenu()
		HelpMenu.Append(wxID_ABOUT, _("About Eclass"), _("About Eclass.Builder"))
		HelpMenu.Append(ID_HELP, _("Help"), _("EClass.Builder Help"))
		HelpMenu.Append(ID_BUG, _("Provide Feedback"), _("Submit feature requests or bugs"))


		menuBar = wxMenuBar()
		menuBar.Append(FileMenu, "&"+ _("File"))
		menuBar.Append(EditMenu, _("Edit"))
		#menuBar.Append(AuthorsMenu, "&" + _("Authors"))
		menuBar.Append(self.PopMenu, "&" + _("Page"))
		menuBar.Append(OptionsMenu, "&" + _("Options"))
		menuBar.Append(ToolsMenu, _("Tools"))
		menuBar.Append(HelpMenu, "&" + _("Help"))
		self.menuBar = menuBar
		self.SetMenuBar(menuBar)
		self.SwitchMenus(False)

		#self.sizer = wxBoxSizer(wxVERTICAL)
		
		#split the window into two - Treeview on one side, browser on the other
		self.splitter1 = wxSplitterWindow (self, -1, style=wxSP_3D | wxNO_3D) #wxSize(760, 500))
		
		#lc = wxLayoutConstraints()
		#lc.top.SameAs   (self.toolbar, wxBottom)
		#lc.bottom.SameAs   (self, wxBottom)
		#lc.right.SameAs (self, wxRight)
		#lc.left.SameAs (self, wxLeft)
		#self.splitter1.SetConstraints(lc)		

		# Tree Control for the XML hierachy
		self.wxTree = wxTreeCtrl (self.splitter1,
								   -1 ,
								   wxDefaultPosition, wxDefaultSize,
								   wxTR_HAS_BUTTONS | wxTR_LINES_AT_ROOT | wxSIMPLE_BORDER | wxTR_HAS_VARIABLE_ROW_HEIGHT)

		#self.wxTree.SetImageList(self.treeimages)
		droptarget = wxTreeDropTarget(self, self.wxTree)
		self.wxTree.SetDropTarget(droptarget)

		#self.splitter1.sizer.Add(self.wxTree, 1) 

		self.previewbook = wxNotebook(self.splitter1, -1, style=wxCLIP_CHILDREN)
		self.booksizer = wxNotebookSizer(self.previewbook)
		self.previewpanel = wxPanel(self.previewbook, -1)
		panelsizer = wxBoxSizer(wxHORIZONTAL)
		self.splitter1.SplitVertically(self.wxTree, self.previewbook, 200)

		if hasmozilla: 
			if wxPlatform == '__WXMSW__':
				self.ie = wxIEHtmlWin(self.previewbook, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
				self.browser = self.ie #default, first to preview
				self.previewbook.AddPage(self.ie, "Internet Explorer")
			else:
				self.browser = None
			self.previewbook.AddPage(self.previewpanel, "Mozilla/Netscape")
			self.mozilla = wxMozillaBrowser(self.previewpanel, -1, style = wxSIMPLE_BORDER | wxCLIP_CHILDREN) 
			self.mozilla.Navigate = self.mozilla.LoadURL
			if not self.browser: #if IE isn't loaded
				self.browser = self.mozilla
			panelsizer.Add(self.mozilla, 1, wxEXPAND)
		else:
			if wxPlatform == '__WXMSW__':
				self.ie = wxIEHtmlWin(self.previewbook, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
				self.browser = self.ie #default, first to preview
			else:
				self.browser = wxHtmlWindow(self.previewbook, -1, wxDefaultPosition, wxDefaultSize)
				self.previewbook.AddPage(self.browser, _("HTML Preview"))
		
		#splittersizer.Add(self.wxTree, 0, wxEXPAND)
		self.previewpanel.SetAutoLayout(True)
		self.previewpanel.SetSizerAndFit(panelsizer)
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
		if wxPlatform == "__WXMAC__":
			EVT_UPDATE_UI(self, self.GetId(), self.OnActivate)
		EVT_MENU(self, ID_CONTACTS, self.OnContacts)

		EVT_CLOSE(self, self.TimeToQuit)

		#EVT_LIST_ITEM_SELECTED(self, self.List.GetId(), self.OnAttributeItemSelected)
		#EVT_TREE_BEGIN_DRAG(self.wxTree, self.wxTree.GetId(), self.OnTreeDrag)
		EVT_RIGHT_DOWN(self.wxTree, self.OnTreeRightClick)
		EVT_LEFT_DOWN(self.wxTree, self.OnTreeLeftClick)
		EVT_LEFT_DCLICK(self.wxTree, self.OnTreeDoubleClick)
		#EVT_LIST_DELETE_ITEM(self, self.List.GetId(), self.OnDeleteItem)
		EVT_KEY_DOWN(self.wxTree, self.OnKeyPressed)

		#EVT_SIZE(self.splitter1, self.SplitterSize)
		self.Show()
		EVT_NOTEBOOK_PAGE_CHANGED(self.previewbook, self.previewbook.GetId(), self.OnPageChanged)
		if wxPlatform == '__WXMSW__':
			EVT_CHAR(self.previewbook, self.SkipNotebookEvent)

		if not self.settings["ShowStartup"] == "False":
			dlgStartup = StartupDialog(self)
			result = dlgStartup.ShowModal()
			dlgStartup.Destroy()
			
			if result == 0:
				self.NewProject(None)
			if result == 1:
				self.OnOpen(None)
			if result == 2:
				self.OnHelp(None)

	def SkipNotebookEvent(self, evt):
		evt.Skip()

	def LoadLanguage(self):
		if self.settings["Language"] == "English":
			lang_dict["en"].install()
		elif self.settings["Language"] == "Espanol":
			lang_dict["es"].install()
		elif self.settings["Language"] == "Francais":
			lang_dict["fr"].install()

	def OnActivate(self, evt):
		self.menuBar.Refresh()
	
	def OnKeyPressed(self, evt):
		self.IsCtrlDown = evt.ControlDown()
		evt.Skip()		

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
			self.CutNode = None #copy automatically cancels a paste operation

	def OnPaste(self, event):
		sel_item = self.wxTree.GetSelection()
		pastenode = self.CopyNode
		if self.CutNode:
			pastenode = self.CutNode
		if event.GetId() == ID_PASTE_BELOW or event.GetId() == ID_PASTE:
			newitem = self.wxTree.InsertItem(self.wxTree.GetItemParent(sel_item), sel_item, self.wxTree.GetItemText(pastenode), -1, -1, wxTreeItemData(self.wxTree.GetPyData(pastenode)))
			beforenode = self.wxTree.GetPyData(sel_item)
			beforenode.parent.children.insert(beforenode.parent.children.index(beforenode) + 1, self.wxTree.GetPyData(pastenode))
		elif event.GetId() == ID_PASTE_CHILD:
			newitem = self.wxTree.AppendItem(sel_item, self.wxTree.GetItemText(pastenode), -1, -1, wxTreeItemData(self.wxTree.GetPyData(pastenode)))
			parentnode = self.wxTree.GetPyData(sel_item)
			parentnode.children.append(self.wxTree.GetPyData(pastenode))
			
		if not self.wxTree.GetChildrenCount(pastenode, False) == 0:
			self.CopyChildrenRecursive(pastenode, newitem)

		self.dirtyNodes.append(newitem)

		if self.CutNode:
			myitem = self.wxTree.GetPyData(pastenode)
			if myitem.parent.children.count(myitem) > 0:
				myitem.parent.children.remove(myitem)
			else:
				self.log.write("Item's parent doesn't have it as a child?!")

			self.wxTree.Delete(self.CutNode)
			self.dirtyNodes.append(myitem.back())
			self.dirtyNodes.append(myitem.next())
			self.CutNode = None

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
		#self.PopMenu.FindItemById(ID_ADD_MENU).Enable(value)
		#self.PopMenu.FindItemById(ID_TREE_REMOVE).Enable(value)
		#self.PopMenu.FindItemById(ID_CREATE_ECLS_LINK).Enable(value)
		#self.PopMenu.FindItemById(ID_EDIT_ITEM).Enable(value)	
		#self.PopMenu.FindItemById(ID_TREE_MOVEUP).Enable(value)
		#self.PopMenu.FindItemById(ID_TREE_MOVEDOWN).Enable(value)	
		#self.PopMenu.FindItemById(ID_TREE_EDIT).Enable(value)

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
		self.CurrentDir = ""
		if wxPlatform == "__WXMSW__":
			self.ie.Navigate("about:blank")
			self.mozilla.Navigate("about:blank")
		else:
			self.browser.SetPage("<HTML><BODY></BODY></HTML")
		self.SwitchMenus(False)

	def OnRefreshTheme(self, event):
		#mythememodule = self.currentTheme
		#exec("mytheme = themes." + mythememodule[1])
		#self.currentTheme = mythememodule
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
		else:
			self.pub = conman.ConMan()
			result = NewPubDialog(self).ShowModal()
			if result == wxID_OK:
				self.isNewCourse = True
				self.wxTree.DeleteAllItems()
				self.CurrentFilename = os.path.join(self.CurrentDir, "imsmanifest.xml")
				self.CurrentItem = self.pub.NewPub(self.pub.name, "English", self.CurrentDir)
				self.isDirty = True
				global eclassdirs
				for dir in eclassdirs:
					if not os.path.exists(os.path.join(self.CurrentDir, dir)):
						os.mkdir(os.path.join(self.CurrentDir, dir))
				if wxPlatform == '__WXMSW__':
					self.CurrentDir = win32api.GetShortPathName(self.CurrentDir)
				self.BindTowxTree(self.pub.nodes[0])	
				self.CurrentTreeItem = self.wxTree.GetRootItem()
				
				self.currentTheme = self.themes.FindTheme("Default (frames)")
				self.AddNewEClassPage(None, self.pub.name, True)
				#exec("plugins." + dplugin + ".EditorDialog(self, self.CurrentItem).ShowModal()")
				#self.Update()
				self.SaveProject(event)  
				#exec("mytheme = themes." + self.currentTheme[1])
				publisher = self.currentTheme.HTMLPublisher(self)
				publisher.CopySupportFiles()
				publisher.CreateTOC()
				self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
				self.Preview()
				self.SwitchMenus(True)
		#f.Destroy()
	
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
		self.Destroy()	

	def PublishToWeb(self, event):
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
		mydialog = wxMessageDialog(self, _("Publishing complete. A PDF version of your EClass can be found at %(pdffile)s. Would you like to preview it now?") % {"pdffile": myPublisher.pdffile}, _("Preview PDF?"), wxYES_NO)
		if mydialog.ShowModal() == wxID_YES:
			if wxPlatform == "__WXMSW__":
				win32api.ShellExecute(0, "open",myPublisher.pdffile, "", myPublisher.pdfdir, 1)
			elif wxPlatform == "__WXMAC__":
				result = os.popen("open " + string.replace(myPublisher.pdffile, " ", "\ "))
				result.close()

	def PublishToIMS(self, event):
		import zipfile
		import tempfile
		#zipname = os.path.join(self.CurrentDir, "myzip.zip")
		deffilename = MakeFileName2(self.pub.name) + ".zip"
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
		mydir = os.path.join(self.CurrentDir, dir)
		if not os.path.basename(dir) in ["installers", "cgi-bin"]:
			for file in os.listdir(mydir):
				mypath = os.path.join(mydir, file)
				if os.path.isfile(mypath) and string.find(file, "imsmanifest.xml") == -1:
					myzip.write(mypath, os.path.join(dir, file))
				elif os.path.isdir(mypath):
					self._DirToZipFile(os.path.join(dir, file), myzip)
		
	def UpdateTextIndex(self):
		searchEnabled = 0
		if not self.pub.settings["SearchEnabled"] == "":
			searchEnabled = self.pub.settings["SearchEnabled"]
		if int(searchEnabled) == 1:
			gsdl = self.settings["GSDL"]
			collect = os.path.join(gsdl, "collect")
			if self.pub.settings["SearchProgram"] == "Lucene":
				cddialog = UpdateIndexDialog(self, False)
				cddialog.UpdateIndex("", "")

			elif self.pub.settings["SearchProgram"] == "Greenstone":
				if wxPlatform == "__WXMSW__":	
					wxYield()
					if True:
						cddialog = UpdateIndexDialog(self, True)
						if not self.pub.pubid == "":
							eclassdir = os.path.join(collect, self.pub.pubid)
						else:
							message = _("You must enter a publication ID to enable the search function. You can specify a publication ID by selecting 'File->Project Settings' from the menu.")
							dialog = wxMessageDialog(self, message, _("Publication ID Not Set"), wxOK)
							dialog.ShowModal()
							dialog.Destroy()
							return
						try:
							cddialog.UpdateIndex(gsdl, eclassdir)
						except:	
							message = _("There was an unexpected error publishing your course. Details on the error message are located in the file: ") + os.path.join(self.AppDir, "errlog.txt") + _(", or on Mac, the error message can be found by viewing /Applications/Utilities/Console.app.")
							import traceback
							self.log.write(traceback.print_exc())
							dialog = wxMessageDialog(self, message, _("Could Not Publish EClass"), wxOK)
							dialog.ShowModal()
							dialog.Destroy()
							cddialog.Destroy()
						result = self.PublishEClass(self.pub.pubid)
				else:
					dialog = wxMessageDialog(self, _("Sorry, building a Greenstone CD from EClass is not yet supported on this platform."), _("Cannot build Greenstone collection."), wxOK)
					dialog.ShowModal()
					dialog.Destroy()

	def PublishToCD(self,event):
		self.UpdateContents()
		self.UpdateTextIndex()
		self.PublishEClass(self.pub.pubid)
			#if result == True:
		message = _("A window will now appear with all files that must be published to CD-ROM. Start your CD-Recording program and copy all files in this window to that program, and your CD will be ready for burning.")
		dialog = wxMessageDialog(self, message, _("Export to CD Finished"), wxOK)
		dialog.ShowModal()
		dialog.Destroy()

				#Open the explorer/finder window	
		if wxPlatform == "__WXMSW__":
			if self.pub.settings["SearchProgram"] == "Greenstone" and self.pub.pubid != "":
				cddir = os.path.join(self.settings["GSDL"], "tmp", "exported_collections")
				win32api.ShellExecute(0, "open", cddir, "", cddir, 1)
			else:
				win32api.ShellExecute(0, "open",self.CurrentDir, "", self.CurrentDir, 1)
		elif wxPlatform == "__WXMAC__":
			result = os.popen("open " + string.replace(self.CurrentDir, " ", "\ "))
			result.close()
										
	def PublishIt(self, event):
		self.PublishEClass()
		import webbrowser
		webbrowser.open_new("file://" + os.path.join(self.CurrentDir, "index.htm"))	
		
	def PublishEClass(self, pubid=""):
		result = False
		busy = wxBusyCursor()
		wxYield()
		try:
			self.CreateDocumancerBook()
			#cleanup after old EClass versions
			files.DeleteFiles(os.path.join(self.CurrentDir, "*.pyd"))
			files.DeleteFiles(os.path.join(self.CurrentDir, "*.dll"))
			files.DeleteFiles(os.path.join(self.CurrentDir, "*.exe"))

			files.CopyFile("autorun.inf", os.path.join(self.AppDir, "autorun"),self.CurrentDir)
			files.CopyFile("loader.exe", os.path.join(self.AppDir, "autorun"),self.CurrentDir)
			installerdir = os.path.join(self.CurrentDir, "installers")
			if not os.path.exists(installerdir):
				os.mkdir(installerdir)
			if sys.platform == "win32":
				files.CopyFile("documancer-0.2.4-setup.exe", os.path.join(self.AppDir, "installers"), os.path.join(self.CurrentDir, "installers"))
			useswishe = False
			if self.pub.settings["SearchProgram"] == "Swish-e":
				useswishe = True
				if os.path.exists(os.path.join(self.CurrentDir, "Karrigell.ini")):
					os.remove(os.path.join(self.CurrentDir, "Karrigell.ini"))
			elif self.pub.settings["SearchProgram"] == "Greenstone":
				cddir = os.path.join(self.settings["GSDL"], "tmp", "exported_collections")
				if not os.path.exists(os.path.join(cddir, "gsdl", "eclass")):
					os.mkdir(os.path.join(cddir, "gsdl", "eclass"))
				files.CopyFiles(self.CurrentDir, os.path.join(cddir, "gsdl", "eclass"), True)
				files.CopyFile("home.dm", os.path.join(self.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
				files.CopyFile("style.dm", os.path.join(self.AppDir, "greenstone"), os.path.join(cddir, "gsdl", "macros"))
			elif self.pub.settings["SearchProgram"] == "Lucene":
				pass

		except:
			message = _("There was an unexpected error publishing your course. Details on the error message are located in the file: ") + os.path.join(self.AppDir, "errlog.txt") + _(", or on Mac, the error message can be found by viewing /Applications/Utilities/Console.app.")
			import traceback
			self.log.write(traceback.print_exc())
			wxMessageDialog(self, message, _("Could Not Publish EClass"), wxOK).ShowModal()
			return False
		del busy

		return True

	def UploadFiles(self, files):
		ftp = FTPUpload(self)
		dialog = wxMessageDialog(self, _("Would you like to upload files associated with these pages?"), _("Upload Dependent Files?"), wxYES_NO)
		if dialog.ShowModal() == wxID_YES:
			import conman.HTMLFunctions as importer
			importFiles = importer.ImportFiles()
			for file in files[:]:
				if os.path.splitext(file)[1] == ".htm" or os.path.splitext(file)[1] == ".html":
					html = open(os.path.join(self.CurrentDir, file), "r").read()
					depFiles = importFiles.GetDependentFiles(html)
					for dep in depFiles:
						depFile = string.replace(dep, "../", "")
						if os.path.exists(os.path.join(self.CurrentDir, depFile)) and not depFile in files:
							files.append(depFile)
				
		ftp.filelist = files
		self.SetStatusText(_("Uploading files..."))
		
		busy = wxBusyCursor()
		try:
			ftp.UploadFiles()
		except ftplib.all_errors, e:
			wxMessageBox(ftp.getFtpErrorMessage(e))
		except:
			self.SetStatusText(_("Unknown error uploading file(s)."))
			import traceback
			if traceback.print_exc() != None:
				self.log.write(traceback.print_exc())
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
		ftppass_file = os.path.join(self.CurrentDir, "ftppass.txt")
		try:
			file = open(ftppass_file, "w")
			file.write(munge(self.ftppass, 'foobar'))
			file.close()
		except:
			message = utils.getStdErrorMessage("IOError", {"filename":ftppass_file, "type":"write"})
			wxMessageDialog(self, message, _("Could Not Save File"), wxOK).ShowModal()
		
		self.CreateDocumancerBook()

		try:
			self.pub.SaveAsXML(self.CurrentFilename, self.encoding)
			self.isDirty = False
		except IOError, e:
			wxMessageDialog(self, str(e), _("Could Not Save File"), wxOK).ShowModal() 

	def CreateDocumancerBook(self):
		#update the Documancer book file
		filename = os.path.join(self.CurrentDir, "eclass.dmbk")
		bookdata = open(os.path.join(self.AppDir,"bookfile.book.in")).read()
		bookdata = string.replace(bookdata, "<!-- insert title here-->", self.pub.name)
		if self.pub.settings["SearchEnabled"] == "1" and self.pub.settings["SearchProgram"] == "Lucene":
			bookdata = string.replace(bookdata, "<!-- insert index info here -->", "<attr name='indexed'>1</attr>\n    <attr name='cachedir'>.</attr>")
		else: 
			bookdata = string.replace(bookdata, "<!-- insert index info here -->", "")
		try:
			myfile = open(filename, "w")
			myfile.write(bookdata)
			myfile.close()
		except:
			message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":filename})
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
				#self.CurrentTreeItem = self.wxTree.GetSelection()
				self.CurrentItem = self.wxTree.GetPyData(self.CurrentTreeItem)
				self.UpdateContents()
				self.Update()
				self.isDirty = True
				
	def AddNewItem(self, event):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
			parent = self.CurrentTreeItem
			newnode = conman.ConNode(conman.GetUUID(),None, self.pub.CurrentNode)
			try:
				dlg = PageEditorDialog(self, newnode, newnode.content, os.path.join(self.CurrentDir, "File"))
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
				import traceback
				self.log.write(traceback.print_exc())
				wxMessageBox(_("There was an unknown error when creating the new page. The page was not created. Detailed error information is in the 'errlog.txt' file."))
	
	def AddNewEClassPage(self, event, name="", isroot=False):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem) or self.isNewCourse:
			dialog = NewPageDialog(self)
			if name != "":
				dialog.txtTitle.SetValue(name)

			if dialog.ShowModal() == wxID_OK:
				plugintext = dialog.cmbType.GetStringSelection() #self.PopMenu.GetLabel(event.GetId())
				plugin = None
				for myplugin in myplugins:
					if not string.find(plugintext, myplugin["FullName"]) == -1:
						plugin = myplugin
		
				if plugin and self.CurrentItem and self.CurrentTreeItem:
					if not isroot:
						parent = self.CurrentTreeItem
						newnode = self.pub.AddChild("", "")
					else:
						parent = None
						newnode = self.CurrentItem
					self.CurrentItem = newnode
					newnode.content.metadata.name = dialog.txtTitle.GetValue() #"New Page"
					newnode.content.filename = os.path.join(plugin["Directory"], dialog.txtFilename.GetValue())
					myplugin = eval("plugins." + plugin["Name"])
					try: 		
						if myplugin.EditorDialog(self,self.CurrentItem).ShowModal() == wxID_OK:
							if not isroot:
								newitem = self.wxTree.AppendItem(self.CurrentTreeItem, self.CurrentItem.content.metadata.name, -1, -1, wxTreeItemData(self.CurrentItem))
								if not self.wxTree.IsExpanded(self.CurrentTreeItem):
									self.wxTree.Expand(self.CurrentTreeItem)
								self.CurrentTreeItem = newitem
								self.wxTree.SelectItem(newitem)
							else:
								self.wxTree.SetPyData(self.CurrentTreeItem, newnode)
							self.UpdateContents()
							self.Update()
							self.isDirty = True
						else:
							self.CurrentItem.parent.children.remove(self.CurrentItem)
					except:
						import traceback
						self.log.write(traceback.print_exc())
						wxMessageBox(_("There was an unknown error when creating the new page. The page was not created. Detailed error information is in the 'errlog.txt' file."))
	
				self.isNewCourse = False
			dialog.Destroy()

	def EditItem(self, event):
		if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
			result = PageEditorDialog(self, self.CurrentItem, self.CurrentItem.content, os.path.join(self.CurrentDir, "Text")).ShowModal()
			self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
			self.Update()
			self.isDirty = True

	def Update(self, myitem = None):
		if myitem == None:
			myitem = self.CurrentItem
		self.UpdateContents()
		publisher = self.GetPublisher(myitem.content.filename)
		if publisher: 
			try:
				publisher.Publish(self, myitem, self.CurrentDir)
				backnode = myitem.back()
				if backnode != None:
					publisher = self.GetPublisher(backnode.content.filename)
					if publisher:
						publisher.Publish(self, backnode, self.CurrentDir)
				nextnode = myitem.next()
				if nextnode != None:
					publisher = self.GetPublisher(nextnode.content.filename)
					if publisher:
						publisher.Publish(self, nextnode, self.CurrentDir)
				self.Preview()
				self.dirtyNodes.append(myitem)
				self.dirtyNodes.append(backnode)
				self.dirtyNodes.append(nextnode)
				if string.lower(self.pub.settings["UploadOnSave"]) == "yes":
					self.UploadPage()
			except:
				import traceback
				if traceback.print_exc() != None:
					self.log.write(traceback.print_exc())

	def UploadPage(self, event = None):
		ftpfiles = []
		myitem = self.CurrentItem
		publisher = self.GetPublisher(myitem.content.filename)
		if publisher: 
			ftpfiles.append("pub/" + publisher.GetFilename(myitem.content.filename))
		else:
			ftpfiles.append("File/" + myitem.content.filename)

		backnode = myitem.back()
		if backnode != None:
			publisher = self.GetPublisher(backnode.content.filename)
			if publisher:
				ftpfiles.append("pub/" + publisher.GetFilename(backnode.content.filename))
			else:
				ftpfiles.append("File/" + backnode.content.filename)
				
		nextnode = myitem.next()
		if nextnode != None:
			publisher = self.GetPublisher(nextnode.content.filename)
			if publisher:
				ftpfiles.append("pub/" + publisher.GetFilename(nextnode.content.filename))
			else:
				ftpfiles.append("File/" + nextnode.content.filename)
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
			wxMessageBox(message, _("Could Not Save File"), wxICON_ERROR)
		except:
			pass #we shouldn't do this, but there may be non-fatal errors we shouldn't
				 #catch
		self.statusBar.SetStatusText("")

	def GetPublisher(self, filename):
		extension = string.split(filename, ".")[-1]
		publisher = None
		for plugin in myplugins:
			if extension in plugin["Extension"]:
				publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
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
		#if not os.path.exists(os.path.join(self.pub.directory, "EClass", self.CurrentItem.content.filename)) and not os.path.exists(os.path.join(self.pub.directory, "Text", self.CurrentItem.content.filename)):
		#	wxMessageDialog(self,_("The file cannot be found. Please ensure that the file exists and is located in the EClass subdirectory of your project."), _("File Not Found"), wxOK).ShowModal()
		#	return
		try:
			if self.CurrentItem and self.wxTree.IsSelected(self.CurrentTreeItem):
				isplugin = False
				result = wxID_CANCEL
				for plugin in myplugins:
					extension = string.split(self.CurrentItem.content.filename, ".")
					extension = extension[-1]
					if extension in plugin["Extension"]:
						isplugin = True
						exec("mydialog = plugins." + plugin["Name"] + ".EditorDialog(self, self.CurrentItem)")
						result = mydialog.ShowModal()
	
				if not isplugin:
					result = PageEditorDialog(self, self.CurrentItem, self.CurrentItem.content, os.path.join(self.CurrentDir, "Text")).ShowModal()
	
				if result == wxID_OK:
					self.Update()
					self.wxTree.SetItemText(self.CurrentTreeItem, self.CurrentItem.content.metadata.name)
					self.isDirty = True
		except:
			import traceback
			self.log.write(traceback.print_exc())
			wxMessageBox(_("There was an unknown error when attempting to start the page editor. Detailed error information is in the 'errlog.txt' file."))
	
	
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
			self.wxTree.DeleteAllItems()
			#self.CurrentDir = OpenPubDialog.GetDirectory()
			busy = wxBusyCursor()
			self.CurrentFilename = os.path.join(self.CurrentDir, "imsmanifest.xml")
			self.pub = conman.ConMan()
			result = self.pub.LoadFromXML(self.CurrentFilename)
			if result != "":
				wxMessageDialog(self, result, _("Error loading XML file."), wxOK).ShowModal()
			else:
				self.pub.directory = self.CurrentDir
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
				#self.currentTheme = self.themes[0]
				#if mytheme != "":
				#	for theme in self.themes:
				#		if theme[0] == mytheme:
				#			self.currentTheme = theme
				self.isDirty = False
				if os.path.exists(os.path.join(self.CurrentDir, "ftppass.txt")):
					file = open(os.path.join(self.CurrentDir, "ftppass.txt"), "r")
					self.ftppass = munge(file.read(), 'foobar')
					file.close()	 
				self.Preview()
				self.wxTree.SelectItem(self.wxTree.GetRootItem())
			del busy
		
		dialog.Destroy()
			
		self.SetFocus()
		self.SwitchMenus(True)
		self.PopMenu.Enable(ID_TREE_REMOVE, False)
		self.toolbar.EnableTool(ID_TREE_REMOVE, False)
		#f.Destroy()

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

	def Preview(self, myfilename=""):
		filename = ""
		if myfilename != "":
			filename = os.path.join(self.CurrentItem.dir, "pub", os.path.basename(myfilename))
		if 0: #string.find(self.CurrentItem.content.filename, ".htm") != -1:
			filename = self.CurrentItem.content.filename
			filename = os.path.join(self.CurrentItem.dir, "Text", filename)
		else:
			for plugin in myplugins:
				extension = string.split(self.CurrentItem.content.filename, ".")[-1]
				if extension in plugin["Extension"]:
					publisher = eval("plugins." + plugin["Name"] + ".HTMLPublisher()")
					filename = publisher.GetFilename(self.CurrentItem.content.filename)
					#publisher.Publish(self, self.CurrentItem, self.CurrentItem.dir)
					filename = os.path.join(self.CurrentItem.dir, "pub", os.path.basename(filename))
					
		if filename == "":
			#no publisher could be found, just pass a link to the file
			#it should be in the File subdirectory
			filename = self.CurrentItem.content.filename
			filename = os.path.join(self.CurrentItem.dir, filename)
			
		if os.path.exists(filename):
			if wxPlatform == "__WXMSW__" or hasmozilla:
				self.browser.Navigate(filename)
				#self.mozilla.Navigate(filename)
			else:
				self.browser.LoadPage(filename) 
		else:
			#self.status.SetStatusText("Cannot find file: "+ filename)
			self.log.write("Error previewing file: " + filename)
		

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
		msg = wxMessageDialog(self, _("Would you like to save the current project before continuing?"),  _("Save Project?"), wxYES_NO | wxCANCEL)
		answer = msg.ShowModal()
		return answer

class ProjectPropsDialog(wxDialog):
	def __init__(self, parent):
		"""
		Dialog for setting various project properties.

		"""
		wxDialog.__init__(self, parent, -1, _("Project Settings"), wxPoint(100, 100), wxSize(400, 400))
		self.notebook = wxNotebook(self, -1, wxPoint(10, 10), wxSize(380, 330))
		self.parent = parent
		self.height = 20
		self.labelx = 10
		self.textx = 80
		self.searchchanged = False
		if wxPlatform == "__WXMAC__":
			self.height=25
		
		panel = self.GeneralPanel()
		self.notebook.AddPage(panel, _("General"))
		panel = self.SearchPanel()
		self.notebook.AddPage(panel, _("Search"))
		panel = self.PublishPanel()
		self.notebook.AddPage(panel, _("Publish"))
		panel = self.FTPPanel()
		self.notebook.AddPage(panel, "FTP")
		if wxPlatform == '__WXMAC__':
			self.notebook.SetSelection(0)

		self.btnOK = wxButton(self,wxID_OK,_("OK"))#wxPoint(210, 350),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.txtname.SetFocus()
		self.txtname.SetSelection(-1,-1)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))#,wxPoint(300, 350),wxSize(76,24))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.notesizer = wxNotebookSizer(self.notebook)
		self.mysizer.Add(self.notesizer, 1, wxEXPAND)

		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, self.height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0, wxALIGN_RIGHT)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		if wxPlatform == '__WXMSW__':
			EVT_CHAR(self.notebook, self.SkipNotebookEvent)
		EVT_BUTTON(self, self.btnOK.GetId(), self.btnOKClicked)

	def SkipNotebookEvent(self, event):
		event.Skip()

	def GeneralPanel(self):
		panel = wxPanel(self.notebook, -1, wxPoint(25, 25))
		self.lblname = wxStaticText(panel, -1, _("Name"), wxPoint(self.labelx,10))
		self.txtname = wxTextCtrl(panel, -1, self.parent.pub.name, wxPoint(self.textx, 10), wxDefaultSize) 
		self.lbldescription = wxStaticText(panel, -1, _("Description"), wxPoint(self.labelx,self.height + 10))
		self.txtdescription = wxTextCtrl(panel, -1, self.parent.pub.description, wxPoint(self.textx, self.height + 10), wxDefaultSize, wxTE_MULTILINE) 
		self.lblkeywords = wxStaticText(panel, -1, _("Keywords"), wxPoint(self.labelx, (self.height*4) + 10))
		self.txtkeywords = wxTextCtrl(panel, -1, self.parent.pub.keywords, wxPoint(self.textx, (self.height*4) + 10), wxDefaultSize) 
		self.txtname.SetFocus()
		self.txtname.SetSelection(0, -1)

		self.generalSizer = wxFlexGridSizer(0, 2, 4, 4)
		self.generalSizer.Add(self.lblname, 0, wxALL, 4)
		self.generalSizer.Add(self.txtname, 1, wxEXPAND|wxALL, 4)
		self.generalSizer.Add(self.lbldescription, 0, wxALL, 4)
		self.generalSizer.Add(self.txtdescription, 1, wxEXPAND|wxALL, 4)
		self.generalSizer.Add(self.lblkeywords, 0, wxALL, 4)
		self.generalSizer.Add(self.txtkeywords, 1, wxEXPAND, 4)
		self.generalSizer.AddGrowableCol(1)

		panel.SetAutoLayout(True)
		panel.SetSizer(self.generalSizer)
		self.generalSizer.Fit(panel)
		panel.Layout()

		return panel

	def PublishPanel(self):
		panel = wxPanel(self.notebook, -1, wxPoint(25, 25))
		self.chkFilename = wxCheckBox(panel, -1, _("Restrict filenames to 31 characters"))
		if self.parent.pub.settings["ShortenFilenames"] == "Yes":
			self.chkFilename.SetValue(1)

		self.pubSizer = wxBoxSizer(wxVERTICAL)
		self.pubSizer.Add(self.chkFilename, 0, wxALL, 4)

		panel.SetAutoLayout(True)
		panel.SetSizer(self.pubSizer)
		self.pubSizer.Fit(panel)
		panel.Layout()

		#EVT_CHOICE(self, self.cmbTheme.GetId(), self.OnThemeChanged)
		#EVT_BUTTON(self, self.btnUpdateTheme.GetId(), self.btnUpdateThemeClicked)

		return panel

	def OnThemeChanged(self, event):
		if self.parent.pub.settings["Theme"] != self.cmbTheme.GetStringSelection():
			self.updateTheme = True

	def FTPPanel(self):
		panel = wxPanel(self.notebook, -1, wxPoint(25, 25))
		self.lblFTPSite = wxStaticText(panel, -1, _("FTP Site"))
		self.txtFTPSite = wxTextCtrl(panel, -1, self.parent.pub.settings["FTPHost"])
		self.lblUsername = wxStaticText(panel, -1, _("Username"))
		self.txtUsername = wxTextCtrl(panel, -1, self.parent.pub.settings["FTPUser"])
		self.lblPassword = wxStaticText(panel, -1, _("Password"))
		self.txtPassword = wxTextCtrl(panel, -1, self.parent.ftppass, wxDefaultPosition, wxDefaultSize, wxTE_PASSWORD)
		self.lblDirectory = wxStaticText(panel, -1, _("Directory"))
		self.txtDirectory = wxTextCtrl(panel, -1, self.parent.pub.settings["FTPDirectory"])
		self.chkPassiveFTP = wxCheckBox(panel, -1, _("Use Passive FTP"))
		if self.parent.pub.settings["FTPPassive"] == "Yes":
			self.chkPassiveFTP.SetValue(True)
		else:
			self.chkPassiveFTP.SetValue(False)
		self.chkUploadOnSave = wxCheckBox(panel, -1, _("Upload Files on Save"))
		if self.parent.pub.settings["UploadOnSave"] == "Yes":
			self.chkUploadOnSave.SetValue(True)
		else:
			self.chkUploadOnSave.SetValue(False)
		
		self.txtFTPSite.SetFocus()
		self.txtFTPSite.SetSelection(0, -1)

		self.ftpSizer = wxFlexGridSizer(0, 2, 4, 4)
		self.ftpSizer.Add(self.lblFTPSite, 0, wxALL, 4)
		self.ftpSizer.Add(self.txtFTPSite, 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.Add(self.lblUsername, 0, wxALL, 4)
		self.ftpSizer.Add(self.txtUsername, 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.Add(self.lblPassword, 0, wxALL, 4)
		self.ftpSizer.Add(self.txtPassword, 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.Add(self.lblDirectory, 0, wxALL, 4)
		self.ftpSizer.Add(self.txtDirectory, 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.Add(self.chkPassiveFTP, 0, wxALL, 4)
		self.ftpSizer.Add((1,1), 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.Add(self.chkUploadOnSave, 0, wxALL, 4)
		self.ftpSizer.Add((1,1), 1, wxEXPAND|wxALL, 4)
		self.ftpSizer.AddGrowableCol(1)

		panel.SetAutoLayout(True)
		panel.SetSizer(self.ftpSizer)
		self.ftpSizer.Fit(self)
		panel.Layout()

		return panel

	def SearchPanel(self):
		panel = wxPanel(self.notebook, -1, wxPoint(25, 25))
		self.chkSearch = wxCheckBox(panel, -1, _("Enable Search Function (Requires Greenstone)"))
		ischecked = self.parent.pub.settings["SearchEnabled"]
		searchtool = ""
		if not ischecked == "":
			try:
				searchbool = int(ischecked)
			except:
				searchbool = 0

			self.chkSearch.SetValue(searchbool)
			if searchbool:
				searchtool = self.parent.pub.settings["SearchProgram"]
				if searchtool == "": #since there wasn't an option selected, must be Greenstone
					searchtool = "Greenstone"
		
		self.options = [_("Use Lucene for searching (Default)"), _("Use Greenstone for searching")]
		self.whichSearch = wxRadioBox(panel, -1, _("Search Engine"), wxDefaultPosition, wxDefaultSize, self.options, 1)
		if searchtool == "Greenstone":
			self.whichSearch.SetStringSelection(self.options[1])
		elif searchtool == "Lucene":
			self.whichSearch.SetStringSelection(self.options[0])
		
		#self.useGSDL = wxRadioBox(panel, -1, )
		
		self.lblpubid = wxStaticText(panel, -1, _("Publication ID"), wxPoint(self.labelx, self.height + 10))
		self.txtpubid = wxTextCtrl(panel, -1, self.parent.pub.pubid, wxPoint(self.textx, self.height + 10), wxSize(240, self.height))
		self.lblpubidhelp = wxStaticText(panel, -1, _("ID must be 8 chars or less, no spaces, all letters\n and/or numbers."),wxPoint(self.textx, (self.height*2) + 10))

		value = self.chkSearch.GetValue()
		self.lblpubid.Enable(value)
		self.txtpubid.Enable(value)
		self.lblpubidhelp.Enable(value)
			
		self.searchSizer = wxBoxSizer(wxVERTICAL)

		self.searchSizer.Add(self.chkSearch, 0, wxALL, 4)
		self.searchSizer.Add(self.whichSearch, 0, wxALL, 4)
		self.searchSizer.Add(self.lblpubid, 0, wxALL|wxEXPAND, 4)
		self.searchSizer.Add(self.txtpubid, 0, wxALL, 4)
		self.searchSizer.Add(self.lblpubidhelp, 0, wxALL, 4)
		panel.SetAutoLayout(True)
		panel.SetSizer(self.searchSizer)
		self.searchSizer.Fit(panel)
		panel.Layout()

		EVT_CHECKBOX(self, self.chkSearch.GetId(), self.chkSearchClicked)
 
		return panel

	def chkSearchClicked(self, event):
		value = self.chkSearch.GetValue()
		self.lblpubid.Enable(value)
		self.txtpubid.Enable(value)
		self.lblpubidhelp.Enable(value)
		self.searchchanged = True
		
	def btnOKClicked(self, event):
		self.parent.pub.name = self.txtname.GetValue()
		self.parent.pub.description = self.txtdescription.GetValue()
		self.parent.pub.keywords = self.txtkeywords.GetValue()

		self.parent.pub.settings["SearchEnabled"] = int(self.chkSearch.GetValue())
		useswishe = False
		updatetheme = False
		if self.whichSearch.GetStringSelection() == self.options[0]:
			self.parent.pub.settings["SearchProgram"] = "Lucene"
			useswishe = True
		elif self.whichSearch.GetStringSelection() == self.options[1]:
			self.parent.pub.settings["SearchProgram"] = "Greenstone"

		if self.searchchanged:
			self.parent.Update()
		if self.chkFilename.GetValue() == True:
			self.parent.pub.settings["ShortenFilenames"] = "Yes"
		else:
			self.parent.pub.settings["ShortenFilenames"] = "No"

		self.parent.pub.settings["FTPHost"] = self.txtFTPSite.GetValue()
		self.parent.pub.settings["FTPDirectory"] = self.txtDirectory.GetValue()
		self.parent.pub.settings["FTPUser"] = self.txtUsername.GetValue()
		self.parent.ftppass = self.txtPassword.GetValue()
		#self.parent.pub.settings["FTPPassword"] = `munge(self.txtPassword.GetValue(), "foobar")`

		if self.chkPassiveFTP.GetValue() == True:
			self.parent.pub.settings["FTPPassive"] = "Yes"
		else:
			self.parent.pub.settings["FTPPassive"] = "No"

		if self.chkUploadOnSave.GetValue() == True:
			self.parent.pub.settings["UploadOnSave"] = "Yes"
		else:
			self.parent.pub.settings["UploadOnSave"] = "No"

		self.parent.pub.pubid = self.txtpubid.GetValue()
		self.parent.isDirty = True
		self.EndModal(wxID_OK)


(UpdateOutputEvent, EVT_OUTPUT_UPDATE) = newevent.NewEvent()
(IndexingCanceledEvent, EVT_INDEXING_CANCELED) = newevent.NewEvent()
(IndexingFinishedEvent, EVT_INDEXING_FINISHED) = newevent.NewEvent()

#--------------------------- Export to CD Progress Dialog Class --------------------------------------
class UpdateIndexDialog(wxDialog):
	def __init__(self, parent, usegsdl=False):
		"""
		Dialog for creating a full-text index of an EClass.

		"""
		wxDialog.__init__ (self, parent, -1, _("Indexing EClass"), wxPoint(100,100),wxSize(400,230), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		lblstart = 10
		txtstart = 80
		self.gsdl = ""
		self.usegsdl = usegsdl
		self.eclassdir = ""
		self.mythread = None
		self.stopthread = False
		self.exportfinished = False
		self.dialogtext = ""
		self.olddir = ""
		self.status = wxStaticText(self, -1, _("Updating full-text index..."), wxPoint(lblstart, 12))
		self.txtProgress = wxTextCtrl(self, -1, "", wxPoint(lblstart, 40), wxSize(360, height*6), wxTE_MULTILINE|wxTE_READONLY)

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.status, 0, wxALL, 4)
		self.mysizer.Add(self.txtProgress, 1, wxEXPAND | wxALL, 4)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()
 
		EVT_CLOSE(self, self.OnClose)
		EVT_OUTPUT_UPDATE(self, self.OnOutputUpdate)
		EVT_INDEXING_FINISHED(self, self.OnIndexingFinished)
		EVT_INDEXING_CANCELED(self, self.OnIndexingCanceled)
		self.Show(True)

	def OnOutputUpdate(self, event):
		self.txtProgress.WriteText("\n" + event.text)
		
	def OnIndexingCanceled(self, event):
		self.EndModal(wxID_CANCEL)
		
	def OnIndexingFinished(self, event):
		self.exportfinished = True
		if wxPlatform != '__WXMSW__' and os.path.exists(self.olddir):
			os.chdir(self.olddir)
		self.EndModal(wxID_OK)
		
	def OnClose(self, event):
		if not self.mythread == None:	
			#return
			self.stopthread = True
			self.txtProgress.WriteText(_("Sending cancel command to process. Please wait...")+"\n")
		else:
			self.EndModal(wxID_OK)	
	
	def UpdateIndex(self, gsdl, eclassdir):
		import threading
		captureoutput = True
		if self.parent.pub.settings["SearchProgram"] == "Greenstone":
			self.gsdl = self.parent.settings["GSDL"]
			self.eclassdir = os.path.join(self.gsdl, "collect", self.parent.pub.pubid) 
			self.processfinished = False
	
			if not os.path.exists(eclassdir):	
				self.call = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "mkcol.bat")) + " " + self.parent.pub.pubid + " " + win32api.GetShortPathName(self.gsdl)
				if captureoutput:
					self.mythread = threading.Thread(None, self.cmdline)
					self.mythread.start()
	
				else:
					os.system(call)
	
			if os.path.exists(eclassdir):
				collecttext = ""
				try:
					collectcfg = open(os.path.join(self.parent.AppDir, "greenstone", "collect.cfg"), "r")
					collecttext = collectcfg.read()
					collectcfg.close()
				except:
					self.txtProgress.WriteText(_("There was an error reading the file ") + "'" + os.path.join(self.parent.AppDir, "greenstone", "collect.cfg") + "'" + _(". Please ensure that the file exists and that you have read permissions."))
				try:
					collecttext = string.replace(collecttext, "**[title]**", self.parent.pub.name)
					collectout = open(os.path.join(eclassdir, "etc", "collect.cfg"), "w")
					collectout.write(collecttext)
					collectout.close()
				except:
					self.txtProgress.WriteText(_("There was an error writing the file '%(collectfile)s'. Please ensure that the file exists and that you have write permissions.") % {"collectfile": os.path.join(self.parent.AppDir, "greenstone", "collect.cfg")})
	
				files.CopyFiles(os.path.join(self.parent.CurrentDir, "pub"), os.path.join(eclassdir, "import"), 1)
					#...and build the collection
				self.call = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "buildcol.bat")) + " " + self.parent.pub.pubid + " " + win32api.GetShortPathName(gsdl) 
				if captureoutput:	 
					self.mythread = threading.Thread(None, self.cmdline)
					self.mythread.start()
				else:
					doscall = win32api.GetShortPathName(os.path.join(self.parent.AppDir, "greenstone", "buildcol.bat"))
					os.spawnv(os.P_WAIT, doscall, [doscall, self.parent.pub.pubid, win32api.GetShortPathName(gsdl)])
					self.txtProgress.WriteText(_("Copying eClass publication files to Greenstone..."))
					exportdir = os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid)
					if not os.path.exists(os.path.join(exportdir, "gsdl", "eclass")):
						os.mkdir(os.path.join(exportdir, "gsdl", "eclass"))
					files.CopyFiles(self.parent.CurrentDir, os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "eclass"), 1)
					files.CopyFile("home.dm", os.path.join(self.parent.AppDir, "greenstone"), os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "macros"))
					files.CopyFile("style.dm", os.path.join(self.parent.AppDir, "greenstone"), os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl", "macros"))
					self.status.SetLabel(_("""Finished exporting. You can find the exported 
collection at:""") + os.path.join(gsdl, "tmp", "exported_" + self.parent.pub.pubid))
		elif self.parent.pub.settings["SearchProgram"] == "Swish-E":
			olddir = ""
			swishedir = os.path.join(self.parent.ThirdPartyDir, "SWISH-E")
			swisheconf = os.path.join(self.parent.pub.directory, "swishe.conf")
			swisheindex = os.path.join(self.parent.pub.directory, "index.swish-e")
			swisheinclude = self.parent.pub.directory
			if wxPlatform == "__WXMSW__":
				#swishedir = win32api.GetShortPathName(os.path.join(swishedir, "swish.bat"))
				swisheconf = win32api.GetShortPathName(swisheconf)
				swisheindex = os.path.join(win32api.GetShortPathName(self.parent.pub.directory), "index.swish-e")
				#swisheinclude = win32api.GetShortPathName(self.parent.pub.directory)
				self.call = win32api.GetShortPathName(os.path.join(swishedir, "swish.bat")) + " " + win32api.GetShortPathName(self.parent.pub.directory) + " " + win32api.GetShortPathName(os.path.join(swishedir, "swish-e.exe"))
			else:
				swishedir = os.path.join(swishedir, "bin")
				self.olddir = os.getcwd()
				os.chdir(self.parent.pub.directory)
				self.call = os.path.join(swishedir, "swish-e") + " -c ./swishe.conf -f index.swish-e"				
			#self.call = swishedir + " -c \"" + swisheconf + "\" -f \"" + swisheindex + "\"" # -i \"" + swisheinclude + "\""
			#self.txtProgress.WriteText("Using swish-e!\n")
			self.txtProgress.WriteText(self.call + "\n")
			print self.call
			self.dialogtext = ""
			self.mythread = threading.Thread(None, self.cmdline)
			self.mythread.start()

			while self.mythread.isAlive():
				wxSleep(1)
			self.mythread = None
			if wxPlatform != '__WXMSW__' and os.path.exists(olddir):
				os.chdir(olddir)
			if self.stopthread == True:
				self.EndModal(wxID_OK)
			self.status.SetLabel(_("Finished exporting!"))
		elif self.parent.pub.settings["SearchProgram"] == "Lucene":
			engine = indexer.SearchEngine(self, os.path.join(self.parent.CurrentDir, "index.lucene"))
			engine.IndexFiles(self.parent.pub.nodes[0])
			
		self.exportfinished = True

	def cmdline(self):
		import time
		if wxPlatform == "__WXMSW__":
			myin, myout = win32pipe.popen4(self.call)
		else:
			myin, myout = os.popen4(self.call)
		while 1:
			line = myout.readline()
			if not line:
				break
			elif self.stopthread == True:
				evt = IndexingCanceledEvent()
				wxPostEvent(self, evt)
				#self.txtProgress.WriteText(_("Cancelling process...")+"\n")
				break
			else:
				evt = UpdateOutputEvent(text = line)
				wxPostEvent(self, evt)
			time.sleep(0.01)
			
		evt = IndexingFinishedEvent()
		wxPostEvent(self, evt)
		myin.close()
		myout.close()

	def write(self, s):
		self.txtProgress.WriteText(s)

	def btnViewFolderClicked(self, event):
		if self.usegsdl:
			win32api.ShellExecute(0, "open",os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid), "", os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid), 1)
		else:
			win32api.ShellExecute(0, "open",self.parent.pub.directory, "", self.parent.pub.directory, 1)

	def btnTestCDClicked(self, event):
		win32api.ShellExecute(0, "open", "server.exe", "", os.path.join(self.gsdl, "tmp", "exported_" + self.parent.pub.pubid, "gsdl"), 1)

	def btnCloseWindowClicked(self, event):
		self.Destroy()

(UpdateFTPDialogEvent, EVT_UPDATE_FTPDIALOG) = newevent.NewEvent()
(UploadFinishedEvent, EVT_UPLOAD_FINISHED) = newevent.NewEvent()
(UploadCanceledEvent, EVT_UPLOAD_CANCELED) = newevent.NewEvent()

#--------------------------- FTP Upload Dialog Class --------------------------------------
class FTPUpload:
	def __init__(self, parent):
		self.filelist = []
		self.dirlist = []
		self.parent = parent
		self.isDialog = False
		self.FTPSite = parent.pub.settings["FTPHost"]
		self.Username = parent.pub.settings["FTPUser"]
		self.Directory = parent.pub.settings["FTPDirectory"]
		self.Password = parent.ftppass #munge(parent.pub.settings["FTPUsername"], "foobar")
		self.stopupload = False
		self.useSearch = 0
		self.projpercent = 0
		self.filepercent = 0

		if parent.pub.settings["FTPPassive"] == "yes":
			self.usePasv = True
		else:
			self.usePasv = False

		if parent.pub.settings["SearchEnabled"] != "":
			self.useSearch = int(parent.pub.settings["SearchEnabled"])

	def StartFTP(self):
		if self.Password == "":
			dialog = wxTextEntryDialog(self.parent, _("Please enter a password to upload to FTP."), _("Enter Password"), "", wxTE_PASSWORD | wxOK | wxCANCEL)
			if dialog.ShowModal() == wxID_OK:
				self.Password = dialog.GetValue()
			else:
				return False

		self.host = ftplib.FTP(self.FTPSite, self.Username, self.Password)
		self.host.set_pasv(self.usePasv)
		self.host.sock.setblocking(1)
		self.host.set_debuglevel(2)
		self.host.sock.settimeout(60)
		return True

	def GenerateFileList(self, indir):
		if self.useSearch == 0 and string.find(indir, "cgi-bin") != -1:
			return
		parentdir = self.parent.CurrentDir
		if wxPlatform == "__WXMSW__":
			parentdir = parentdir + "\\"
		else:
			parentdir = parentdir + "/"
		mydir = string.replace(indir, parentdir, "")
		if wxPlatform == "__WXMSW__":
			mydir = string.replace(mydir, "\\", "/")
		#if not mydir in self.dirlist:
		if not string.find(mydir, "C:") == 0:
			fulldir = self.Directory + "/" + mydir
			if not fulldir[0] == "/":
				fulldir = "/" + fulldir
			self.dirlist.append(fulldir)

		for item in os.listdir(indir):
			myitem = os.path.join(indir, item)
			
			if os.path.isfile(myitem) and not string.find(item, "._") == 0 and string.find(item, "Karrigell") == -1 and string.find(item, "httpserver") == -1 and string.find(item, "ftppass.txt") == -1:
				finalname = string.replace(myitem, parentdir, "")
				if wxPlatform == "__WXMSW__":
					finalname = string.replace(finalname, "\\", "/")
				#finalname = string.replace(finalname, os.pathsep, "/")
				if string.find(myitem, "cgi-bin") == -1:
					if string.find(item, ".dll") == -1 and string.find(item, ".pyd") == -1 and string.find(item, ".exe") == -1:
						self.filelist.append(finalname)
				else:
					self.filelist.append(finalname)
			elif os.path.isdir(myitem):
				self.GenerateFileList(myitem)

	def CreateDirectories(self):
		self.StartFTP()
		ftpdir = self.Directory
		if not ftpdir == "" and not ftpdir[0] == "/":
			ftpdir = "/" + ftpdir 
		if not ftpdir == "" and not ftpdir[-1] == "/":
			ftpdir = ftpdir + "/"
		self.cwd(ftpdir)
		for item in self.dirlist:
			self.cwd(item) #create the folders if they don't already exist

	def UploadFiles(self):
		import time
		if self.stopupload:
			self.host.close()
			return
		self.StartFTP()
		self.CreateDirectories()

		#lastdir = self.Directory #this should have gotten created already
		if self.Directory == "" or not self.Directory[-1] == "/":
			self.Directory = self.Directory + "/"
		if self.isDialog:
			if wxPlatform != "__WXMAC__":
				self.projGauge.SetRange(len(self.filelist))
		myfile = None
		for item in self.filelist[:]:
			try:
				if self.stopupload:
					self.host.close()
					evt = UploadCanceledEvent()
					wxPostEvent(self, evt)
					return

				myitem = os.path.join(self.parent.CurrentDir, item)
				myfile = open(myitem, "rb")
				bytes = os.path.getsize(myitem)
				dir = self.Directory
				if not dir[-1] == "/":
					dir = dir + "/"
				if not dir[0] == "/":
					dir = "/" + dir
				if string.find(item, "/") != -1:
					mydir, myitem = os.path.split(item)					
					dir = dir + string.replace(mydir, "\\", "/")
					if not dir[-1] == "/":
						dir = dir + "/"
				else:
					myitem = item
		
				self.host.voidcmd('TYPE I')
				self.mysocket = self.host.transfercmd('STOR ' + dir + myitem)
				self.filepercent = 0

				evt = UpdateFTPDialogEvent(projpercent = self.projpercent, filepercent = self.filepercent)
				wxPostEvent(self, evt)

				onepercent = bytes/100
				if onepercent == 0:
					onepercent = 1
				if self.mysocket:
					#self.mysocket.setblocking(1)
					self.mysocket.settimeout(30)
					if self.isDialog:
						self.txtProgress.SetLabel(_("Current File: ") + myitem)
					elif self.parent:
						self.parent.SetStatusText(_("Uploading file %(file)s...") % {"file": myitem})
					bytesuploaded = 0
					while 1:
						block = myfile.read(4096)
						if not block or self.stopupload:
							break

						resp = self.mysocket.sendall(block)
						time.sleep(1)
						bytesuploaded = bytesuploaded + 4096
						if self.isDialog:
							self.filepercent = bytesuploaded/onepercent
							evt = UpdateFTPDialogEvent(projpercent = self.projpercent, filepercent = self.filepercent)
							wxPostEvent(self, evt)
						elif self.parent:
							self.parent.SetStatusText(_("Uploaded %(current)d of %(total)d bytes for file %(filename)s." % {"current":bytesuploaded, "total":bytes, "filename":myitem})) 
						wxYield()
					self.mysocket.close()
					self.mysocket = None
					self.host.voidresp()
					myindex = self.filelist.index(item)
					self.filelist.remove(item)

				myfile.close()

				self.projpercent = self.projpercent + 1
				evt = UpdateFTPDialogEvent(projpercent = self.projpercent, filepercent = self.filepercent)
				wxPostEvent(self, evt)

			except ftplib.all_errors, e:
				if myfile:
					myfile.close()
				raise

		self.host.quit()
		evt = UploadFinishedEvent()
		wxPostEvent(self, evt)

	def getFtpErrorMessage(self, e):
		""" Given an ftplib error object, generate some common error messages. """
		code = ""
		try:
			code = e.args[0][:3]
		except:
			code = repr(e)[:3]

		if code == "550":
			return _("Attempt to create a file or directory on the server failed. Please check your file permissions. The error reported was: \n\n" + str(e.args[0]))
		elif code == "530":
			return _("EClass was unable to connect to the specified FTP server. Please check to ensure your server name, username and password are correct. The error message returned was:") + "\n\n" + str(e)
		elif code == "425":
			return _("Cannot open a data connection. Try changing the \"Use Passive FTP\" setting and uploading again.")
		elif code == "426":
			return _("Connection closed by server. Click Upload again to resume upload.")
		elif code == "452":
			return _("Server is full. You will need to either delete files from the server or ask for more server space from your system administrator.")
		else: 
			return _("An unexpected error has occurred while uploading. Please click 'Upload' again to attempt to resume uploading. The error reported was: \n\n" + repr(e)) 
			#self.parent.logfile.write(str(e))

	def cwd(self, item):
		myitem = item
		try:
			if not string.rfind(myitem, "/") == 0:
				myitem = myitem + "/"
			self.host.cwd(myitem)
		except:
			try:
				self.host.mkd(myitem)
				self.host.cwd(myitem)
			except ftplib.all_errors, e:
				raise

class FTPUploadDialog(wxDialog, FTPUpload):
	def __init__(self, parent):
		FTPUpload.__init__(self, parent)
		self.isDialog = True
		wxDialog.__init__ (self, parent, -1, _("Publish to web site"), wxPoint(100,100),wxSize(250,260), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.makefilelist = True
		self.mythread = None
		self.closewindow = False
		self.filelist = []
		self.folderlist = []
		self.projpercent = 0
		self.filepercent = 0
		#lines up labels and textboxes
		lblstart = 10
		txtstart = 80
		
		self.lblFTPSite = wxStaticText(self, -1, _("FTP Site"))
		self.txtFTPSite = wxTextCtrl(self, -1, self.parent.pub.settings["FTPHost"])
		self.lblUsername = wxStaticText(self, -1, _("Username"))
		self.txtUsername = wxTextCtrl(self, -1, self.parent.pub.settings["FTPUser"], wxPoint(txtstart, 30), wxSize(180, -1))
		self.lblPassword = wxStaticText(self, -1, _("Password"))
		self.txtPassword = wxTextCtrl(self, -1, self.parent.ftppass, style=wxTE_PASSWORD)
		self.lblDirectory = wxStaticText(self, -1, _("Directory"))
		self.txtDirectory = wxTextCtrl(self, -1, self.parent.pub.settings["FTPDirectory"])
		self.txtProgress = wxStaticText(self, -1, "Current File:") #wxTextCtrl(self, -1, "", style=wxTE_MULTILINE|wxTE_READONLY)
		self.fileGauge = wxGauge(self, -1, 1, style=wxGA_PROGRESSBAR)
		self.fileGauge.SetRange(100)
		self.txtTotalProg = wxStaticText(self, -1, "Total Progress:")
		self.projGauge = wxGauge(self, -1, 1, style=wxGA_PROGRESSBAR)
		self.projGauge.SetRange(100)
		#self.lstFiles = wxListBox(self, -1, style=wxLB_SINGLE)
		self.chkPassive = wxCheckBox(self, -1, _("Use Passive FTP"))
		self.stopupload = False

		self.btnOK = wxButton(self,-1,_("Upload"))
		self.btnOK.SetDefault()
		self.txtFTPSite.SetFocus()
		self.txtFTPSite.SetSelection(0, -1)
		self.btnCancel = wxButton(self,-1,_("Close"))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.gridsizer = wxFlexGridSizer(0, 2, 4, 4)
		self.gridsizer.Add(self.lblFTPSite, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtFTPSite, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblUsername, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtUsername, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblPassword, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtPassword, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add(self.lblDirectory, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtDirectory, 1, wxEXPAND|wxALIGN_RIGHT|wxALL, 4)
		self.gridsizer.Add((1, 1), 0, wxALL, 4)
		self.gridsizer.Add(self.chkPassive, 0, wxALIGN_RIGHT|wxALL, 4)
		self.mysizer.Add(self.gridsizer, 3, wxEXPAND|wxALL)
		self.mysizer.Add(self.txtProgress, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.fileGauge, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.txtTotalProg, 0, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.projGauge, 0, wxEXPAND|wxALL, 4)
		#self.mysizer.Add(self.lstFiles, 2, wxEXPAND|wxALL, 4)
		
		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0, wxALIGN_RIGHT)

		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnCancel, self.btnCancel.GetId(), self.btnCancelClicked)
		EVT_CLOSE(self, self.OnClose)
		EVT_UPDATE_FTPDIALOG(self, self.OnUpdateDialog)
		EVT_UPLOAD_FINISHED(self, self.OnUploadFinished)
		EVT_UPLOAD_CANCELED(self, self.OnUploadCanceled)
		
	def OnUploadFinished(self, event):
		self.txtProgress.SetLabel(_("Finished uploading.\n"))
		self.parent.SetStatusText(_("Finished uploading."))
		self.fileGauge.SetValue(0)
		self.projGauge.SetValue(0)
		self.btnCancel.SetLabel(_("Close"))
		self.btnOK.Enable(True)
		
	def OnUploadCanceled(self, event):
		self.txtProgress.SetLabel(_("Disconnected. Upload cancelled by user.\n"))
		self.btnCancel.SetLabel(_("Close"))
		self.btnOK.Enable(True)
		self.stopupload = False
		if self.closewindow == True:
			self.EndModal(wxID_OK)
		
	def OnUpdateDialog(self, event):
		self.projGauge.SetValue(event.projpercent)
		self.fileGauge.SetValue(event.filepercent)

	def OnClose(self, event):
		if not self.mythread == None:
			self.stopupload = True
			self.closewindow = True
		else:
			self.EndModal(wxID_OK)

	def btnCancelClicked(self, event):
		if self.btnCancel.GetLabel() == _("Cancel"):
			self.stopupload = True

		else:				
			self.parent.pub.settings["FTPHost"] = self.txtFTPSite.GetValue()
			self.parent.pub.settings["FTPUser"] = self.txtUsername.GetValue()
			self.parent.pub.settings["FTPDirectory"] = self.txtDirectory.GetValue()
			#self.parent.pub.settings["FTPPassword"] = `munge(self.txtPassword.GetValue(), "foobar")`
			self.stopupload = True
			#self.parent.pub.settings["FTPPassive"] = int(self.chkPassive.GetValue())
			self.EndModal(wxID_CANCEL)

	def btnOKClicked(self, event):
		import threading
		self.FTPSite = self.txtFTPSite.GetValue()
		self.Username = self.txtUsername.GetValue()
		self.Password = self.txtPassword.GetValue()
		self.Directory = self.txtDirectory.GetValue()
		if self.chkPassive.IsChecked():
			self.usePasv = True
		else:
			self.usePasv = False

		try:
			self.StartFTP()
		except IOError, e:
			mesesage = utils.getStdErrorMessage(e, {"filename":e.filename})
			wxMessageDialog(message)
		except ftplib.all_errors, e:
			message = self.getFtpErrorMessage(e)
			self.parent.logfile.write(message)
			wxMessageDialog(self, message, _("FTP Login Error"), wxOK).ShowModal()
			return

		self.btnOK.Enable(False)
		self.btnCancel.SetLabel(_("Cancel"))
		if self.makefilelist:
			self.GenerateFileList(self.parent.CurrentDir)
			self.makefilelist = False
		self.mythread = threading.Thread(None, self.UploadFiles)
		try:
			self.mythread.run()
		except ftplib.all_errors, e:
			self.host.close()
			wxMessageBox(self.getFtpErrorMessage(e))
			self.OnUploadCanceled(None)
		return

#--------------------------- PreferencesEditor Class --------------------------------------
class PreferencesEditor(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("System Preferences"), wxPoint(100,100),wxSize(300,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		icnFolder = wxBitmap(os.path.join(parent.AppDir, "icons", "Open.gif"), wxBITMAP_TYPE_GIF)
		self.lblHTMLEditor = wxStaticText(self, -1, _("HTML Editor"), wxPoint(10, 12))
		self.txtHTMLEditor = wxTextCtrl(self, -1, parent.settings["HTMLEditor"], wxPoint(80, 10), wxSize(180, -1))
		self.btnHTMLEditor = wxBitmapButton(self, -1, icnFolder, wxPoint(250, 10), wxSize(20, 18))
		self.lblOpenOffice = wxStaticText(self, -1, _("OpenOffice Folder"), wxPoint(10, 12))
		self.txtOpenOffice = wxTextCtrl(self, -1, parent.settings["OpenOffice"], wxPoint(80, 10), wxSize(180, -1))
		self.btnOpenOffice = wxBitmapButton(self, -1, icnFolder, wxPoint(250, 10), wxSize(20, 18))
		self.lblCourseFolder = wxStaticText(self, -1, _("Course Folder"), wxPoint(10, 12 + (height)))
		self.txtCourseFolder = wxTextCtrl(self, -1, parent.settings["CourseFolder"], wxPoint(80, 10 + (height)), wxSize(180, -1))
		self.btnCourseFolder = wxBitmapButton(self, -1, icnFolder, wxPoint(250, 10 + height), wxSize(20, 18))
		self.lblGSDL = wxStaticText(self, -1, _("Greenstone Directory"), wxPoint(10, 12 + (height*2)))
		self.txtGSDL = wxTextCtrl(self, -1, parent.settings["GSDL"], wxPoint(80, 10 + (height*2)), wxSize(180, -1))
		self.btnGSDL = wxBitmapButton(self, -1, icnFolder, wxPoint(250, 10 + (height*2)), wxSize(20, 18))
		self.lblLanguage = wxStaticText(self, -1, _("Language"))
		self.languages = ["English", "Francais", "Espanol"]

		self.cmbLanguage = wxChoice(self, -1, wxDefaultPosition, wxDefaultSize, self.languages)
		if parent.settings["Language"] != "":
			self.cmbLanguage.SetStringSelection(parent.settings["Language"])
			
		self.lblDefaultPlugin = wxStaticText(self, -1, _("New Page Default"))
		self.pluginnames = []
		for plugin in myplugins:
			if plugin["CanCreateNew"]:
				self.pluginnames.append(plugin["FullName"])
		self.cmbDefaultPlugin = wxChoice(self, -1, wxDefaultPosition, wxDefaultSize, self.pluginnames)
		if parent.settings["DefaultPlugin"] != "":
			self.cmbDefaultPlugin.SetStringSelection(parent.settings["DefaultPlugin"])

		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(100, 140),wxSize(76, 24))
		self.btnOK.SetDefault()

		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))#,wxPoint(190, 140),wxSize(76,24))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		#create the grid sizer
		self.gridsizer = wxFlexGridSizer(0, 3, 4, 4)
		self.gridsizer.Add(self.lblHTMLEditor, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtHTMLEditor, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add(self.btnHTMLEditor, 0, wxALIGN_CENTER|wxALL, 4)
		self.gridsizer.Add(self.lblOpenOffice, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtOpenOffice, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add(self.btnOpenOffice, 0, wxALIGN_CENTER|wxALL, 4)
		self.gridsizer.Add(self.lblCourseFolder, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtCourseFolder, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add(self.btnCourseFolder, 0, wxALIGN_CENTER|wxALL, 4)
		self.gridsizer.Add(self.lblGSDL, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.txtGSDL, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add(self.btnGSDL, 0, wxALIGN_CENTER|wxALL, 4)
		self.gridsizer.Add(self.lblLanguage, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.cmbLanguage, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add((1, 1), 1, wxALL, 4)
		self.gridsizer.Add(self.lblDefaultPlugin, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.cmbDefaultPlugin, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add((1, 1), 1, wxALL, 4)
		#self.gridsizer.Add((1, 1), 1, wxALL, 4)
		#self.gridsizer.Add(self.chkAutoName, 1, wxALIGN_RIGHT|wxALL, 2)
		#self.gridsizer.Add((1, 1), 1, wxALL, 4)
		self.mysizer.Add(self.gridsizer, 1, wxEXPAND)
		
		#create the button sizer
		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0, wxALIGN_RIGHT)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnCourseFolder, self.btnCourseFolder.GetId(), self.btnCourseFolderClicked)
		EVT_BUTTON(self.btnHTMLEditor, self.btnHTMLEditor.GetId(), self.btnHTMLEditorClicked)
		EVT_BUTTON(self.btnGSDL, self.btnGSDL.GetId(), self.btnGSDLClicked)
		EVT_BUTTON(self.btnOpenOffice, self.btnOpenOffice.GetId(), self.btnOpenOfficeClicked)
		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
	
	def btnOKClicked(self, event):
		self.parent.settings["HTMLEditor"] = self.txtHTMLEditor.GetValue()
		if self.txtOpenOffice.GetValue() != "" and self.parent.settings["OpenOffice"] != self.txtOpenOffice.GetValue():
			self.parent.settings["OpenOffice"] = self.txtOpenOffice.GetValue()
			if self.CheckAutostartPyUNO() == False:
				if self.AutostartPyUNO():
					wxMessageBox(_("If you have OpenOffice running, please close and restart it now to enable Word document support."))
				else:
					wxMessageBox(_("Failed to configure OpenOffice."))
		else:
			self.parent.settings["OpenOffice"] = self.txtOpenOffice.GetValue()

		self.parent.settings["GSDL"] = self.txtGSDL.GetValue()
		self.parent.settings["CourseFolder"] = self.txtCourseFolder.GetValue()
		self.parent.settings["DefaultPlugin"] = self.cmbDefaultPlugin.GetStringSelection()
		language = self.parent.settings["Language"]
		if language != self.cmbLanguage.GetStringSelection():
			self.parent.settings["Language"] = self.cmbLanguage.GetStringSelection()
			#self.parent.LoadLanguage()
			wxMessageDialog(self, _("You will need to restart EClass.Builder for changes to take effect."), _("Restart required."), wxOK).ShowModal()
		self.EndModal(wxID_OK)

	def CheckAutostartPyUNO(self):
		import re
		myfilename = ""
		if os.name == "nt":
			myfilename = os.path.join(self.parent.settings["OpenOffice"], "share", "registry", "data", "org", "openoffice", "Setup.xcu")
		try:
			print "Registering Pyuno... Location is: " + myfilename
			file = open(myfilename, "r")
			data = file.read()
			file.close()
			if string.find(data, "<prop oor:name=\"ooSetupConnectionURL\">") != -1:
				return True
			else:
				return False
		except:
			return False

	def AutostartPyUNO(self):
		import re
		myfilename = ""
		if os.name == "nt":
			myfilename = os.path.join(self.parent.settings["OpenOffice"], "share", "registry", "data", "org", "openoffice", "Setup.xcu")
		try:
			print "Registering Pyuno... Location is: " + myfilename
			file = open(myfilename, "r")
			data = file.read()
			file.close()
			file = open(myfilename + ".bak", "w")
			file.write(data)
			file.close()
			if string.find(data, "<prop oor:name=\"ooSetupConnectionURL\">") == -1:
				if string.find(data, "<node oor:name=\"Office\">") > -1:
					myterm = re.compile("(<node oor:name=\"Office\">)", re.IGNORECASE|re.DOTALL)
					data = myterm.sub("\\1\n<prop oor:name=\"ooSetupConnectionURL\"><value>socket,host=localhost,port=2002;urp;</value></prop>\n", data)
				else:
					data = data + """
					<node oor:name="Office">
						<prop oor:name="ooSetupConnectionURL">socket,host=localhost,port=2002;urp;</prop>
					</node>
					"""
				file = open(myfilename, "w")
				file.write(data)
				file.close()
			return True
		except:
			print "Sorry, cannot register OpenOffice."
			return False

	def btnHTMLEditorClicked(self, event):
		defaultdir = "."
		type = "All Files(*.*)|*.*"
		if wxPlatform == "__WXMSW__":
			defaultdir = "C:\Program Files"
			type = "Program Files(*.exe)|*.exe"
		elif wxPlatform == "__WXMAC__":
			defaultdir = "/Applications"
		f = wxFileDialog(self, _("Select a file"), defaultdir, "", type, wxOPEN)
		if f.ShowModal() == wxID_OK:
			self.txtHTMLEditor.SetValue(f.GetPath())
		f.Destroy()

	def btnCourseFolderClicked(self, event):
		f = wxDirDialog(self, _("Select a folder to store your courses"))
		if f.ShowModal() == wxID_OK:
			self.txtCourseFolder.SetValue(f.GetPath())
		f.Destroy()

	def btnGSDLClicked(self, event):
		f = wxDirDialog(self, _("Select the folder containing your Greenstone installation"))
		if f.ShowModal() == wxID_OK:
			self.txtGSDL.SetValue(f.GetPath())
		f.Destroy()

	def btnOpenOfficeClicked(self, event):
		f = wxDirDialog(self, _("Select the folder containing your OpenOffice installation"))
		if f.ShowModal() == wxID_OK:
			self.txtOpenOffice.SetValue(f.GetPath())
		f.Destroy()

#--------------------------- NewPubDialog Class ---------------------------------------

class NewPubDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("New Project"), wxPoint(100,100),wxSize(400,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.lblTitle = wxStaticText(self, -1, _("Name"), wxPoint(10, 12))
		self.txtTitle = wxTextCtrl(self, -1, "", wxPoint(80, 10), wxDefaultSize) #wxSize(160, height))
		self.lblDescription = wxStaticText(self, -1, _("Description"), wxPoint(10, 12 + (height)))
		self.txtDescription = wxTextCtrl(self, -1, "", wxPoint(80, 10 + (height)), wxDefaultSize, wxTE_MULTILINE)
		self.lblKeywords = wxStaticText(self, -1, _("Keywords"), wxPoint(10, 12 + (height*4)))
		self.txtKeywords = wxTextCtrl(self, -1, "", wxPoint(80, 10 + (height*4)), wxDefaultSize) #wxSize(160, height))

		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(100, 12 + (height*6)),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(0, -1)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))#,wxPoint(190, 12 + (height*6)),wxSize(76,24))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.TitleSizer = wxFlexGridSizer(0, 2, 4, 4)
		self.TitleSizer.Add(self.lblTitle, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.txtTitle, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.Add(self.lblDescription, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.txtDescription, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.Add(self.lblKeywords, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.txtKeywords, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.AddGrowableCol(1)
		self.mysizer.Add(self.TitleSizer, 1, wxEXPAND)
		#self.mysizer.Add(25, 300, 0)
		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0)
		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
	
	def btnOKClicked(self, event):
		self.parent.CurrentDir = self.parent.pub.directory = os.path.join(self.parent.settings["CourseFolder"], MakeFolder(self.txtTitle.GetValue()))
		#print self.parent.CurrentDir

		if not os.path.exists(self.parent.CurrentDir):
			os.mkdir(self.parent.CurrentDir)
			self.parent.pub.name = self.txtTitle.GetValue()
			self.parent.pub.description = self.txtDescription.GetValue()
			self.parent.pub.keywords = self.txtKeywords.GetValue()
			self.EndModal(wxID_OK)
		else:
			wxMessageDialog(self, _("A publication with this name already exists. Please choose another name."), _("Publication exists!"), wxOK).ShowModal()

#--------------------------- NewPageDialog Class ---------------------------------------

class NewPageDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("New Page"), wxPoint(100,100),wxSize(400,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.lblTitle = wxStaticText(self, -1, _("Name"), wxPoint(10, 12))
		self.txtTitle = wxTextCtrl(self, -1, _("New Page"))
		self.lblType = wxStaticText(self, -1, "Type")
		self.cmbType = wxChoice(self, -1)

		self.lblFilename = wxStaticText(self, -1, "Filename")
		self.txtFilename = wxTextCtrl(self, -1, _("New Page"))
		self.filenameEdited = False
		
		extension = ".ecp"
		for plugin in myplugins:
			if plugin["CanCreateNew"]:
				self.cmbType.Append(plugin["FullName"])
			if self.parent.settings["DefaultPlugin"] != "" and plugin["FullName"] == self.parent.settings["DefaultPlugin"]:
				extension = "." + plugin["Extension"][0]
		
		if self.parent.settings["DefaultPlugin"] != "":
			self.cmbType.SetStringSelection(self.parent.settings["DefaultPlugin"])
		else:
			self.cmbType.SetStringSelection("EClass Page")
		self.txtFilename.SetValue(self.txtTitle.GetValue())
		self.UpdateFilename(None)

		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(100, 12 + (height*6)),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(0, -1)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))#,wxPoint(190, 12 + (height*6)),wxSize(76,24))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.TitleSizer = wxFlexGridSizer(0, 2, 4, 4)
		self.TitleSizer.Add(self.lblTitle, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.txtTitle, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.Add(self.lblFilename, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.txtFilename, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.Add(self.lblType, 0, wxALIGN_RIGHT|wxALL, 4)
		self.TitleSizer.Add(self.cmbType, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.TitleSizer.AddGrowableCol(1)
		self.mysizer.Add(self.TitleSizer, 1, wxEXPAND)
		#self.mysizer.Add(25, 300, 0)
		self.buttonSizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonSizer.Add((100, height), 1, wxEXPAND)
		self.buttonSizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonSizer.Add(self.btnCancel, 0, wxALL, 4)
		self.mysizer.Add(self.buttonSizer, 0)
		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnCancel, self.btnCancel.GetId(), self.btnCancelClicked)
		EVT_CHOICE(self, self.cmbType.GetId(), self.UpdateFilename)
		EVT_CHAR(self.txtFilename, self.CheckFilename)
		EVT_TEXT(self, self.txtTitle.GetId(), self.UpdateFilename)

	def CheckFilename(self, event):
		if len(self.txtFilename.GetValue()) >= 31 and not event.GetKeyCode() == WXK_BACK:
			return
		else: 
			self.filenameEdited = True
			event.Skip()
		
	
	def UpdateFilename(self, event):
		title = self.txtFilename.GetValue()
		if string.find(title, ".") != -1:
			title = title[:string.rfind(title, ".")]

		pluginname = self.cmbType.GetStringSelection()
		extension = ".ecp"
		for plugin in myplugins:
			if plugin["FullName"] == pluginname:
				extension = "." + plugin["Extension"][0]
				break

		if not self.filenameEdited:
			title = MakeFileName2(self.txtTitle.GetValue())
		
		title = title[:31-len(extension)]

		filename = title + extension
		counter = 2
		oldtitle = title
		import glob
		while len(glob.glob(os.path.join(self.parent.CurrentDir, "EClass", title + ".*"))) > 0 or len(glob.glob(os.path.join(self.parent.CurrentDir, "Text", title + ".*"))) > 0:
			#name = "New Page " + `counter`
			title = oldtitle + " " + `counter`
			filename = title + extension
			counter = counter + 1
		self.txtFilename.SetValue(filename)


	def btnCancelClicked(self, event):
		if self.parent.isNewCourse:
			wxMessageBox(_("You must create a root page for this course."))
			return

		self.EndModal(wxID_CANCEL)

	def btnOKClicked(self, event):
		pluginname = self.cmbType.GetStringSelection()
		for plugin in myplugins:
			if plugin["FullName"] == pluginname:
				break

		if os.path.exists(os.path.join(self.parent.CurrentDir, plugin["Directory"], self.txtFilename.GetValue())):
			wxMessageBox(_("Filename already exists. Please rename the file and try again."))
		else:
			self.EndModal(wxID_OK)

#--------------------------- OpenPubDialog Class ---------------------------------------

class OpenPubDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Open Publication"), wxPoint(100,100),wxSize(480,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.lblSelect = wxStaticText(self, -1, _("Select a publication:"))
		self.cmbpubs = wxListBox(self, -1, wxDefaultPosition, wxSize(-1, height*5))
		self.coursedir = parent.settings["CourseFolder"]
		if os.path.exists(self.coursedir):
			for item in os.listdir(self.coursedir):
				try:
					mypub = os.path.join(self.coursedir, item)
					if os.path.isdir(mypub) and os.path.exists(os.path.join(mypub, "imsmanifest.xml")):
						self.cmbpubs.Append(item)
				except:
					pass
		
		self.btnBrowse = wxButton(self, -1, _("Browse..."))
		self.btnOK = wxButton(self,wxID_OK, _("OK"))
		self.btnOK.SetDefault()
		self.cmbpubs.SetFocus()
		if self.cmbpubs.GetCount() > 0:
			self.cmbpubs.SetSelection(0)
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.lblSelect, 0, wxALL, 4)
		self.mysizer.Add(self.cmbpubs, 1, wxEXPAND|wxALL, 4)
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add(self.btnBrowse, 0, wxALIGN_LEFT|wxALL, 4)
		self.buttonsizer.Add((1,1),1, wxEXPAND | wxALL, 4)
		self.buttonsizer.Add(self.btnOK, 0, wxALIGN_RIGHT|wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALIGN_RIGHT|wxALL,4)
		self.mysizer.Add(self.buttonsizer, 0, wxEXPAND | wxALL, 4)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		EVT_BUTTON(self.btnBrowse, self.btnBrowse.GetId(), self.btnBrowseClicked)
		EVT_LEFT_DCLICK(self.cmbpubs, self.btnOKClicked)

	def btnBrowseClicked(self, event):
		dir = ""
		f = wxDirDialog(self, _("Select the folder containing your EClass"))
		if f.ShowModal() == wxID_OK:
			dir = f.GetPath()
			f.Destroy()
			if not os.path.exists(os.path.join(dir, "imsmanifest.xml")):
				message = _("This folder does not contain an EClass Project. Please try selecting another folder.")
				dialog = wxMessageDialog(self, message, "No EClass Found", wxOK)
				dialog.ShowModal()
				dialog.Destroy()
				return

			self.parent.CurrentDir = dir
			if wxPlatform == '__WXMSW__':
				self.parent.CurrentDir = win32api.GetShortPathName(self.parent.CurrentDir)
			self.EndModal(wxID_OK)

	def btnOKClicked(self, event):
		if self.cmbpubs.GetStringSelection() != "":
			self.parent.CurrentDir = os.path.join(self.coursedir, self.cmbpubs.GetStringSelection())
			if wxPlatform == '__WXMSW__':
				self.parent.CurrentDir = win32api.GetShortPathName(self.parent.CurrentDir)
			self.EndModal(wxID_OK)

#--------------------------- PageEditorDialog Class ---------------------------------------

class PageEditorDialog (wxDialog):
	"""
	Content page editing modal dialog window
	"""
	def __init__(self, parent, node, content, dir):
		"""
		"""
		wxDialog.__init__ (self, parent, -1, _("Page Properties"),
						 wxPoint(100,100),
						   wxSize(260,300),
						   wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		# Storage for the attribute name/value pair
		self.node = node
		self.content = content 
		self.parent = parent
		self.dir = dir
		self.filename = ""
		self.updatetoc = False

		self.notebook = wxNotebook(self, -1)
		self.notebook.AddPage(self.GeneralPanel(), _("General"))
		self.notebook.AddPage(self.CreditPanel(), _("Credits"))
		self.notebook.AddPage(self.ClassificationPanel(), _("Categories"))

		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(70, 20 + (height*10)),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.btnCancel = wxButton(self,wxID_CANCEL,_("Cancel"))#,wxPoint(160, 20 + (height*10)),wxSize(76,24))

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(wxNotebookSizer(self.notebook), 1, wxEXPAND | wxALL, 4)
		
	 	self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
	 	self.buttonsizer.Add((1, height), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALL,4)
		self.mysizer.Add(self.buttonsizer, 0, wxALL|wxALIGN_RIGHT, 4)

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		if self.content.filename != "":
			filename = self.content.filename
			self.txtExistingFile.SetValue(filename)

		EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)
		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)	

	def GeneralPanel(self):
		icnFolder = wxBitmap(os.path.join(self.parent.AppDir, "icons", "Open.gif"), wxBITMAP_TYPE_GIF)
	
		mypanel = wxPanel(self.notebook, -1)
		self.lblTitle = wxStaticText(mypanel, -1, _("Name"))
		self.lblDescription = wxStaticText(mypanel, -1, _("Description"))
		self.lblKeywords = wxStaticText(mypanel, -1, _("Keywords"))
		self.lblPublic = wxStaticText(mypanel, -1, _("Public"))
		self.lblContent = wxStaticText(mypanel, -1, _("Page Content:"))

		self.txtTitle = wxTextCtrl(mypanel, -1, self.content.metadata.name)
		self.txtDescription = wxTextCtrl(mypanel, -1, self.content.metadata.description, style=wxTE_MULTILINE)
		self.txtKeywords = wxTextCtrl(mypanel, -1, self.content.metadata.keywords, size=wxSize(160, -1))
		#public_values = [_("true"), _("false")]
		#self.txtPublic = wxChoice(mypanel, -1, wxDefaultPosition, wxSize(160,-1), public_values)
		#if self.content.public == "True":
		#	self.txtPublic.SetSelection(0)
		#else:
		#	self.txtPublic.SetSelection(1)

		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(-1, -1)

		self.btnSelectFile = wxBitmapButton(mypanel, -1, icnFolder, size=wxSize(20, 18))
		self.txtExistingFile = wxTextCtrl(mypanel, -1, "", size=wxSize(160, -1))


   		mysizer = wxBoxSizer(wxVERTICAL)
   		self.gridSizer = wxFlexGridSizer(0, 2, 4, 4)
   		self.gridSizer.Add(self.lblTitle, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtTitle, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblDescription, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtDescription, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblKeywords, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		self.gridSizer.Add(self.txtKeywords, 1, wxEXPAND|wxALL, 4)
   		#self.gridSizer.Add(self.lblPublic, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		#self.gridSizer.Add(self.txtPublic, 1, wxEXPAND|wxALL, 4)
   		#self.gridSizer.Add(self.lblTemplate, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
   		#self.gridSizer.Add(self.cmbTemplate, 1, wxEXPAND|wxALL, 4)
   		self.gridSizer.Add(self.lblContent, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
  
   		self.smallsizer = wxBoxSizer(wxHORIZONTAL)
   		self.smallsizer.Add(self.txtExistingFile, 1, wxEXPAND|wxALL, 4)
   		self.smallsizer.Add(self.btnSelectFile, 0, wxALIGN_CENTER|wxALL, 4)
  
   		self.gridSizer.Add(self.smallsizer, 1, wxEXPAND|wxALL, 4)
   		mysizer.Add(self.gridSizer, 1, wxEXPAND)
		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		return mypanel

	def CreditPanel(self):
		mypanel = wxPanel(self.notebook, -1)
		peopleIcon = wxBitmap(os.path.join(self.parent.AppDir, "icons", "users16.gif"), wxBITMAP_TYPE_GIF)
		self.lblAuthor = wxStaticText(mypanel, -1, _("Author"))
		self.txtAuthor = wxComboBox(mypanel, -1)
		self.btnAuthor = wxBitmapButton(mypanel, -1, peopleIcon, size=wxSize(20, 18))
		
		self.lblDate = wxStaticText(mypanel, -1, _("Creation/Publication Date (Format: YYYY-MM-DD)"))
		self.txtDate = wxTextCtrl(mypanel, -1)

		self.lblOrganization = wxStaticText(mypanel, -1, _("Organization/Publisher"))
		self.txtOrganization = wxComboBox(mypanel, -1)
		self.btnOrganization = wxBitmapButton(mypanel, -1, peopleIcon, size=wxSize(20, 18))

		#self.lblContributors = wxStaticText(mypanel, -1, _("Contributors"))
		#self.lstContributors = wxListCtrl(mypanel, -1, style=wxLC_REPORT)
		#self.lstContributors.InsertColumn(0, _("Role"))
		#self.lstContributors.InsertColumn(1, _("Entity"))
		#self.lstContributors.InsertColumn(2, _("Date"))

		#self.btnAdd = wxButton(mypanel, -1, _("Add"))
		#self.btnEdit = wxButton(mypanel, -1, _("Edit"))
		#self.btnRemove = wxButton(mypanel, -1, _("Remove"))

		self.lblCredit = wxStaticText(mypanel, -1, _("Credits"))
		self.txtCredit = wxTextCtrl(mypanel, -1, self.content.metadata.rights.description, style=wxTE_MULTILINE)

		mysizer = wxBoxSizer(wxVERTICAL)
		mysizer.Add(self.lblAuthor, 0, wxALL, 4)
		authorsizer = wxBoxSizer(wxHORIZONTAL)
		authorsizer.Add(self.txtAuthor, 1, wxEXPAND | wxALL, 4)
		authorsizer.Add(self.btnAuthor, 0, wxALL, 4)
		mysizer.Add(authorsizer, 0, wxEXPAND)

		mysizer.Add(self.lblDate, 0, wxALL, 4)
		mysizer.Add(self.txtDate, 0, wxALL | wxEXPAND, 4)

		mysizer.Add(self.lblOrganization, 0, wxALL, 4)
		orgsizer = wxBoxSizer(wxHORIZONTAL)
		orgsizer.Add(self.txtOrganization, 1, wxEXPAND | wxALL, 4)
		orgsizer.Add(self.btnOrganization, 0, wxALL, 4)
		mysizer.Add(orgsizer, 0, wxEXPAND)

		#mysizer.Add(self.lblContributors, 0, wxALL, 4)
		#mysizer.Add(self.lstContributors, 0, wxEXPAND | wxALL, 4)
		#buttonsizer = wxBoxSizer(wxHORIZONTAL)
		#buttonsizer.Add(self.btnAdd)
		#buttonsizer.Add(self.btnEdit)
		#buttonsizer.Add(self.btnRemove)
		#mysizer.Add(buttonsizer, 0, wxALIGN_CENTRE)
		
		mysizer.Add(self.lblCredit, 0, wxALL, 4)
		mysizer.Add(self.txtCredit, 0, wxALL | wxEXPAND, 4)

		self.UpdateAuthorList()

		EVT_BUTTON(self.btnAuthor, self.btnAuthor.GetId(), self.OnLoadContacts)
		EVT_BUTTON(self.btnOrganization, self.btnOrganization.GetId(), self.OnLoadContacts)
		#EVT_TEXT(self.txtAuthor, self.txtAuthor.GetId(), self.CheckAuthor)
		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		return mypanel

	def ClassificationPanel(self):
		mypanel = wxPanel(self.notebook, -1)
		
		self.lblCategories = wxStaticText(mypanel, -1, _("Categories"))
		self.lstCategories = wxListBox(mypanel, -1)

		self.btnAddCategory = wxButton(mypanel, -1, _("Add"))
		self.btnEditCategory = wxButton(mypanel, -1, _("Edit"))
		self.btnRemoveCategory = wxButton(mypanel, -1, _("Remove"))

		mysizer = wxBoxSizer(wxVERTICAL)
		mysizer.Add(self.lblCategories, 0, wxALL, 4)
		mysizer.Add(self.lstCategories, 0, wxEXPAND | wxALL, 4)
		buttonsizer = wxBoxSizer(wxHORIZONTAL)
		buttonsizer.Add(self.btnAddCategory)
		buttonsizer.Add(self.btnEditCategory)
		buttonsizer.Add(self.btnRemoveCategory)
		mysizer.Add(buttonsizer, 0, wxALIGN_CENTRE)

		for item in self.content.metadata.classification.categories:
			self.lstCategories.Append(item)
		
		EVT_BUTTON(self.btnAddCategory, self.btnAddCategory.GetId(), self.AddCategory)
		EVT_BUTTON(self.btnEditCategory, self.btnEditCategory.GetId(), self.EditCategory)
		EVT_BUTTON(self.btnRemoveCategory, self.btnRemoveCategory.GetId(), self.RemoveCategory)

		mypanel.SetSizer(mysizer)
		mypanel.SetAutoLayout(True)

		return mypanel

	def AddCategory(self, event):
		dialog = wxTextEntryDialog(self, _("Please type the name of the new category here."), _("Add Category"))
		if dialog.ShowModal() == wxID_OK:
			value = dialog.GetValue()
			if value != "":
				self.lstCategories.Append(value)

	def EditCategory(self, event):
		selitem = self.lstCategories.GetSelection()
		if selitem != wxNOT_FOUND:
			dialog = wxTextEntryDialog(self, _("Type the new value for your category here."), _("Edit Category"), self.lstCategories.GetStringSelection())
			if dialog.ShowModal() == wxID_OK:
				value = dialog.GetValue()
				if value != "":
					self.lstCategories.SetString(selitem, value)

	def RemoveCategory(self, event):
		selitem = self.lstCategories.GetSelection()
		if selitem != wxNOT_FOUND:
			self.lstCategories.Delete(selitem)

	def OnLoadContacts(self, event):
		ContactsDialog(self.parent).ShowModal()
		self.UpdateAuthorList()

	def UpdateAuthorList(self):
		oldvalue = self.txtAuthor.GetValue()
		self.txtAuthor.Clear()
		for name in self.parent.vcardlist.keys():
			self.txtAuthor.Append(name, self.parent.vcardlist[name])

		oldorg = self.txtOrganization.GetValue()
		self.txtOrganization.Clear()
		for name in self.parent.vcardlist.keys():
			self.txtOrganization.Append(name, self.parent.vcardlist[name])

		if oldvalue != "":
			self.txtAuthor.SetValue(oldvalue)
		else:
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Author":
					self.txtAuthor.SetValue(person.entity.fname.value)
					if person.date != "":
						self.txtDate.SetValue(person.date)
				elif person.role == "Content Provider":
					self.txtOrganization.SetValue(person.entity.fname.value)

		if oldorg != "":
			self.txtOrganization.SetValue(oldorg)
		else:
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Content Provider":
					self.txtOrganization.SetValue(person.entity.fname.value)

	def CheckAuthor(self, event):
		text = self.txtAuthor.GetValue()
		for name in self.parent.vcardlist.keys():
			if string.find(name, text) == 0:
				self.txtAuthor.SetValue(name)
			self.txtAuthor.SetInsertionPoint(len(text))
			self.txtAuthor.SetSelection(len(text), len(name))

	def btnSelectFileClicked(self, event):
		filtertext = "All Files (*.*)|*.*"
		for plugin in myplugins:
			if filtertext != "":
				filtertext = filtertext + "|"
			textext = ""
			filterext = ""
			for count in range(0, len(plugin["Extension"])):
				textext = textext + "*." + plugin["Extension"][count]
				filterext = filterext + "*." + plugin["Extension"][count]
				if not count == (len(plugin["Extension"]) - 1):
					textext = textext + ", "
					filterext = filterext + "; "
			filtertext = filtertext + plugin["FullName"] + " Files (" + textext + ")|" + filterext
			
		f = wxFileDialog(self, _("Select a file"), os.path.join(self.parent.CurrentDir), "", filtertext, wxOPEN)
		if f.ShowModal() == wxID_OK:
			self.filedir = f.GetDirectory()
			self.filename = f.GetFilename()
			isEClassPluginPage = False
			fileext = os.path.splitext(self.filename)[1][1:]
			page_plugin = None
			for myplugin in myplugins:
				if (fileext in myplugin["Extension"]):
					isEClassPluginPage = True
					page_plugin = myplugins[myplugins.index(myplugin)]
					break

			if isEClassPluginPage and page_plugin:
				overwrite = False 
				if os.path.join(self.parent.CurrentDir, page_plugin["Directory"], self.filename) == os.path.join(self.filedir, self.filename):
					pass
				elif os.path.exists(os.path.join(self.parent.CurrentDir, page_plugin["Directory"], self.filename)):
					msg = wxMessageDialog(self, _("The file %(filename)s already exists. Do you want to overwrite this file?") % {"filename": self.content.filename}, _("Save Project?"), wxYES_NO)
					answer = msg.ShowModal()
					msg.Destroy()
					if answer == wxID_YES:
						overwrite = True
				else:
					overwrite = True
				files.CopyFile(self.filename, self.filedir, os.path.join(self.parent.CurrentDir, page_plugin["Directory"], self.filename))
				self.filename = os.path.join(page_plugin["Directory"], self.filename)
			elif self.filename == "imsmanifest.xml": #another publication
				self.node = conman.ConMan()
				self.node.LoadFromXML(os.path.join(self.filedir, self.filename))
			else:
				files.CopyFile(self.filename, self.filedir, os.path.join(self.parent.CurrentDir, "File"))
				self.filename = os.path.join("File", self.filename)
			
			self.txtExistingFile.SetValue(self.filename)
		f.Destroy()

	def btnOKClicked(self, event):
		public = "True"
		if self.txtTitle.GetValue() == "":
			wxMessageBox(_("Please enter a name for your page."))
			return

		if self.txtExistingFile.GetValue() == "":
			wxMessageBox(_("Please select a file to provide the content for this page."))
			return 

		#if self.txtPublic.GetSelection() == 1:
		#	public = "False"
		#else:
		#	public = "True"

		self.content.public = "True"

		#if self.content.public != public:
		#	self.content.public = public
		#	self.parent.Update()
		self.content.metadata.keywords = self.txtKeywords.GetValue()
		self.content.metadata.description = self.txtDescription.GetValue()
		self.content.metadata.name = self.txtTitle.GetValue()
		self.content.metadata.rights.description = self.txtCredit.GetValue()
		if not self.txtAuthor.GetValue() == "":
			self.UpdateContactInfo(self.txtAuthor.GetValue(), "Author")

		if not self.txtOrganization.GetValue() == "":
			self.UpdateContactInfo(self.txtOrganization.GetValue(), "Content Provider")

		if not self.txtDate.GetValue() == "":
			for person in self.content.metadata.lifecycle.contributors:
				if person.role == "Author":
					person.date = self.txtDate.GetValue()
		else:
			#check if we can remove any empty contact info that might be there
			for person in self.content.metadata.lifecycle.contributors:
				try:
					if person.role == "Author" and self.txtAuthor.GetValue() == "":
						self.content.metadata.lifecycle.contributors.remove(person)
					elif person.role == "Content Provider" and self.txtOrganization.GetValue() == "":
						self.content.metadata.lifecycle.contributors.remove(person)
				except:
					import traceback
					if traceback.print_exc() != None:
						self.parent.log.write(traceback.print_exc())

		
		self.content.metadata.classification.categories = []
		for num in range(0, self.lstCategories.GetCount()):
			self.content.metadata.classification.categories.append(self.lstCategories.GetString(num))

		self.content.filename = self.txtExistingFile.GetValue()
		#self.content.template = self.cmbTemplate.GetStringSelection()
		self.EndModal(wxID_OK)

	def UpdateContactInfo(self, name, role):
		"""
		Updates the contact's information, or adds them to the contact database
		if there's no info on the contact.
		"""
		if role == "":
			role = "Author"
		newcard = None
		if not name in self.parent.vcardlist.keys():
			newcard = vcard.VCard()
			newcard.fname.value = name
			newcard.filename = os.path.join(self.parent.PrefDir, "Contacts", MakeFileName2(name) + ".vcf")
			myfile = open(newcard.filename, "wb")
			myfile.write(newcard.asString())
			myfile.close()
			self.parent.vcardlist[newcard.fname.value] = newcard
		else:
			newcard = self.parent.vcardlist[name]

		hasPerson = False
		for person in self.content.metadata.lifecycle.contributors:
			if person.role == role:
				hasPerson = True
				person.entity = newcard

		if not hasPerson:
			contrib = conman.Contributor()
			contrib.role = role
			contrib.entity = newcard
			self.content.metadata.lifecycle.contributors.append(contrib)

class ContactsDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Contact Manager"), wxPoint(100,100),wxSize(300,300), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.lstContacts = wxListBox(self, -1)

		self.btnAdd = wxButton(self, -1, _("Add"))
		self.btnEdit = wxButton(self, -1, _("Edit"))
		self.btnRemove = wxButton(self, -1, _("Remove"))

		self.btnImport = wxButton(self, -1, _("Import"))
		self.btnClose = wxButton(self, wxID_CANCEL, _("Close"))

		EVT_BUTTON(self.btnAdd, self.btnAdd.GetId(), self.OnAdd)
		EVT_BUTTON(self.btnImport, self.btnImport.GetId(), self.OnImport)
		EVT_BUTTON(self.btnEdit, self.btnEdit.GetId(), self.OnEdit)
		EVT_BUTTON(self.btnRemove, self.btnRemove.GetId(), self.OnRemove)

		mysizer = wxBoxSizer(wxVERTICAL)
		contactsizer = wxBoxSizer(wxHORIZONTAL)
		contactsizer.Add(self.lstContacts, 1, wxEXPAND | wxALL, 4)

		contactBtnSizer = wxBoxSizer(wxVERTICAL)
		contactBtnSizer.Add(self.btnAdd)
		contactBtnSizer.Add(self.btnEdit)
		contactBtnSizer.Add(self.btnRemove)
		contactsizer.Add(contactBtnSizer, 0, wxALL | wxALIGN_CENTRE, 4)

		mysizer.Add(contactsizer, 1, wxEXPAND)

		btnsizer = wxBoxSizer(wxHORIZONTAL)
		btnsizer.Add(self.btnImport, 0, wxALL, 4)
		btnsizer.Add((1,1), 1, wxEXPAND)
		btnsizer.Add(self.btnClose, 0, wxALL, 4)
		
		mysizer.Add(btnsizer, 0, wxEXPAND)

		self.SetSizer(mysizer)
		self.SetAutoLayout(True)

		self.LoadContacts()
		self.Layout()

	def LoadContacts(self):
		self.lstContacts.Clear()
		for name in self.parent.vcardlist.keys():
			if not string.strip(name) == "":
				self.lstContacts.Append(name, self.parent.vcardlist[name])

	def OnAdd(self, event):
		thisvcard = vcard.VCard()
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wxID_OK:
			thisname = editor.vcard.fname.value
			self.parent.vcardlist[thisname] = editor.vcard
			self.lstContacts.Append(thisname, self.parent.vcardlist[thisname])

	def OnImport(self, event):
		dialog = wxFileDialog(self, _("Choose a vCard"), "", "", _("vCard Files") + " (*.vcf)|*.vcf", wxOPEN)
		if dialog.ShowModal() == wxID_OK:
			files.CopyFile(dialog.GetFilename(), dialog.GetDirectory(), os.path.join(self.parent.PrefDir, "Contacts"))
			newvcard = vcard.VCard()
			newvcard.parseFile(os.path.join(self.parent.PrefDir, "Contacts", dialog.GetFilename()))
			if newvcard.fname.value == "":
				myvcard.fname.value = myvcard.name.givenName + " "
				if myvcard.name.middleName != "":
					myvcard.fname.value = myvcard.fname.value + myvcard.name.middleName + " "
				myvcard.fname.value = myvcard.fname.value + myvcard.name.familyName
			self.parent.vcardlist[newvcard.fname.value] = newvcard
			self.lstContacts.Append(name, newvcard)

	def OnEdit(self, event):
		thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
		name = thisvcard.fname.value
		editor = ContactEditor(self, thisvcard)
		if editor.ShowModal() == wxID_OK:
			thisname = editor.vcard.fname.value
			if name != thisname:
				self.parent.vcardlist.pop(name)
			self.parent.vcardlist[thisname] = editor.vcard
			self.lstContacts.SetClientData(self.lstContacts.GetSelection(), editor.vcard)
		editor.Destroy()

	def OnRemove(self, event):
		result = wxMessageDialog(self, _("This action cannot be undone. Would you like to continue?"), _("Remove Contact?"), wxYES_NO).ShowModal()
		if result == wxID_YES:
			thisvcard = self.lstContacts.GetClientData(self.lstContacts.GetSelection())
			try:
				os.remove(thisvcard.filename)
			except:
				wxMessageBox(_("The contact could not be deleted. Please ensure you have the proper permissions to access the EClass.Builder data directory."))
				return

			del self.parent.vcardlist[thisvcard.fname.value]
			self.lstContacts.Delete(self.lstContacts.GetSelection())

class ContactEditor(wxDialog):
	def __init__(self, parent, myvcard):
		wxDialog.__init__ (self, parent, -1, _("Contact Editor"), wxPoint(100,100),wxSize(300,300), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.myvcard = myvcard
		self.parent = parent
		self.lblFullName = wxStaticText(self, -1, _("Full Name"))
		self.txtFullName = wxTextCtrl(self, -1, myvcard.fname.value)
		self.lblFirstName = wxStaticText(self, -1, _("First"))
		self.txtFirstName = wxTextCtrl(self, -1, myvcard.name.givenName)
		self.lblMiddleName = wxStaticText(self, -1, _("Middle"))
		self.txtMiddleName = wxTextCtrl(self, -1, myvcard.name.middleName)
		self.lblLastName = wxStaticText(self, -1, _("Last"))
		self.txtLastName = wxTextCtrl(self, -1, myvcard.name.familyName)
		self.lblPrefix = wxStaticText(self, -1, _("Prefix"))
		self.txtPrefix = wxTextCtrl(self, -1, myvcard.name.prefix, size=wxSize(40, -1))
		self.lblSuffix = wxStaticText(self, -1, _("Suffix"))
		self.txtSuffix = wxTextCtrl(self, -1, myvcard.name.suffix, size=wxSize(40, -1))

		self.lblTitle = wxStaticText(self, -1, _("Title"))
		self.txtTitle = wxTextCtrl(self, -1, myvcard.title.value)

		self.lblOrganization = wxStaticText(self, -1, _("Organization"))
		self.txtOrganization = wxTextCtrl(self, -1, myvcard.organization.name)

		self.lblEmail = wxStaticText(self, -1, _("Email"))
		email = ""
		if len(myvcard.emails) > 0:
			email = myvcard.emails[0].value

		self.txtEmail = wxTextCtrl(self, -1, email)

		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))

		mysizer = wxBoxSizer(wxVERTICAL)
		prefixsizer = wxBoxSizer(wxHORIZONTAL)
		prefixsizer.AddMany([(self.lblFullName, 0, wxALL, 4), (self.txtFullName, 1, wxALL | wxEXPAND, 4)])
		mysizer.Add(prefixsizer)
		propsizer = wxFlexGridSizer(2, 6, 2, 2)
		propsizer.AddMany([
						(self.lblFirstName, 0, wxALL, 4), (self.txtFirstName, 0, wxALL | wxEXPAND, 4),
						(self.lblMiddleName, 0, wxALL, 4), (self.txtMiddleName, 0, wxALL, 4),
						(self.lblLastName, 0, wxALL, 4), (self.txtLastName, 0, wxALL | wxEXPAND, 4),
						(self.lblPrefix, 0, wxALL, 4), (self.txtPrefix, 0, wxALL, 4), 
						(self.lblSuffix, 0, wxALL, 4), (self.txtSuffix, 0, wxALL, 4),((1,1))])
		mysizer.Add(propsizer, 0, wxEXPAND)
		propsizer2 = wxFlexGridSizer(2, 4, 2, 2)
		propsizer2.AddMany([(self.lblTitle, 0, wxALL, 4), (self.txtTitle, 1, wxALL | wxEXPAND, 4), 
						(self.lblOrganization, 0, wxALL, 4), (self.txtOrganization, 1, wxALL | wxEXPAND, 4),
						(self.lblEmail, 0, wxALL, 4), (self.txtEmail, 1, wxALL | wxEXPAND, 4)])
		mysizer.Add(propsizer2, 0, wxEXPAND)
		
		btnsizer = wxBoxSizer(wxHORIZONTAL)
		btnsizer.Add((1,1), 1, wxEXPAND)
		if wxPlatform != "__WXMAC__":
			btnsizer.Add(self.btnOK)
			btnsizer.Add(self.btnCancel)
		else:
			btnsizer.Add(self.btnCancel)
			btnsizer.Add(self.btnOK)
		mysizer.Add(btnsizer, 0, wxEXPAND | wxALL, 4)

		self.SetSizerAndFit(mysizer)
		self.SetAutoLayout(True)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOK)

	def OnOK(self, event):
		if self.txtFullName.GetValue() == "":
			wxMessageBox(_("You must enter a full name for this contact."))

		self.myvcard.fname.value = self.txtFullName.GetValue()
		self.myvcard.name.prefix = self.txtPrefix.GetValue()
		self.myvcard.name.suffix = self.txtSuffix.GetValue()
		self.myvcard.name.familyName = self.txtLastName.GetValue()
		self.myvcard.name.middleName = self.txtMiddleName.GetValue()
		self.myvcard.name.givenName = self.txtFirstName.GetValue()
		self.myvcard.title.value = self.txtTitle.GetValue()
		self.myvcard.organization.name = self.txtOrganization.GetValue()
		if len(self.myvcard.emails) == 0: 
			self.myvcard.emails.append(vcard.Email())
		self.myvcard.emails[0].value = self.txtEmail.GetValue()
		if self.myvcard.filename == "":
			prefdir = self.parent.parent.PrefDir
			thisfilename = os.path.join(prefdir, "Contacts", MakeFileName2(self.myvcard.fname.value) + ".vcf")
			if os.path.exists(thisfilename):
				result = wxMessageDialog(self, _("A contact with this name already exists. Overwrite existing contact file?"), _("Overwrite contact?"), wxYES_NO).ShowModal()
				if result == wxID_YES: 
					self.myvcard.filename = thisfilename
				else:
					return 
			else:
				self.myvcard.filename = thisfilename

		myfile = open(self.myvcard.filename, "wb")
		myfile.write(self.myvcard.asString())
		myfile.close()

		self.vcard = self.myvcard
		self.EndModal(wxID_OK)

class EClassAboutDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("About EClass.Builder"), wxPoint(100,100),wxSize(460,400), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		
		if wxPlatform == '__WXMSW__':
			self.browser = wxIEHtmlWin(self, -1, wxDefaultPosition, wxSize(456,300), style = wxNO_FULL_REPAINT_ON_RESIZE)
			self.browser.Navigate(os.path.join(parent.AppDir,"about",parent.langdir, "about_eclass.html"))
		else:
			self.browser = wxHtmlWindow(self, -1, wxDefaultPosition, wxSize(456,300))
			self.browser.LoadPage(os.path.join(parent.AppDir,"about", parent.langdir, "about_eclass.html"))
		
		self.btnOK = wxButton(self,wxID_OK,_("OK"))#,wxPoint(200, 340),wxSize(76, 24))
		self.btnOK.SetDefault()
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.browser, 1, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.btnOK, 0, wxALIGN_CENTER|wxALL, 6)			

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)	

	def btnOKClicked(self, event):
		self.EndModal(wxID_OK)

class StartupDialog(wxDialog):
	def __init__(self, parent):
		point = parent.GetPositionTuple()
		size = parent.GetSizeTuple()
		wxDialog.__init__ (self, parent, -1, _("Welcome to EClass.Builder"),wxDefaultPosition, wxSize(460,160), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		buttonstart = 90
		fontsize = 22
		if wxPlatform == "__WXMAC__":
			buttonstart = 50
			height = 25
			fontsize = 28
		self.parent = parent
		myfont = wxFont(fontsize, wxMODERN, wxNORMAL, wxBOLD, False, "Arial")
		self.lblWelcome = wxStaticText(self, -1, _("Welcome to EClass.Builder"))
		self.lblWelcome.SetFont(myfont)
		self.lblWelcome.SetForegroundColour(wxNamedColour("blue"))

		self.lblVersion = wxStaticText(self, -1, "Version " + self.parent.version)

		self.chkShowThisDialog = wxCheckBox(self, -1, _("Don't show this dialog on startup."))
		self.btnNew = wxButton(self, -1, _("New Project"))
		self.btnOpen = wxButton(self, -1, _("Open Project"))
		self.btnOpen.SetDefault()
		self.btnTutorial = wxButton(self, -1, _("View Tutorial"))

		self.dialogsizer = wxBoxSizer(wxVERTICAL)
		self.dialogsizer.Add(self.lblWelcome, 0, wxALL|wxALIGN_CENTER, 4)	
		self.dialogsizer.Add(self.lblVersion, 0, wxALL|wxALIGN_CENTER, 4)	
		self.dialogsizer.Add(self.chkShowThisDialog, 0, wxALL|wxALIGN_CENTER, 10)
		self.boxsizer = wxBoxSizer(wxHORIZONTAL)
		self.boxsizer.Add(self.btnNew, 0, wxALL | wxALIGN_CENTER, 10)
		self.boxsizer.Add(self.btnOpen, 0, wxALL | wxALIGN_CENTER, 10)
		self.boxsizer.Add(self.btnTutorial, 0, wxALL | wxALIGN_CENTER, 10)
		self.dialogsizer.Add(self.boxsizer, 1, wxALIGN_CENTER)
		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.dialogsizer)
		self.Layout()
		self.CentreOnParent(wxBOTH)

		EVT_BUTTON(self, self.btnNew.GetId(), self.OnNew)
		EVT_BUTTON(self, self.btnOpen.GetId(), self.OnOpen)
		EVT_BUTTON(self, self.btnTutorial.GetId(), self.OnTutorial)
		EVT_CHECKBOX(self, self.chkShowThisDialog.GetId(), self.OnCheck)

		#EVT_PAINT(self, self.OnPaint)

	def OnNew(self, event):
		self.EndModal(0)
		#self.parent.NewProject(None)

	def OnOpen(self, event):
		self.EndModal(1)
		#self.parent.OnOpen(None)

	def OnTutorial(self, event):
		self.EndModal(2)
		#self.parent.OnHelp(None)

	def OnCheck(self, event):
		if event.Checked():
			self.parent.settings["ShowStartup"] = "False"
		else:
			self.parent.settings["ShowStartup"] = "True"

	#def OnPaint(self, event):
	#	dc = wxPaintDC(self)
	#	if wxPlatform == "__WXMAC__":
	#		welcomesize = "28"
	#		versionsize = "12"
	#		welcomestart = 40
	#		versionstart = 180
	#	else:
	#		welcomesize = "22"
	#		versionsize = "10"
	#		welcomestart = 40
	#		versionstart = 160
	#	welcometext = "<font family='swiss' size='" + welcomesize + "' weight='bold' color='blue'>Welcome to EClass.Builder</font>"
	#	versiontext = "<font family='swiss' size='" + versionsize + "'>Version " + self.parent.version + "</font>"
	#	fancytext.renderToDC(welcometext, dc, welcomestart, 10)
	#	fancytext.renderToDC(versiontext, dc, versionstart, 50)

class LinkChecker(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, "Link Checker",wxDefaultPosition, wxSize(600, 440), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.linkList = wxListCtrl(self, -1, size=(600,400), style=wxLC_REPORT)
		self.linkList.InsertColumn(0, "Link", width=300)
		self.linkList.InsertColumn(1, "Page", width=200)
		self.linkList.InsertColumn(2, "Status")

		self.btnOK = wxButton(self, wxID_OK, "Check")
		self.btnCancel = wxButton(self, wxID_CANCEL, "Cancel")

		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.linkList, 1, wxEXPAND | wxALL, 4)
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		self.buttonsizer.Add((1, 1), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		self.buttonsizer.Add(self.btnCancel, 0, wxALL,4)
		self.mysizer.Add(self.buttonsizer, 0, wxALL|wxALIGN_RIGHT, 4)
		self.links = []
		self.itemCount = 0
		self.isChecking = False
		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.mysizer)
		self.Layout()
		self.currentFile = ""

		EVT_BUTTON(self, wxID_OK, self.OnCheck)
		EVT_BUTTON(self, wxID_CANCEL, self.OnCancel)

	def OnCheck(self, event):
		self.btnOK.Enable(False)
		self.isChecking = True
		self.CheckLinks()
		self.btnOK.Enable(True)
		self.isChecking = False

	def OnCancel(self, event):
		self.isChecking = False
		self.EndModal(wxID_CANCEL)

	def CheckLinks(self):
		files = os.listdir(os.path.join(self.parent.CurrentDir, "pub"))
		for file in files:
			if not self.isChecking:
				return
			self.currentFile = file
			filename = os.path.join(self.parent.CurrentDir, "pub", file)
			if os.path.isfile(filename):
				if string.find(os.path.splitext(file)[1], "htm") != -1: 
					myhtml = open(filename, "r").read()
					imagelinks = re.compile("src\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
					imagelinks.sub(self.CheckLink,myhtml)
					weblinks = re.compile("href\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
					weblinks.sub(self.CheckLink, myhtml)

	def CheckLink(self, match):
		link = match.group(1)
		if string.find(string.lower(link), "http://") == 0 or string.find(string.lower(link), "ftp://") == 0:
			if link in self.links:
				return
			else:
				self.links.append(link)
			#add the link to the list and check the status
			self.linkList.InsertStringItem(self.itemCount, link)
			self.linkList.SetStringItem(self.itemCount, 1, "/pub/" + self.currentFile)
			self.linkList.SetStringItem(self.itemCount, 2, "Connecting...")
			import threading
			self.mythread = threading.Thread(None, self.ConnectToLink, args=(self.itemCount, link))
			self.mythread.start()
			self.itemCount = self.itemCount + 1

	def ConnectToLink(self, item, link):
			import urllib2
			if not self.isChecking:
				return
			try:
				urllib2.urlopen(link)
				self.linkList.SetStringItem(item, 2, "OK")
			except:
				self.linkList.SetStringItem(item, 2, "Broken")

class ThemeManager(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Theme Manager"),wxDefaultPosition, wxSize(760, 540), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.lblThemeList = wxStaticText(self, -1, _("Installed Themes"))
		#themelist = []
		#for theme in self.parent.themes:
		#	if theme[2].isPublic:
		#		themelist.append(theme[0])

		self.lstThemeList = wxListBox(self, -1, choices=self.parent.themes.GetPublicThemeNames())
		self.lstThemeList.SetSelection(0)
		self.AppDir = parent.AppDir
		self.CurrentDir = os.path.join(self.parent.AppDir, "themes", "ThemePreview")
		if wxPlatform == "__WXMSW__":
			self.CurrentDir = win32api.GetShortPathName(self.CurrentDir)
		#self.templates = parent.templates
		self.lblPreview = wxStaticText(self, -1, _("Theme Preview"))
		self.pub = conman.ConMan()
		self.pub.LoadFromXML(os.path.join(self.CurrentDir, "imsmanifest.xml"))
		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.oldtheme = self.parent.pub.settings["Theme"]
		
		#self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))
		import wxbrowser
		self.browser = wxbrowser.wxBrowser(self, -1)
		#self.browser.LoadPage("http://www.apple.com")

		icnNewTheme = wxBitmap(os.path.join(self.parent.AppDir, "icons", "plus16.gif"), wxBITMAP_TYPE_GIF)
		icnCopyTheme = wxBitmap(os.path.join(self.parent.AppDir, "icons", "copy16.gif"), wxBITMAP_TYPE_GIF)
		icnDeleteTheme = wxBitmap(os.path.join(self.parent.AppDir, "icons", "minus16.gif"), wxBITMAP_TYPE_GIF)

		self.btnNewTheme = wxBitmapButton(self, -1, icnNewTheme)
		self.btnCopyTheme = wxBitmapButton(self, -1, icnCopyTheme)
		self.btnDeleteTheme = wxBitmapButton(self, -1, icnDeleteTheme)

		self.btnSetTheme = wxButton(self, -1, _("Use this theme"))
		self.btnExportTheme = wxButton(self, -1, _("Export theme"))
		self.btnImportTheme = wxButton(self, -1, _("Import theme"))
		#self.btnEditTheme = wxButton(self, -1, "Edit Theme")

		themesizer = wxBoxSizer(wxHORIZONTAL)
		themesizer.AddMany([(self.btnNewTheme, 0, wxALL | wxALIGN_CENTER, 5), #(self.btnEditTheme, 0, wxALL | wxALIGN_CENTER, 5), 
				  (self.btnCopyTheme, 0, wxALL | wxALIGN_CENTER, 5), (self.btnDeleteTheme, 0, wxALL | wxALIGN_CENTER, 5)])

		self.sizer = wxBoxSizer(wxVERTICAL)
		mainsizer = wxFlexGridSizer(2, 2, 4, 4)
		mainsizer.AddMany([(self.lblThemeList, 0, wxALL, 4), (self.lblPreview, 0, wxALL, 4), (self.lstThemeList, 1, wxEXPAND | wxALL, 4), (self.browser.browser, 1, wxEXPAND | wxALL, 4)])
		mainsizer.Add(themesizer, 0, wxALL | wxALIGN_CENTER, 4)
		#mainsizer.Add(self.btnOK, 0, wxALL | wxALIGN_RIGHT, 4)
		mainsizer.AddGrowableCol(1)
		mainsizer.AddGrowableRow(1)
		
		self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		#self.buttonsizer.Add(themesizer, 0, wxALL | wxALIGN_LEFT, 4)
		self.buttonsizer.Add(self.btnSetTheme, 0, wxALL | wxALIGN_CENTER, 4)
		self.buttonsizer.Add(self.btnExportTheme, 0, wxALL | wxALIGN_CENTER, 4)
		self.buttonsizer.Add(self.btnImportTheme, 0, wxALL | wxALIGN_CENTER, 4)
		#self.buttonsizer.Add(self.btnEditTheme, 0, wxALL | wxALIGN_CENTER, 4)
		self.buttonsizer.Add((1, 1), 1, wxEXPAND)
		self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		#self.buttonsizer.Add(self.btnCancel, 0, wxALL,4)
		mainsizer.Add(self.buttonsizer, 1, wxALL | wxEXPAND, 4)
		self.sizer.Add(mainsizer, 1, wxEXPAND | wxALL, 4)
		self.SetAutoLayout(True)
		self.SetSizer(self.sizer)
		#if self.parent.pub.settings["Theme"] != "":
		#	for theme in themelist:
		#		if theme[0] == self.parent.pub.settings["Theme"]:
		#			self.lstThemeList.SetStringSelection(self.parent.pub.settings["Theme"])
		#else:
		
		if self.parent.currentTheme and self.parent.currentTheme.themename in self.parent.themes.GetPublicThemeNames():
			self.lstThemeList.SetStringSelection(self.parent.currentTheme.themename)
		else:
			self.lstThemeList.SetStringSelection("Default (frames)")

		self.OnThemeChanged(None)
		self.Layout()

		EVT_BUTTON(self, self.btnNewTheme.GetId(), self.OnNewTheme)
		EVT_BUTTON(self, self.btnCopyTheme.GetId(), self.OnCopyTheme)
		EVT_BUTTON(self, self.btnDeleteTheme.GetId(), self.OnDeleteTheme)
		EVT_BUTTON(self, self.btnSetTheme.GetId(), self.OnSetTheme)
		EVT_BUTTON(self, self.btnExportTheme.GetId(), self.ExportTheme)
		EVT_BUTTON(self, self.btnImportTheme.GetId(), self.ImportTheme)
		EVT_LISTBOX(self, self.lstThemeList.GetId(), self.OnThemeChanged)

	def OnThemeChanged(self, event):
		themename = self.lstThemeList.GetStringSelection()
		#mythememodule = self.parent.themes[0]
		#for theme in self.parent.themes:
		#	if theme[0] == themename:
		#		mythememodule = theme
		#exec("mytheme = themes." + mythememodule[1])
		self.currentTheme = self.parent.themes.FindTheme(themename)
		publisher = self.currentTheme.HTMLPublisher(self)
		result = publisher.Publish()
		if result:
			self.browser.LoadPage(os.path.join(self.CurrentDir, "index.htm"))

	def OnSetTheme(self, event):
		self.UpdateTheme()

	def ReloadThemes(self):
		self.parent.themes.LoadThemes()
		self.lstThemeList.Clear()
		for theme in self.parent.themes.GetPublicThemeNames():
			self.lstThemeList.Append(theme)

	def UpdateTheme(self):
		mythememodule = ""
		mytheme = self.lstThemeList.GetStringSelection()
		if not mytheme == "":
			theme = self.parent.themes.FindTheme(mytheme)
			self.parent.currentTheme = theme
			self.parent.pub.settings["Theme"] = mytheme
		else:
			self.parent.currentTheme = self.parent.themes.FindTheme("Default (frames)")
			
		#exec("mytheme = themes." + mythememodule)

		publisher = self.parent.currentTheme.HTMLPublisher(self.parent)
		result = publisher.Publish()
		self.parent.Preview()
		self.updateTheme = False

	def OnNewTheme(self, event):
		dialog = wxTextEntryDialog(self, _("Please type a name for your new theme"), _("New Theme"), _("New Theme"))
		if dialog.ShowModal() == wxID_OK:
			themedir = os.path.join(self.parent.AppDir, "themes")
			filename = string.replace(MakeFileName2(dialog.GetValue()) + ".py", " ", "_")
			foldername = MakeFolder(dialog.GetValue())
			try:
				os.mkdir(os.path.join(themedir, foldername))
			except:
				wxMessageBox(_("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(self.parent.AppDir, "themes")})
				return 
			myfile = open(os.path.join(themedir, filename), "w")
			data = """
from BaseTheme import *
themename = "%s"

class HTMLPublisher(BaseHTMLPublisher):
	def __init__(self, parent):
		BaseHTMLPublisher.__init__(self, parent)
		self.themedir = os.path.join(self.appdir, "themes", themename)
""" % (string.replace(dialog.GetValue(), "\"", "\\\""))
			myfile.write(data)
			myfile.close()

			#copy support files from Default (no frames)
			files.CopyFiles(os.path.join(themedir, "Default (no frames)"), os.path.join(themedir, foldername), 1)
			#self.lstThemeList.Append(dialog.GetValue())
			self.parent.themes.LoadThemes()
			self.ReloadThemes()
			#modulename = string.replace(filename, ".py", "")
			#exec("import themes." + modulename)
			#self.parent.themes.append([dialog.GetValue(), modulename])
		dialog.Destroy()

	def OnDeleteTheme(self, event):
		filename = string.replace(MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
		modulename = string.replace(filename, ".py", "")
		if self.parent.currentTheme == [self.lstThemeList.GetStringSelection(), modulename]:
			wxMessageBox(_("Cannot delete theme because it is currently in use for this EClass. To delete this theme, please change your EClass theme."))
			return 
		dialog = wxMessageDialog(self, _("Are you sure you want to delete the theme '%(theme)s'? This action cannot be undone.") % {"theme":self.lstThemeList.GetStringSelection()}, _("Confirm Delete"), wxYES_NO)
		if dialog.ShowModal() == wxID_YES:
			themedir = os.path.join(self.parent.AppDir, "themes")
			themefile = os.path.join(themedir, filename)
			if os.path.exists(themefile):
				os.remove(themefile)
			if os.path.exists(themefile + "c"):
				os.remove(themefile + "c")
			foldername = os.path.join(themedir, self.lstThemeList.GetStringSelection())
			if os.path.exists(foldername):
				files.DeleteFolder(foldername)
			
			self.parent.themes.LoadThemes()
			self.ReloadThemes()

			#self.parent.themes.remove([self.lstThemeList.GetStringSelection(), modulename])
			#self.lstThemeList.Delete(self.lstThemeList.GetSelection())

		dialog.Destroy()

	def OnCopyTheme(self, event):
		dialog = wxTextEntryDialog(self, _("Please type a name for your new theme"), _("New Theme"), "")
		if dialog.ShowModal() == wxID_OK:  
			themedir = os.path.join(self.parent.AppDir, "themes")
			filename = string.replace(MakeFileName2(dialog.GetValue()) + ".py", " ", "_")
			otherfilename = string.replace(MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
			otherfilename = string.replace(otherfilename, "(", "")
			otherfilename = string.replace(otherfilename, ")", "")
			foldername = MakeFolder(dialog.GetValue())
			try:
				os.mkdir(os.path.join(themedir, foldername))
			except:
				wxMessageBox(_("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(self.parent.AppDir, "themes")})
				return 

			copyfile = open(os.path.join(themedir, otherfilename), "r")
			data = copyfile.read()
			copyfile.close()

			oldthemeline = 'themename = "%s"' % (string.replace(self.lstThemeList.GetStringSelection(), "\"", "\\\""))
			newthemeline = 'themename = "%s"' % (string.replace(dialog.GetValue(), "\"", "\\\""))
			data = string.replace(data, oldthemeline, newthemeline) 
			myfile = open(os.path.join(themedir, filename), "w")
			myfile.write(data)
			myfile.close()

			#copy support files from Default (no frames)
			files.CopyFiles(os.path.join(themedir, self.lstThemeList.GetStringSelection()), os.path.join(themedir, foldername), 1)
			self.parent.themes.LoadThemes()
			self.ReloadThemes()
			#self.lstThemeList.Append(dialog.GetValue())
			#modulename = string.replace(filename, ".py", "")
			#exec("import themes." + modulename)
			#self.parent.themes.append([dialog.GetValue(), modulename])
		dialog.Destroy()

	def ExportTheme(self, event=None):
		import zipfile
		themename = MakeFileName2(self.lstThemeList.GetStringSelection())
		dialog = wxFileDialog(self, _("Export Theme File"), "", themename + ".theme", _("Theme Files") + " (*.theme)|*.theme", wxSAVE|wxOVERWRITE_PROMPT) 
		if dialog.ShowModal() == wxID_OK:
			filename = dialog.GetPath()
			themezip = zipfile.ZipFile(filename, "w")
			themepyfile = string.replace(themename + ".py", " ", "_")
			themezip.write(os.path.join(self.parent.AppDir, "themes", themepyfile), themepyfile)
			themefolder = MakeFolder(self.lstThemeList.GetStringSelection())
			self.AddDirToZip(themefolder, themezip)
			themezip.close()
			wxMessageBox(_("Theme successfully exported."))
		dialog.Destroy()

	def AddDirToZip(self, dir, zip):
		for item in os.listdir(os.path.join(self.AppDir, "themes", dir)):
			if os.path.isfile(os.path.join(self.AppDir, "themes", dir, item)):
				zip.write(os.path.join(self.AppDir, "themes", dir, item), os.path.join(dir, item))
			elif os.path.isdir(os.path.join(self.AppDir, "themes", dir, item)):
				self.AddDirToZip(os.path.join(dir, item), zip)

	def ImportTheme(self, event=None):
		import zipfile
		dialog = wxFileDialog(self, _("Select Theme to Import"), "", "", _("Theme Files") + " (*.theme)|*.theme", wxOPEN) 
		if dialog.ShowModal() == wxID_OK:
			filename = dialog.GetPath()
			themezip = zipfile.ZipFile(filename, "r")
			files = themezip.infolist()
			for file in files:
				data = themezip.read(file.filename)
				if not os.path.exists(os.path.join(self.AppDir, "themes", os.path.dirname(file.filename))):
					os.mkdir(os.path.join(self.AppDir, "themes", os.path.dirname(file.filename)))

				file = open(os.path.join(self.AppDir, "themes", file.filename), "wb")
				file.write(data)
				file.close()
				self.ReloadThemes()
			wxMessageBox(_("Theme imported successfully."))

	def CreateDirs(self, filelist):
		pass

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
				import traceback
				print traceback.print_exc()
				#if not newtreeitem == None:
				#	self.wxTree.Delete(newtreeitem)
				#if not newitem == None and not previtem == None:
				#	previtem.parent.children.remove(newitem)

				message = "There was an error while moving the page. Please contact your systems administrator or send email to kevino@tulane.edu if this error continues to occur."
				print message
				dialog = wxMessageDialog(self.parent, message, "Error moving page", wxOK)
				dialog.ShowModal()
				dialog.Destroy()
				#self.wxTree.InsertItem(olditemparent, olditemsibling, self.wxTree.GetItemText(oldtreeitem), -1, -1, wxTreeItemData(olditem))
				#olditem
		#print text
		return wxDragCopy


def MakeFolder(mytext):
	mytext = string.replace(mytext, "\\", "")
	mytext = string.replace(mytext, "/", "")
	mytext = string.replace(mytext, ":", "")
	mytext = string.replace(mytext, "*", "")
	mytext = string.replace(mytext, "?", "")
	mytext = string.replace(mytext, "\"", "")
	mytext = string.replace(mytext, "<", "")
	mytext = string.replace(mytext, ">", "")
	mytext = string.replace(mytext, "|", "")
	mytext = mytext 
	return mytext

#------------------------------- MyApp Class ----------------------------------------
class MyApp(wxApp):
	def OnInit(self):
		self.frame = MainFrame2(None, -1, "EClass.Builder")
		self.frame.Show(True)
		self.SetTopWindow(self.frame)
		return True

for arg in sys.argv:
	print arg
	if arg == "--autostart-pyuno":
		import re
		myfilename = ""
		if os.name == "nt":
			myfilename = "C:\\Program Files\\OpenOffice.org1.1beta\\share\\registry\\data\\org\\openoffice\\Setup.xcu"
		try:
			print "Registering Pyuno... Location is: " + myfilename
			file = open(myfilename, "r")
			data = file.read()
			file.close()
			file = open(myfilename + ".bak", "w")
			file.write(data)
			file.close()
			if string.find(data, "<prop oor:name=\"ooSetupConnectionURL\">") == -1:
				if string.find(data, "<node oor:name=\"Office\">") > -1:
					myterm = re.compile("(<node oor:name=\"Office\">)", re.IGNORECASE|re.DOTALL)
					data = myterm.sub("\\1\n<prop oor:name=\"ooSetupConnectionURL\"><value>socket,host=localhost,port=2002;urp;</value></prop>\n", data)
				else:
					data = data + """
					<node oor:name="Office">
						<prop oor:name="ooSetupConnectionURL">socket,host=localhost,port=2002;urp;</prop>
					</node>
					"""
				file = open(myfilename, "w")
				file.write(data)
				file.close()
		except:
			print "Sorry, cannot register OpenOffice."
		exit(0)
	if arg == "--debug":
		debug = 1

app = MyApp(0)
app.MainLoop()
