import string, sys, os
from wxPython.wx import *

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
		self.notebook.AddPage(panel, _("FTP"))
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

		self.buttonSizer = wxStdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
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
		self.txtdescription = wxTextCtrl(panel, -1, self.parent.pub.description, wxPoint(self.textx, self.height + 10), wxSize(-1, 160), wxTE_MULTILINE) 
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

		icnFolder = wxBitmap(os.path.join(self.parent.AppDir, "icons", "Open.gif"), wxBITMAP_TYPE_GIF)

		self.lblCDDir = wxStaticText(panel, -1, _("Directory to save CD files."))
		self.btnSelectFile = wxBitmapButton(panel, -1, icnFolder, size=wxSize(20, 18))
		self.txtCDDir = wxTextCtrl(panel, -1, "", size=wxSize(160, -1))		

		#self.serverOptions = [_("EClass Web Server (Karrigell)"), _("Documancer")]
		#self.radboxServer = wxRadioBox(panel, -1, _("Specify EClass Viewer Software"), wxDefaultPosition, wxDefaultSize, self.serverOptions)
		
		self.pubSizer = wxBoxSizer(wxVERTICAL)
		self.pubSizer.Add(self.chkFilename, 0, wxALL, 4)
		#self.pubSizer.Add(self.radboxServer, 0, wxALL, 4)
		self.pubSizer.Add(self.lblCDDir, 0, wxALL, 4)

   		self.smallsizer = wxBoxSizer(wxHORIZONTAL)
   		self.smallsizer.Add(self.txtCDDir, 1, wxEXPAND|wxALL, 4)
   		self.smallsizer.Add(self.btnSelectFile, 0, wxALIGN_CENTER|wxALL, 4)

		self.pubSizer.Add(self.smallsizer, 0, wxEXPAND|wxALL, 4)

		if self.parent.pub.settings["CDSaveDir"] != "":
			self.txtCDDir.SetValue(self.parent.pub.settings["CDSaveDir"])

		panel.SetAutoLayout(True)
		panel.SetSizer(self.pubSizer)
		self.pubSizer.Fit(panel)
		panel.Layout()

		EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)

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
		self.chkSearch = wxCheckBox(panel, -1, _("Enable Search Function"))
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

	def btnSelectFileClicked(self, event):
		dialog = wxDirDialog(self, _("Choose a folder to store CD files."), style=wxDD_NEW_DIR_BUTTON)
		if dialog.ShowModal() == wxID_OK:
			self.txtCDDir.SetValue(dialog.GetPath())
		dialog.Destroy()
		
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

		#if self.radboxServer.GetStringSelection() == self.serverOptions[0]:
		#	self.parent.pub.settings["ServerProgram"] = "Karrigell"
		#	useswishe = True
		#elif self.radboxServer.GetStringSelection() == self.options[1]:
		#	self.parent.pub.settings["ServerProgram"] = "Documancer"

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

		self.parent.pub.settings["CDSaveDir"] = self.txtCDDir.GetValue()

		self.parent.pub.pubid = self.txtpubid.GetValue()
		self.parent.isDirty = True
		self.EndModal(wxID_OK)