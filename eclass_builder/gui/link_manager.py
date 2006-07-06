import string, os, sys, re
from wxPython.wx import *
import utils

class LinkChecker(wxDialog):
	def __init__(self, parent):
		wxDialog.__init__ (self, parent, -1, _("Link Checker"),wxDefaultPosition, wxSize(600, 440), wxDIALOG_MODAL|wxDEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.linkList = wxListCtrl(self, -1, size=(600,400), style=wxLC_REPORT)
		self.linkList.InsertColumn(0, _("Link"), width=300)
		self.linkList.InsertColumn(1, _("Page"), width=200)
		self.linkList.InsertColumn(2, _("Status"))

		self.btnOK = wxButton(self, wxID_OK, _("Check"))
		self.btnCancel = wxButton(self, wxID_CANCEL, _("Cancel"))

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
		files = os.listdir(os.path.join(self.parent.ProjectDir, "pub"))
		for file in files:
			if not self.isChecking:
				return
			self.currentFile = file
			filename = os.path.join(self.parent.ProjectDir, "pub", file)
			if os.path.isfile(filename):
				if string.find(os.path.splitext(file)[1], "htm") != -1: 
					myhtml = utils.openFile(filename, "r").read()
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
			self.linkList.SetStringItem(self.itemCount, 2, _("Connecting..."))
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
				self.linkList.SetStringItem(item, 2, _("OK"))
			except:
				self.linkList.SetStringItem(item, 2, _("Broken"))