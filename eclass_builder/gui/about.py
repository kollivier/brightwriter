import string, sys, os
import wx
import wxbrowser
import settings

class EClassAboutDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__ (self, parent, -1, _("About EClass.Builder"), wx.Point(100,100),wx.Size(460,400), wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE)
		self.parent = parent
		self.browser = wxbrowser.wxBrowser(self, -1)
		self.browser.LoadPage(os.path.join(settings.AppDir,"about", settings.LangDirName, "about_eclass.html"))
		
		self.btnOK = wx.Button(self,wx.ID_OK,_("OK"))
		self.btnOK.SetDefault()
		self.mysizer = wx.BoxSizer(wx.VERTICAL)
		self.mysizer.Add(self.browser.browser, 1, wx.EXPAND|wx.ALL, 4)
		self.mysizer.Add(self.btnOK, 0, wx.ALIGN_CENTER|wx.ALL, 6)			

		self.SetAutoLayout(True)
		self.SetSizer(self.mysizer)
		self.Layout()

		wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.btnOKClicked)	

	def btnOKClicked(self, event):
		self.EndModal(wx.ID_OK)
