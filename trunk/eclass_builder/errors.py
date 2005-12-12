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
		#get traceback if available
		tb = ""
		try:
			import traceback
			type, value, trace = sys.exc_info()
			list = traceback.format_tb(trace) + ["\n"] + traceback.format_exception_only(type, value)
			tb = string.join(list, "")
		except:
			pass

		message = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + self.separator + message + self.separator + tb + self.separator
		utils.LogFile.write(self, message)

appErrorLog = AppErrorLog()

class ErrorLogViewer(wxDialog):
	def __init__(self, parent=None):
		wxDialog.__init__(self, parent, -1, _("Error log viewer"), wxDefaultPosition, wxSize(400, 300), style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
		self.listCtrl = wxListCtrl(self, -1, style=wxLC_REPORT)
		self.lblDetails = wxStaticText(self, -1, _("Error Details"))
		self.details = wxTextCtrl(self, -1, style=wxTE_MULTILINE)
		self.itemCount = 0
		self.selItem = None
		self.listCtrl.InsertColumn(0, "Time")
		self.listCtrl.InsertColumn(1, "Error Message")
		self.listCtrl.SetColumnWidth(0, 100)
		self.listCtrl.SetColumnWidth(1, 280)

		self.saveBtn = wxButton(self, wxID_SAVE)
		self.clearBtn = wxButton(self, -1, _("Clear"))

		mySizer = wxBoxSizer(wxVERTICAL)
		mySizer.Add(self.listCtrl, 1, wxEXPAND | wxALL, 4)
		mySizer.Add(self.lblDetails, 0, wxLEFT | wxRIGHT, 6)
		mySizer.Add(self.details, 1, wxEXPAND | wxALL, 4)

		btnSizer = wxBoxSizer(wxHORIZONTAL)
		btnSizer.Add(self.clearBtn, 0, wxALL, 4)
		btnSizer.Add((1,1), 1, wxEXPAND)
		btnSizer.Add(self.saveBtn, 0, wxALL, 4)
		mySizer.Add(btnSizer, 0, wxEXPAND)
		self.SetSizer(mySizer)
		self.Layout()

		EVT_BUTTON(self, self.clearBtn.GetId(), self.OnClear)
		EVT_BUTTON(self, self.saveBtn.GetId(), self.OnSave)
		#EVT_LEFT_DCLICK(self, self.listCtrl.GetId(), self.OnDblClick)
		EVT_LIST_ITEM_SELECTED(self, self.listCtrl.GetId(), self.OnSelection)

		self.LoadErrorLog()

	def OnSelection(self, evt):
		self.details.SetValue(self.errList[self.listCtrl.GetItemData(evt.m_itemIndex)][2])

#	def OnDblClick(self, evt):
#		wxMessageBox(self.

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
		self.details.SetValue("")

	def LoadErrorLog(self):
		global appErrorLog
		self.listCtrl.DeleteAllItems()
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

