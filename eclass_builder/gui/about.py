import string, sys, os
from wxPython.wx import *
import wxbrowser

class EClassAboutDialog(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("About EClass.Builder"), wxPoint(100,100),wxSize(460,400), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.browser = wxbrowser.wxBrowser(self, -1)
		self.browser.LoadPage(os.path.join(settings.AppDir,"about", parent.langdir, "about_eclass.html"))
		
		self.btnOK = wxButton(self,wxID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.mysizer = wxBoxSizer(wxVERTICAL)
		self.mysizer.Add(self.browser.browser, 1, wxEXPAND|wxALL, 4)
		self.mysizer.Add(self.btnOK, 0, wxALIGN_CENTER|wxALL, 6)			

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.Layout()

		EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)	

	def btnOKClicked(self, event):
		self.EndModal(wxID_OK)