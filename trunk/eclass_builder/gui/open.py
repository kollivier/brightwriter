import string, sys, os
import wx
import wxaddons.sized_controls as sc
import wxaddons.persistence
import settings

class OpenPubDialog(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("Open Publication"), (100,100), (480,200), wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.parent = parent
		self.path = ""
		
		pane = self.GetContentsPane()
		self.lblSelect = wx.StaticText(pane, -1, _("Select a publication:"))
		self.cmbpubs = wx.ListBox(pane, -1)
		self.cmbpubs.SetSizerProps({"expand": True, "proportion": 1})
		self.coursedir = settings.AppSettings["CourseFolder"]

		btnPane = sc.SizedPanel(pane, -1)
		btnPane.SetSizerType("horizontal")
		btnPane.SetSizerProp("expand", True)
		self.btnBrowse = wx.Button(btnPane, -1, _("Browse..."))
		spacer = sc.SizedPanel(btnPane, -1)
		spacer.SetSizerProps({"expand": True, "proportion": 1})
		self.btnOK = wx.Button(btnPane,wx.ID_OK, _("OK"))
		self.btnOK.SetDefault()
		self.btnCancel = wx.Button(btnPane,wx.ID_CANCEL,_("Cancel"))

		#self.buttonsizer.Add(self.btnBrowse, 0, wx.ALIGN_LEFT)
		#self.buttonsizer.Add((1,1),1, wx.EXPAND | wx.ALL, 4)
		stdbuttonsizer = wx.StdDialogButtonSizer()
		stdbuttonsizer.AddButton(self.btnOK)
		stdbuttonsizer.AddButton(self.btnCancel)
		stdbuttonsizer.Realize()
		btnPane.GetSizer().Add(stdbuttonsizer, 0, wx.ALIGN_CENTER)
		#self.SetButtonSizer(self.buttonsizer)

		self.LoadProjects()
		self.cmbpubs.SetFocus()
		if self.cmbpubs.GetCount() > 0:
			self.cmbpubs.SetSelection(0)

		self.Fit()
		self.SetMinSize(self.GetSize())

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		wx.EVT_BUTTON(self.btnBrowse, self.btnBrowse.GetId(), self.btnBrowseClicked)
		wx.EVT_LEFT_DCLICK(self.cmbpubs, self.btnOKClicked)

	def LoadProjects(self):
		if os.path.exists(self.coursedir):
			for item in os.listdir(self.coursedir):
				try:
					mypub = os.path.join(self.coursedir, item)
					if os.path.isdir(mypub) and os.path.exists(os.path.join(mypub, "imsmanifest.xml")):
						self.cmbpubs.Append(item)
				except:
					pass

	def btnBrowseClicked(self, event):
		dir = ""
		f = wx.DirDialog(self, _("Select the folder containing your EClass"))
		if f.ShowModal() == wx.ID_OK:
			self.path = f.GetPath()
			f.Destroy()
			if not os.path.exists(os.path.join(self.path, "imsmanifest.xml")):
				message = _("This folder does not contain an EClass Project. Please try selecting another folder.")
				dialog = wx.MessageDialog(self, message, "No EClass Found", wx.OK)
				dialog.ShowModal()
				dialog.Destroy()
				return

			self.EndModal(wx.ID_OK)
			
	def GetPath(self):
		return os.path.join(self.path, "imsmanifest.xml")
		
	def btnOKClicked(self, event):
		if self.cmbpubs.GetStringSelection() != "":
			self.path = os.path.join(self.coursedir, self.cmbpubs.GetStringSelection())
			self.EndModal(wx.ID_OK)