import string, sys, os
from wxPython.wx import *

class OpenPubDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Open Publication"), wxPoint(100,100),wxSize(480,200), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		height = 20
		if wxPlatform == "__WXMAC__":
			height = 25
		self.parent = parent
		self.path = ""
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
		self.buttonsizer.Add(self.btnBrowse, 0, wxALIGN_LEFT)
		self.buttonsizer.Add((1,1),1, wxEXPAND | wxALL, 4)
		stdbuttonsizer = wxStdDialogButtonSizer()
		stdbuttonsizer.AddButton(self.btnOK)
		stdbuttonsizer.AddButton(self.btnCancel)
		stdbuttonsizer.Realize()
		self.buttonsizer.Add(stdbuttonsizer)
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
			self.path = f.GetPath()
			f.Destroy()
			if not os.path.exists(os.path.join(self.path, "imsmanifest.xml")):
				message = _("This folder does not contain an EClass Project. Please try selecting another folder.")
				dialog = wxMessageDialog(self, message, "No EClass Found", wxOK)
				dialog.ShowModal()
				dialog.Destroy()
				return

			self.EndModal(wxID_OK)
			
	def GetPath(self):
		return os.path.join(self.path, "imsmanifest.xml")
		
	def btnOKClicked(self, event):
		if self.cmbpubs.GetStringSelection() != "":
			self.path = os.path.join(self.coursedir, self.cmbpubs.GetStringSelection())
			self.EndModal(wxID_OK)