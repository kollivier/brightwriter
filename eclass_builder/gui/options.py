import string, sys, os
import wx
import wx.lib.sized_controls as sc
import persistence
import gui.select_box as picker

import plugins
import utils
import guiutils
import settings

def getPluginsCanCreateNew():
	pluginnames = []
	for plugin in plugins.pluginList:
	   if plugin.plugin_info["CanCreateNew"]:
			pluginnames.append(plugin.plugin_info["FullName"])
			
	return pluginnames

class PreferencesEditor(sc.SizedDialog):
	def __init__(self, parent):
		sc.SizedDialog.__init__ (self, parent, -1, _("Options"), wx.Point(100,100), 
		                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		pane = self.GetContentsPane()
		pane.SetSizerType("form")
		
		wx.StaticText(pane, -1, _("Course Folder"))
		self.pickCourseFolder = picker.SelectBox(pane, settings.AppSettings["EClass3Folder"], "Directory")
		
		wx.StaticText(pane, -1, _("Language"))
		self.languages = ["English", "Francais", "Espanol"]

		self.cmbLanguage = wx.Choice(pane, -1, wx.DefaultPosition, wx.DefaultSize, self.languages)
		self.cmbLanguage.SetSizerProp("expand", True)

		#create the button sizer
		self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))
			
		wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)

		self.Fit()
		self.SetMinSize(self.GetSize())
		
		self.LoadSettings()

	def LoadSettings(self):
		if settings.AppSettings["Language"] != "":
			self.cmbLanguage.SetStringSelection(settings.AppSettings["Language"])

	def btnOKClicked(self, event):
		settings.AppSettings["EClass3Folder"] = self.pickCourseFolder.GetValue()
		
		language = settings.AppSettings["Language"]
		if language != self.cmbLanguage.GetStringSelection():
			settings.AppSettings["Language"] = self.cmbLanguage.GetStringSelection()
			wx.MessageDialog(self, _("You will need to restart EClass.Builder for changes to take effect."), _("Restart required."), wx.OK).ShowModal()
		self.EndModal(wx.ID_OK)
