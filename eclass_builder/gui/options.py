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
		                          style=wx.DIALOG_MODAL|wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parent = parent
		pane = self.GetContentsPane()
		pane.SetSizerType("form")
		
		wx.StaticText(pane, -1, _("HTML Editor"))
		self.pickHTMLEditor = picker.SelectBox(pane, settings.AppSettings["HTMLEditor"], 
		                                        "Program Files", guiutils.getOSApplicationsDir(),
		                                        [guiutils.getOSProgramExt()], textsize=(180, -1))
		
		wx.StaticText(pane, -1, _("OpenOffice Folder"))
		self.pickOpenOffice = picker.SelectBox(pane, settings.AppSettings["OpenOffice"], "Directory")
		
		wx.StaticText(pane, -1, _("Course Folder"))
		self.pickCourseFolder = picker.SelectBox(pane, settings.AppSettings["CourseFolder"], "Directory")
		
		wx.StaticText(pane, -1, _("Greenstone Directory"))
		self.pickGSDL = picker.SelectBox(pane, settings.AppSettings["GSDL"], "Directory")
		
		wx.StaticText(pane, -1, _("Language"))
		self.languages = ["English", "Francais", "Espanol"]

		self.cmbLanguage = wx.Choice(pane, -1, wx.DefaultPosition, wx.DefaultSize, self.languages)
		self.cmbLanguage.SetSizerProp("expand", True)
		
		wx.StaticText(pane, -1, _("New Page Default"))
		self.cmbDefaultPlugin = wx.Choice(pane, -1, wx.DefaultPosition, wx.DefaultSize, getPluginsCanCreateNew())
		self.cmbDefaultPlugin.SetSizerProp("expand", True)

		self.converters = {"Microsoft Office":"ms_office", "OpenOffice": "open_office", "Command Line Tools": "command_line"}

		self.lblConverter = wx.StaticText(pane, -1, _("Document Converter"))
		self.cmbConverter = wx.Choice(pane, -1, choices=self.converters.keys())
		self.cmbConverter.SetSizerProp("expand", True)

		#create the button sizer
		self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL))
			
		wx.EVT_BUTTON(self, wx.ID_OK, self.btnOKClicked)

		self.Fit()
		self.SetMinSize(self.GetSize())
		
		self.LoadSettings()

	def LoadSettings(self):
		if settings.AppSettings["Language"] != "":
			self.cmbLanguage.SetStringSelection(settings.AppSettings["Language"])

		if settings.AppSettings["DefaultPlugin"] != "":
			self.cmbDefaultPlugin.SetStringSelection(settings.AppSettings["DefaultPlugin"])

		defaultConv = ""
		if settings.AppSettings["PreferredConverter"] != "":
			for item in self.converters.items():
				if item[1] == settings.AppSettings["PreferredConverter"]:
					defaultConv = item[0]

		if defaultConv != "":
			self.cmbConverter.SetStringSelection(defaultConv)

	def btnOKClicked(self, event):
		settings.AppSettings["HTMLEditor"] = self.pickHTMLEditor.GetValue()
		settings.AppSettings["OpenOffice"] = self.pickOpenOffice.GetValue()

		settings.AppSettings["GSDL"] = self.pickGSDL.GetValue()
		settings.AppSettings["CourseFolder"] = self.pickCourseFolder.GetValue()
		settings.AppSettings["DefaultPlugin"] = self.cmbDefaultPlugin.GetStringSelection()
		
		if self.cmbConverter.GetStringSelection() != "":
			settings.AppSettings["PreferredConverter"] = self.converters[self.cmbConverter.GetStringSelection()]
		
		language = settings.AppSettings["Language"]
		if language != self.cmbLanguage.GetStringSelection():
			settings.AppSettings["Language"] = self.cmbLanguage.GetStringSelection()
			wx.MessageDialog(self, _("You will need to restart EClass.Builder for changes to take effect."), _("Restart required."), wx.OK).ShowModal()
		self.EndModal(wx.ID_OK)
