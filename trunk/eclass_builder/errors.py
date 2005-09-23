import sys, string, os
import utils
import guiutils
import time
from wxPython.wx import *

class AppErrorLog(utils.LogFile):
	def __init__(self):
		utils.LogFile.__init__(self)
		self.filename = os.path.join(guiutils.getAppDataDir(), "errors.txt")
		self.separator = u"|"

	def write(self, message):
		message = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + self.separator + message
		utils.LogFile.write(self, message)

appErrorLog = AppErrorLog()

class ErrorLogViewer(wxDialog):
	def __init__(self, parent=None):
		wxDialog.__init__(self, parent, -1, _("Error log viewer"), wxDefaultPosition, wxSize(400, 300), style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
		self.listCtrl = wxListCtrl(self, -1, style=wxLC_REPORT)
		self.itemCount = 0
		self.listCtrl.InsertColumn(0, "Time")
		self.listCtrl.InsertColumn(1, "Error Message")
		self.listCtrl.SetColumnWidth(0, 100)
		self.listCtrl.SetColumnWidth(1, 280)

		self.saveBtn = wxButton(self, wxID_SAVE)
		self.clearBtn = wxButton(self, -1, _("Clear"))

		mySizer = wxBoxSizer(wxVERTICAL)
		mySizer.Add(self.listCtrl, 1, wxEXPAND | wxALL, 4)

		btnSizer = wxBoxSizer(wxHORIZONTAL)
		btnSizer.Add(self.clearBtn, 0, wxALL, 4)
		btnSizer.Add((1,1), 1, wxEXPAND)
		btnSizer.Add(self.saveBtn, 0, wxALL, 4)
		mySizer.Add(btnSizer, 0, wxEXPAND)
		self.SetSizer(mySizer)
		self.Layout()

		EVT_BUTTON(self, self.clearBtn.GetId(), self.OnClear)
		EVT_BUTTON(self, self.saveBtn.GetId(), self.OnSave)

		self.LoadErrorLog()

	def OnSave(self, evt):
		global appErrorLog
		fileDialog = wxFileDialog(self, _("Save Log File"),"", "errorlog.txt", style=wxSAVE|wxOVERWRITE_PROMPT)
		result = fileDialog.ShowModal() 
		if result == wxID_OK:
			filename = fileDialog.GetPath()
			afile = open(filename, "wb")
			afile.write(appErrorLog.read().encode("utf-8"))
			afile.close()
		fileDialog.Destroy()

	def OnClear(self, evt):
		global appErrorLog
		appErrorLog.clear()
		self.LoadErrorLog()


	def LoadErrorLog(self):
		global appErrorLog
		self.listCtrl.DeleteAllItems()
		errorList = appErrorLog.read().split("\n")
		for err in errorList:
			if err != "":
				errArray = err.split(appErrorLog.separator)
				self.listCtrl.InsertStringItem(self.itemCount, errArray[0])
				self.listCtrl.SetStringItem(self.itemCount, 1, errArray[1])
				self.itemCount += 1

