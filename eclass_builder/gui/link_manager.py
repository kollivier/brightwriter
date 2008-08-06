import string, os, sys, re
import wx
import wx.lib.sized_controls as sc
import persistence
import autolist
import utils
import guiutils
import settings

class LinkChecker(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("Link Checker"),wx.DefaultPosition, (600, 440), wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		self.selItem = None
		
		pane = self.GetContentsPane()
		self.linkList = autolist.AutoSizeListCtrl(pane, -1, size=(600,400), style=wx.LC_REPORT)
		self.linkList.InsertColumn(0, _("Link"), width=300)
		self.linkList.InsertColumn(1, _("Page"), width=200)
		self.linkList.InsertColumn(2, _("Status"))
		self.linkList.SetSizerProps({"expand": True, "proportion":1})
		
		btnPane = sc.SizedPanel(pane, -1)
		btnPane.SetSizerProps({"expand": True, "halign":"right"})

		self.btnOK = wx.Button(self, wx.ID_OK, _("Check"))
		self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
		
		self.btnSizer = wx.StdDialogButtonSizer()
		self.btnSizer.AddButton(self.btnOK)
		self.btnSizer.AddButton(self.btnCancel)
		self.btnSizer.Realize()
		
		self.SetButtonSizer(self.btnSizer)

		#self.mysizer = wxBoxSizer(wxVERTICAL)
		#self.mysizer.Add(self.linkList, 1, wxEXPAND | wxALL, 4)
		#self.buttonsizer = wxBoxSizer(wxHORIZONTAL)
		#self.buttonsizer.Add((1, 1), 1, wxEXPAND)
		#self.buttonsizer.Add(self.btnOK, 0, wxALL, 4)
		#self.buttonsizer.Add(self.btnCancel, 0, wxALL,4)
		#self.mysizer.Add(self.buttonsizer, 0, wxALL|wxALIGN_RIGHT, 4)
		self.links = []
		self.itemCount = 0
		self.isChecking = False
		self.currentFile = ""
		#self.SetAutoLayout(True)
		#self.SetSizerAndFit(self.mysizer)
		#self.Layout()
		
		self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self, wx.ID_OK, self.OnCheck)
		wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
		self.linkList.Bind(wx.EVT_LEFT_DCLICK, self.OnDblClick)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSel, self.linkList)
		
	def OnItemSel(self, event):
		self.selItem = event.m_itemIndex
	
	def OnDblClick(self, event):
		if self.selItem:
			filename = settings.ProjectDir + self.linkList.GetItem(self.selItem, 1).GetText()
			guiutils.openInHTMLEditor(filename)

	def OnCheck(self, event):
		self.btnOK.Enable(False)
		self.isChecking = True
		self.CheckLinks()
		self.btnOK.Enable(True)
		self.isChecking = False

	def OnCancel(self, event):
		self.isChecking = False
		self.EndModal(wx.ID_CANCEL)

	def CheckLinks(self):
		files = os.listdir(os.path.join(settings.ProjectDir, "Text"))
		for file in files:
			if not self.isChecking:
				return
			self.currentFile = file
			filename = os.path.join(settings.ProjectDir, "Text", file)
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
			if self.linkList:
				self.linkList.InsertStringItem(self.itemCount, link)
				self.linkList.SetStringItem(self.itemCount, 1, "/Text/" + self.currentFile)
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
				request = urllib2.Request(link)
				opener = urllib2.build_opener()
				# some providers, such as Wikipedia, will block requests
				# when a user agent isn't specified, or if it's a defualt
				# user agent for automated bots. So we need to specify our
				# own user agent to keep from being blocked.
				request.add_header('User-Agent','EClass Link Checker/1.0 +http://www.eclass.net/') 
				opener.open(request)
				wx.CallAfter(self.linkList.SetStringItem, item, 2, _("OK"))
			except urllib2.URLError, e:
				print "link is: " + link
				if hasattr(e, 'reason'):
					print 'We failed to reach a server.'
					print 'Reason: ', e.reason
				elif hasattr(e, 'code'):
					print 'The server couldn\'t fulfill the request.'
					print 'Error code: ', e.code
				wx.CallAfter(self.linkList.SetStringItem, item, 2, _("Broken"))