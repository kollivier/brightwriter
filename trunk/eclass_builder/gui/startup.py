import string, os, sys
from wxPython.wx import *
import version

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

		self.lblVersion = wxStaticText(self, -1, "Version " + version.asString())

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

	def OnNew(self, event):
		self.EndModal(0)

	def OnOpen(self, event):
		self.EndModal(1)

	def OnTutorial(self, event):
		self.EndModal(2)

	def OnCheck(self, event):
		if event.Checked():
			self.parent.settings["ShowStartup"] = "False"
		else:
			self.parent.settings["ShowStartup"] = "True"
