import sys, string, os
import utils
import guiutils
import time

import wx
from wxaddons.persistence import *
from wxaddons.sized_controls import *
import errors

appErrorLog = errors.appErrorLog

class ErrorLogViewer(SizedDialog):
	def __init__(self, parent=None):
		SizedDialog.__init__(self, parent, -1, _("Error log viewer"), wx.DefaultPosition, wx.Size(420, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		pane = self.GetContentsPane()
		self.listCtrl = wx.ListCtrl(pane, -1, style=wx.LC_REPORT)
		self.listCtrl.SetSizerProp("expand", "true")
		self.listCtrl.SetSizerProp("proportion", 1)
		
		self.lblDetails = wx.StaticText(pane, -1, _("Error Details"))
		self.details = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
		self.details.SetSizerProp("expand", "true")
		self.details.SetSizerProp("proportion", 1)
		
		self.itemCount = 0
		self.selItem = None
		self.listCtrl.InsertColumn(0, _("Time"))
		self.listCtrl.InsertColumn(1, _("Error Message"))
		self.listCtrl.SetColumnWidth(0, 100)
		self.listCtrl.SetColumnWidth(1, 280)

		btnpane = SizedPanel(pane, -1)
		btnpane.SetSizerType("horizontal")
		btnpane.SetSizerProp("expand", "true")

		self.saveBtn = wx.Button(btnpane, wx.ID_SAVE)
		spacer = SizedPanel(btnpane, -1)
		spacer.SetSizerProp("expand", "true")
		spacer.SetSizerProp("proportion", 1)

		self.clearBtn = wx.Button(btnpane, -1, _("Clear"))

		wx.EVT_BUTTON(self, self.clearBtn.GetId(), self.OnClear)
		wx.EVT_BUTTON(self, self.saveBtn.GetId(), self.OnSave)
		#EVT_LEFT_DCLICK(self, self.listCtrl.GetId(), self.OnDblClick)
		wx.EVT_LIST_ITEM_SELECTED(self, self.listCtrl.GetId(), self.OnSelection)

		self.LoadErrorLog()
		wx.EVT_ACTIVATE(self, self.OnActivate)

	def OnSelection(self, evt):
		self.details.SetValue(self.errList[self.listCtrl.GetItemData(evt.m_itemIndex)][2])
		
	def OnActivate(self, evt):
		self.LoadErrorLog()

#	def OnDblClick(self, evt):
#		wxMessageBox(self.

	def OnSave(self, evt):
		global appErrorLog
		fileDialog = wx.FileDialog(self, _("Save Log File"),"", "errorlog.txt", style=wxSAVE|wxOVERWRITE_PROMPT)
		result = fileDialog.ShowModal() 
		if result == wx.ID_OK:
			filename = fileDialog.GetPath()
			afile = open(filename, "wb")
			afile.write(appErrorLog.read().encode("utf-8"))
			afile.close()
		fileDialog.Destroy()

	def OnClear(self, evt):
		global appErrorLog
		appErrorLog.clear()
		self.LoadErrorLog()
		self.details.SetValue("")

	def LoadErrorLog(self):
		global appErrorLog
		self.listCtrl.DeleteAllItems()
		self.itemCount = 0
		errorList = appErrorLog.read().split(appErrorLog.separator + "\n")
		self.errList = []
		for err in errorList:
			if err != "":
				errArray = err.split(appErrorLog.separator)
				self.errList.append(errArray)
				index = self.errList.index(errArray)
				self.listCtrl.InsertStringItem(self.itemCount, errArray[0])
				if len(errArray) > 1:
					self.listCtrl.SetStringItem(self.itemCount, 1, errArray[1])
				self.listCtrl.SetItemData(self.itemCount, index)
				self.itemCount += 1