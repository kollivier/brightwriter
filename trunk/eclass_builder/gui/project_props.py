import string, sys, os
import wx
import wxaddons.sized_controls as sc
import wxaddons.persistence
import settings
import encrypt

class ProjectPropsDialog(sc.SizedDialog):
	def __init__(self, parent):
		"""
		Dialog for setting various project properties.

		"""
		sc.SizedDialog.__init__(self, parent, -1, _("Project Settings"), wx.Point(100, 100), wx.Size(400, 400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		pane = self.GetContentsPane()
		self.notebook = wx.Notebook(pane, -1)
		self.notebook.SetSizerProps({"proportion":1, "expand":True})
		self.parent = parent
		self.searchchanged = False
		
		self.generalPanel = GeneralPanel(self.notebook, self.parent.pub)
		self.notebook.AddPage(self.generalPanel, _("General"))
		
		self.searchPanel = SearchPanel(self.notebook, self.parent.pub)
		self.notebook.AddPage(self.searchPanel, _("Search"))
		
		self.publishPanel = PublishPanel(self.notebook)
		self.notebook.AddPage(self.publishPanel, _("Publish"))
		
		self.ftpPanel = FTPPanel(self.notebook)
		self.notebook.AddPage(self.ftpPanel, _("FTP"))
		if wx.Platform == '__WXMAC__':
			self.notebook.SetSelection(0)

		self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))

		self.Fit()
		self.SetMinSize(self.GetSize())
		
		# TODO: Can this be removed?
		if wx.Platform == '__WXMSW__':
			wx.EVT_CHAR(self.notebook, self.SkipNotebookEvent)
		wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)

	def SkipNotebookEvent(self, event):
		event.Skip()
		
	def btnOKClicked(self, event):
		self.parent.pub.name = self.generalPanel.txtname.GetValue()
		self.parent.pub.description = self.generalPanel.txtdescription.GetValue()
		self.parent.pub.keywords = self.generalPanel.txtkeywords.GetValue()

		settings.ProjectSettings["SearchEnabled"] = int(self.searchPanel.chkSearch.GetValue())
		useswishe = False
		updatetheme = False
		if self.searchPanel.whichSearch.GetStringSelection() == self.searchPanel.options[0]:
			settings.ProjectSettings["SearchProgram"] = "Lucene"
			useswishe = True
		elif self.searchPanel.whichSearch.GetStringSelection() == self.self.searchPanel.options[1]:
			settings.ProjectSettings["SearchProgram"] = "Greenstone"

		if self.searchchanged:
			self.parent.Update()
		if self.publishPanel.chkFilename.GetValue() == True:
			settings.ProjectSettings["ShortenFilenames"] = "Yes"
		else:
			settings.ProjectSettings["ShortenFilenames"] = "No"

		settings.ProjectSettings["FTPHost"] = self.ftpPanel.txtFTPSite.GetValue()
		settings.ProjectSettings["FTPDirectory"] = self.ftpPanel.txtDirectory.GetValue()
		settings.ProjectSettings["FTPUser"] = self.ftpPanel.txtUsername.GetValue()
		settings.ProjectSettings["FTPPassword"] = encrypt.encrypt(self.ftpPanel.txtPassword.GetValue())

		if self.ftpPanel.chkPassiveFTP.GetValue() == True:
			settings.ProjectSettings["FTPPassive"] = "Yes"
		else:
			settings.ProjectSettings["FTPPassive"] = "No"

		if self.ftpPanel.chkUploadOnSave.GetValue() == True:
			settings.ProjectSettings["UploadOnSave"] = "Yes"
		else:
			settings.ProjectSettings["UploadOnSave"] = "No"

		settings.ProjectSettings["CDSaveDir"] = self.publishPanel.txtCDDir.GetValue()

		self.parent.pub.pubid = self.searchPanel.txtpubid.GetValue()
		self.parent.isDirty = True
		self.EndModal(wx.ID_OK)
		
class GeneralPanel(sc.SizedPanel):
    def __init__(self, parent, pub):
		sc.SizedPanel.__init__(self, parent, -1)
		self.pub = pub
		self.SetSizerType("form")
		self.lblname = wx.StaticText(self, -1, _("Name"))
		self.txtname = wx.TextCtrl(self, -1, pub.name)
		self.txtname.SetSizerProp("expand", True)
		self.lbldescription = wx.StaticText(self, -1, _("Description"))
		self.txtdescription = wx.TextCtrl(self, -1, pub.description, style=wx.TE_MULTILINE)
		self.txtdescription.SetSizerProps({"expand":True, "proportion":1})
		self.lblkeywords = wx.StaticText(self, -1, _("Keywords"))
		self.txtkeywords = wx.TextCtrl(self, -1, pub.keywords) 
		self.txtkeywords.SetSizerProp("expand", True)
		self.txtname.SetFocus()
		self.txtname.SetSelection(0, -1)
		
