import string, sys, os
import wx
import wx.lib.sized_controls as sc
import persistence
import plugins
from fileutils import MakeFileName2
import utils
import settings

def GetBestSize(self):
	height = self.GetMinSize()[1]
	return wx.Size(180, height)
	
wx.TextCtrl.DoGetBestSize = GetBestSize

class NewPubDialog(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("New Project"), wx.Point(100,100), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		self.eclassdir = None
		pane = self.GetContentsPane()
		pane.SetSizerType("form")
		self.lblTitle = wx.StaticText(pane, -1, _("Name"))
		self.lblTitle.SetSizerProp("valign", "center")
		self.txtTitle = wx.TextCtrl(pane, -1, size=(180, -1))
		self.txtTitle.SetSizerProp("expand", True)
		self.lblDescription = wx.StaticText(pane, -1, _("Description"))
		self.lblDescription.SetSizerProp("valign", "center")
		self.txtDescription = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
		self.txtDescription.SetSizerProps({"expand":True, "proportion":1})
		self.lblKeywords = wx.StaticText(pane, -1, _("Keywords"))
		self.lblKeywords.SetSizerProp("valign", "center")
		self.txtKeywords = wx.TextCtrl(pane, -1)
		self.txtKeywords.SetSizerProp("expand", True)

		self.btnOK = wx.Button(self,wx.ID_OK)
		self.btnOK.SetDefault()
		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(0, -1)
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"))

		self.buttonSizer = wx.StdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
		self.SetButtonSizer(self.buttonSizer)
		
		self.Fit()
		self.SetMinSize(self.GetSize())
		# TODO: Add close dialog support for this
		#self.LoadState("NewPubDialog")

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
	
	def btnOKClicked(self, event):
		self.eclassdir = os.path.join(settings.AppSettings["EClass3Folder"], 
		                        utils.createSafeFilename(self.txtTitle.GetValue()))

		if not os.path.exists(self.eclassdir):
			self.EndModal(wx.ID_OK)
		else:
			wx.MessageDialog(self, _("A publication with this name already exists. Please choose another name."), _("Publication exists!"), wx.OK).ShowModal()

class NewPageDialog(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("New Page"), wx.Point(100,100), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		pane = self.GetContentsPane()
		pane.SetSizerType("form")

		self.lblTitle = wx.StaticText(pane, -1, _("Name"))
		self.lblTitle.SetSizerProp("valign", "center")
		self.txtTitle = wx.TextCtrl(pane, -1, _("New Page"), size=(180, -1))
		self.txtTitle.SetSizerProp("expand", True)

		self.lblFilename = wx.StaticText(pane, -1, "Filename")
		self.lblFilename.SetSizerProp("valign", "center")
		self.txtFilename = wx.TextCtrl(pane, -1, _("New Page"))
		self.txtFilename.SetSizerProp("expand", True)
		self.filenameEdited = False
		
		extension = ".xhtml"
		self.txtFilename.SetValue(self.txtTitle.GetValue())
		self.UpdateFilename(None)

		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.txtTitle.SetFocus()
		self.txtTitle.SetSelection(0, -1)
		self.btnCancel = wx.Button(self,wx.ID_CANCEL,_("Cancel"))

		self.buttonSizer = wx.StdDialogButtonSizer()
		self.buttonSizer.AddButton(self.btnOK)
		self.buttonSizer.AddButton(self.btnCancel)
		self.buttonSizer.Realize()
		self.SetButtonSizer(self.buttonSizer)
		
		self.Fit()
		self.SetMinSize(self.GetSize())
		self.SetMaxSize((-1, self.GetSize().y))

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)
		wx.EVT_BUTTON(self.btnCancel, self.btnCancel.GetId(), self.btnCancelClicked)
		wx.EVT_CHAR(self.txtFilename, self.CheckFilename)
		wx.EVT_TEXT(self, self.txtTitle.GetId(), self.UpdateFilename)

	def CheckFilename(self, event):
		self.filenameEdited = True
		event.Skip()
	
	def UpdateFilename(self, event):
		title = self.txtFilename.GetValue()
		if string.find(title, ".") != -1:
			title = title[:string.rfind(title, ".")]

		extension = ".html"

		if not self.filenameEdited:
			title = MakeFileName2(self.txtTitle.GetValue())
		
			title = title[:31-len(extension)]
	
			filename = title + extension
			counter = 2
			oldtitle = title
			self.txtFilename.SetValue(os.path.join('Content', filename))


	def btnCancelClicked(self, event):
		self.EndModal(wx.ID_CANCEL)

	def btnOKClicked(self, event):
		if os.path.exists(os.path.join(settings.ProjectDir, self.txtFilename.GetValue())):
			wx.MessageBox(_("Filename already exists. Please rename the file and try again."))
		else:
			self.EndModal(wx.ID_OK)
