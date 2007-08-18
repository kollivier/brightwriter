import string, os, sys
import wx
import version

class StartupDialog(wx.Dialog):
	def __init__(self, parent):
		point = parent.GetPositionTuple()
		size = parent.GetSizeTuple()
		wx.Dialog.__init__ (self, parent, -1, _("Welcome to EClass.Builder"),wx.DefaultPosition, wx.Size(460,160), wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE)
		height = 20
		buttonstart = 90
		fontsize = 22
		if wx.Platform == "__WXMAC__":
			buttonstart = 50
			height = 25
			fontsize = 28
		self.parent = parent
		myfont = wx.Font(fontsize, wx.MODERN, wx.NORMAL, wx.BOLD, False, "Arial")
		self.lblWelcome = wx.StaticText(self, -1, _("Welcome to EClass.Builder"))
		self.lblWelcome.SetFont(myfont)
		self.lblWelcome.SetForegroundColour(wx.NamedColour("blue"))

		self.lblVersion = wx.StaticText(self, -1, "Version " + version.asString())

		self.chkShowThisDialog = wx.CheckBox(self, -1, _("Don't show this dialog on startup."))
		self.btnNew = wx.Button(self, -1, _("New Project"))
		self.btnOpen = wx.Button(self, -1, _("Open Project"))
		self.btnOpen.SetDefault()
		self.btnTutorial = wx.Button(self, -1, _("View Tutorial"))

		self.dialogsizer = wx.BoxSizer(wx.VERTICAL)
		self.dialogsizer.Add(self.lblWelcome, 0, wx.ALL|wx.ALIGN_CENTER, 4)	
		self.dialogsizer.Add(self.lblVersion, 0, wx.ALL|wx.ALIGN_CENTER, 4)	
		self.dialogsizer.Add(self.chkShowThisDialog, 0, wx.ALL|wx.ALIGN_CENTER, 10)
		self.boxsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.boxsizer.Add(self.btnNew, 0, wx.ALL | wx.ALIGN_CENTER, 10)
		self.boxsizer.Add(self.btnOpen, 0, wx.ALL | wx.ALIGN_CENTER, 10)
		self.boxsizer.Add(self.btnTutorial, 0, wx.ALL | wx.ALIGN_CENTER, 10)
		self.dialogsizer.Add(self.boxsizer, 1, wx.ALIGN_CENTER)
		self.SetAutoLayout(True)
		self.SetSizerAndFit(self.dialogsizer)
		self.Layout()
		self.CentreOnParent(wx.BOTH)

		wx.EVT_BUTTON(self, self.btnNew.GetId(), self.OnNew)
		wx.EVT_BUTTON(self, self.btnOpen.GetId(), self.OnOpen)
		wx.EVT_BUTTON(self, self.btnTutorial.GetId(), self.OnTutorial)
		wx.EVT_CHECKBOX(self, self.chkShowThisDialog.GetId(), self.OnCheck)

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
