from wxPython.wx import *
import string, sys, os
import conman
import fileutils
import utils

class ThemeManager(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Theme Manager"),wxDefaultPosition, wxSize(760, 540), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.lblThemeList = wxStaticText(self, -1, _("Installed Themes"))

		self.lstThemeList = wxListBox(self, -1, choices=self.parent.themes.GetPublicThemeNames())
		self.lstThemeList.SetSelection(0)
		self.AppDir = parent.AppDir
		self.CurrentDir = os.path.join(self.parent.AppDir, "themes", "ThemePreview")
		#if wxPlatform == "__WXMSW__":
		#	self.CurrentDir = win32api.GetShortPathName(self.CurrentDir)
		#self.templates = parent.templates
		self.lblPreview = wxStaticText(self, -1, _("Theme Preview"))
		self.pub = conman.ConMan()
		self.pub.LoadFromXML(os.path.join(self.CurrentDir, "imsmanifest.xml"))
		self.btnOK = wxButton(self, wxID_OK, _("OK"))
		self.oldtheme = self.parent.pub.settings["Theme"]
		
		import wxbrowser
		self.browser = wxbrowser.wxBrowser(self, -1)

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
			filename = string.replace(fileutils.MakeFileName2(dialog.GetValue()) + ".py", "-", "_")
			foldername = utils.createSafeFilename(dialog.GetValue())
			try:
				os.mkdir(os.path.join(themedir, foldername))
			except:
				message = _("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(self.parent.AppDir, "themes")}
				self.parent.log.write(message)
				wxMessageBox(message)
				return 
			myfile = utils.openFile(os.path.join(themedir, filename), "w")


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
			fileutils.CopyFiles(os.path.join(themedir, "Default (no frames)"), os.path.join(themedir, foldername), 1)
			#self.lstThemeList.Append(dialog.GetValue())
			self.parent.themes.LoadThemes()
			self.ReloadThemes()
			#modulename = string.replace(filename, ".py", "")
			#exec("import themes." + modulename)
			#self.parent.themes.append([dialog.GetValue(), modulename])
		dialog.Destroy()

	def OnDeleteTheme(self, event):
		filename = string.replace(fileutils.MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
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
				fileutils.DeleteFolder(foldername)
			
			self.parent.themes.LoadThemes()
			self.ReloadThemes()

			#self.parent.themes.remove([self.lstThemeList.GetStringSelection(), modulename])
			#self.lstThemeList.Delete(self.lstThemeList.GetSelection())

		dialog.Destroy()

	def OnCopyTheme(self, event):
		dialog = wxTextEntryDialog(self, _("Please type a name for your new theme"), _("New Theme"), "")
		if dialog.ShowModal() == wxID_OK:  
			themedir = os.path.join(self.parent.AppDir, "themes")
			filename = string.replace(fileutils.MakeFileName2(dialog.GetValue()) + ".py", " ", "_")
			otherfilename = string.replace(fileutils.MakeFileName2(self.lstThemeList.GetStringSelection()) + ".py", " ", "_")
			otherfilename = string.replace(otherfilename, "(", "")
			otherfilename = string.replace(otherfilename, ")", "")
			foldername = utils.createSafeFilename(dialog.GetValue())
			try:
				os.mkdir(os.path.join(themedir, foldername))
			except:
				message = _("Cannot create theme. Check that a theme with this name does not already exist, and that you have write access to the '%(themedir)s' directory.") % {"themedir":os.path.join(self.parent.AppDir, "themes")}
				self.parent.log.write(message)
				wxMessageBox(message)
				return 

			copyfile = utils.openFile(os.path.join(themedir, otherfilename), "r")
			data = copyfile.read()
			copyfile.close()

			oldthemeline = 'themename = "%s"' % (string.replace(self.lstThemeList.GetStringSelection(), "\"", "\\\""))
			newthemeline = 'themename = "%s"' % (string.replace(dialog.GetValue(), "\"", "\\\""))
			data = string.replace(data, oldthemeline, newthemeline) 
			myfile = utils.openFile(os.path.join(themedir, filename), "w")
			myfile.write(data)
			myfile.close()

			#copy support files from Default (no frames)
			fileutils.CopyFiles(os.path.join(themedir, self.lstThemeList.GetStringSelection()), os.path.join(themedir, foldername), 1)
			self.parent.themes.LoadThemes()
			self.ReloadThemes()
			#self.lstThemeList.Append(dialog.GetValue())
			#modulename = string.replace(filename, ".py", "")
			#exec("import themes." + modulename)
			#self.parent.themes.append([dialog.GetValue(), modulename])
		dialog.Destroy()

	def ExportTheme(self, event=None):
		import zipfile
		themename = fileutils.MakeFileName2(self.lstThemeList.GetStringSelection())
		dialog = wxFileDialog(self, _("Export Theme File"), "", themename + ".theme", _("Theme Files") + " (*.theme)|*.theme", wxSAVE|wxOVERWRITE_PROMPT) 
		if dialog.ShowModal() == wxID_OK:
			filename = dialog.GetPath()
			themezip = zipfile.ZipFile(filename, "w")
			themepyfile = string.replace(themename + ".py", " ", "_")
			themezip.write(os.path.join(self.parent.AppDir, "themes", themepyfile), themepyfile)
			themefolder = utils.createSafeFilename(self.lstThemeList.GetStringSelection())
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

				file = utils.openFile(os.path.join(self.AppDir, "themes", file.filename), "wb")
				file.write(data)
				file.close()
				self.ReloadThemes()
			wxMessageBox(_("Theme imported successfully."))

	def CreateDirs(self, filelist):
		pass