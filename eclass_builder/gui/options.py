import string, sys, os
from wxPython.wx import *
import plugins
import utils

class PreferencesEditor(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Options"), wxPoint(100,100),wxSize(300,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
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
		for plugin in plugins.pluginList:
			if plugin.plugin_info["CanCreateNew"]:
				self.pluginnames.append(plugin.plugin_info["FullName"])
		self.cmbDefaultPlugin = wxChoice(self, -1, wxDefaultPosition, wxDefaultSize, self.pluginnames)
		if parent.settings["DefaultPlugin"] != "":
			self.cmbDefaultPlugin.SetStringSelection(parent.settings["DefaultPlugin"])

		self.converters = {"Microsoft Office":"ms_office", "OpenOffice": "open_office", "Command Line Tools": "command_line"}

		self.lblConverter = wxStaticText(self, -1, _("Document Converter"))
		self.cmbConverter = wxChoice(self, -1, choices=self.converters.keys())
		defaultConv = ""
		if parent.settings["PreferredConverter"] != "":
			for item in self.converters.items():
				print `item`
				if item[1] == parent.settings["PreferredConverter"]:
					defaultConv = item[0]

		if defaultConv != "":
			self.cmbConverter.SetStringSelection(defaultConv)

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
		self.gridsizer.Add(self.lblConverter, 0, wxALIGN_RIGHT|wxALIGN_CENTER_VERTICAL|wxALL, 4)
		self.gridsizer.Add(self.cmbConverter, 1, wxALIGN_RIGHT|wxEXPAND|wxALL, 2)
		self.gridsizer.Add((1, 1), 1, wxALL, 4)
		#self.gridsizer.Add(self.chkAutoName, 1, wxALIGN_RIGHT|wxALL, 2)
		#self.gridsizer.Add((1, 1), 1, wxALL, 4)
		self.mysizer.Add(self.gridsizer, 1, wxEXPAND)
		
		#create the button sizer
		self.buttonSizer = wxStdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
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
		self.parent.settings["PreferredConverter"] = self.converters[self.cmbConverter.GetStringSelection()]
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
			file = utils.openFile(myfilename, "r")
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
			file = utils.openFile(myfilename, "r")
			data = file.read()
			file.close()
			file = utils.openFile(myfilename + ".bak", "w")
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
				file = utils.openFile(myfilename, "w")
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