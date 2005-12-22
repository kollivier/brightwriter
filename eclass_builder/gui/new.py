import string, sys, os
from wxPython.wx import *
import plugins
from conman.validate import MakeFileName2
import utils
import settings

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
		self.buttonSizer = wxStdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
		self.mysizer.Add(self.buttonSizer, 0)
		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.mysizer.Fit(self)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
	
	def btnOKClicked(self, event):
		settings.CurrentDir = self.parent.CurrentDir = self.parent.pub.directory = os.path.join(self.parent.settings["CourseFolder"], utils.MakeFolder(self.txtTitle.GetValue()))
		#print self.parent.CurrentDir

		if not os.path.exists(self.parent.CurrentDir):
			os.mkdir(self.parent.CurrentDir)
			self.parent.pub.name = self.txtTitle.GetValue()
			self.parent.pub.description = self.txtDescription.GetValue()
			self.parent.pub.keywords = self.txtKeywords.GetValue()
			self.EndModal(wxID_OK)
		else:
			wxMessageDialog(self, _("A publication with this name already exists. Please choose another name."), _("Publication exists!"), wxOK).ShowModal()

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
		for plugin in plugins.pluginList:
			if plugin.plugin_info["CanCreateNew"]:
				self.cmbType.Append(plugin.plugin_info["FullName"])
			if self.parent.settings["DefaultPlugin"] != "" and plugin.plugin_info["FullName"] == self.parent.settings["DefaultPlugin"]:
				extension = "." + plugin.plugin_info["Extension"][0]
		
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
		self.buttonSizer = wxStdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
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
		for plugin in plugins.pluginList:
			if plugin.plugin_info["FullName"] == pluginname:
				extension = "." + plugin.plugin_info["Extension"][0]
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
		for plugin in plugins.pluginList:
			if plugin.plugin_info["FullName"] == pluginname:
				break

		if os.path.exists(os.path.join(self.parent.CurrentDir, plugin.plugin_info["Directory"], self.txtFilename.GetValue())):
			wxMessageBox(_("Filename already exists. Please rename the file and try again."))
		else:
			self.EndModal(wxID_OK)