class SearchPanel(sc.SizedPanel):
	def __init__(self, parent, pub):
		sc.SizedPanel.__init__(self, parent, -1)
		self.chkSearch = wx.CheckBox(self, -1, _("Enable Search Function"))
		
		self.options = [_("Use Lucene for searching (Default)"), _("Use Greenstone for searching")]
		self.whichSearch = wx.RadioBox(self, -1, _("Search Engine"), wx.DefaultPosition, wx.DefaultSize, self.options, 1)
		
		#self.useGSDL = wxRadioBox(panel, -1, )
		
		self.lblpubid = wx.StaticText(self, -1, _("Greenstone Collection ID"))
		self.txtpubid = wx.TextCtrl(self, -1, pub.pubid)
		self.lblpubidhelp = wx.StaticText(self, -1, _("ID must be 8 chars or less, no spaces, all letters\n and/or numbers."))
		
		self.LoadSettings()
		self.updatePubIdState()

		wx.EVT_CHECKBOX(self, self.chkSearch.GetId(), self.chkSearchClicked)
		wx.EVT_RADIOBOX(self, self.whichSearch.GetId(), self.whichSearchClicked)
		
	def whichSearchClicked(self, event):
		self.updatePubIdState()
		self.searchchanged = True
		
	def updatePubIdState(self):
		value = (self.chkSearch.IsChecked() and self.whichSearch.GetStringSelection() == self.options[1])
		self.lblpubid.Enable(value)
		self.txtpubid.Enable(value)
		self.lblpubidhelp.Enable(value)
	
	def chkSearchClicked(self, event):
		value = self.chkSearch.GetValue()
		self.whichSearch.Enable(value)
		self.updatePubIdState()
		self.searchchanged = True
 
	def LoadSettings(self):
		ischecked = settings.ProjectSettings["SearchEnabled"]
		searchtool = ""
		if not ischecked == "":
			try:
				searchbool = int(ischecked)
			except:
				searchbool = 0

			self.chkSearch.SetValue(searchbool)
			if searchbool:
				searchtool = settings.ProjectSettings["SearchProgram"]
				if searchtool == "": #since there wasn't an option selected, must be Greenstone
					searchtool = "Greenstone"
					
		if searchtool == "Greenstone":
			self.whichSearch.SetStringSelection(self.options[1])
		elif searchtool == "Lucene":
			self.whichSearch.SetStringSelection(self.options[0])
			
		value = self.chkSearch.GetValue()
		self.lblpubid.Enable(value)
		self.txtpubid.Enable(value)
		self.lblpubidhelp.Enable(value)
		
class PublishPanel(sc.SizedPanel):
	def __init__(self, parent):
		sc.SizedPanel.__init__(self, parent, -1)
		self.chkFilename = wx.CheckBox(self, -1, _("Restrict filenames to 31 characters"))

		self.lblCDDir = wx.StaticText(self, -1, _("Directory to save CD files:"))
		
		cdpanel = sc.SizedPanel(self, -1)
		cdpanel.SetSizerType("horizontal")
		cdpanel.SetSizerProp("expand", True)
		self.txtCDDir = wx.TextCtrl(cdpanel, -1, "")
		self.txtCDDir.SetSizerProps({"expand":True, "proportion":1})
		
		icnFolder = wx.Bitmap(os.path.join(settings.AppDir, "icons", "Open.gif"), wx.BITMAP_TYPE_GIF)
		self.btnSelectFile = wx.BitmapButton(cdpanel, -1, icnFolder)
		self.btnSelectFile.SetSizerProp("valign", "center")

		self.LoadSettings()

		wx.EVT_BUTTON(self.btnSelectFile, self.btnSelectFile.GetId(), self.btnSelectFileClicked)
	
	def LoadSettings(self):
		if settings.ProjectSettings["CDSaveDir"] != "":
			self.txtCDDir.SetValue(settings.ProjectSettings["CDSaveDir"])
			
		if settings.ProjectSettings["ShortenFilenames"] == "Yes":
			self.chkFilename.SetValue(1)
		
	def btnSelectFileClicked(self, event):
		dialog = wx.DirDialog(self, _("Choose a folder to store CD files."), style=wx.DD_NEW_DIR_BUTTON)
		if dialog.ShowModal() == wx.ID_OK:
			self.txtCDDir.SetValue(dialog.GetPath())
		dialog.Destroy()
		
class FTPPanel(sc.SizedPanel):
	def __init__(self, parent):
		sc.SizedPanel.__init__(self, parent, -1)
		ftppanel = sc.SizedPanel(self, -1)
		ftppanel.SetSizerType("form")
		ftppanel.SetSizerProp("expand", True)
		self.lblFTPSite = wx.StaticText(ftppanel, -1, _("FTP Site"))
		self.txtFTPSite = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPHost"])
		self.txtFTPSite.SetSizerProp("expand", True)
		self.lblUsername = wx.StaticText(ftppanel, -1, _("Username"))
		self.txtUsername = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPUser"])
		self.txtUsername.SetSizerProp("expand", True)
		self.lblPassword = wx.StaticText(ftppanel, -1, _("Password"))
		# FIXME - restore this setting once I clean up the FTP support
		self.txtPassword = wx.TextCtrl(ftppanel, -1, encrypt.decrypt(settings.ProjectSettings["FTPPassword"]), style=wx.TE_PASSWORD)
		self.txtPassword.SetSizerProp("expand", True)
		self.lblDirectory = wx.StaticText(ftppanel, -1, _("Directory"))
		self.txtDirectory = wx.TextCtrl(ftppanel, -1, settings.ProjectSettings["FTPDirectory"])
		self.txtDirectory.SetSizerProp("expand", True)
		
		self.chkPassiveFTP = wx.CheckBox(self, -1, _("Use Passive FTP"))
		self.chkUploadOnSave = wx.CheckBox(self, -1, _("Upload Files on Save"))
		
		self.txtFTPSite.SetFocus()
		self.txtFTPSite.SetSelection(0, -1)
		
	def LoadSettings(self):
		if settings.ProjectSettings["FTPPassive"] == "Yes":
			self.chkPassiveFTP.SetValue(True)
		else:
			self.chkPassiveFTP.SetValue(False)
			
		if settings.ProjectSettings["UploadOnSave"] == "Yes":
			self.chkUploadOnSave.SetValue(True)
		else:
			self.chkUploadOnSave.SetValue(False)