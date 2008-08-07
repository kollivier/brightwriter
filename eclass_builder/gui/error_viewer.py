import sys, string, os
import utils
import guiutils
import time

import wx
import persistence
import wx.lib.sized_controls as sc
import autolist
import errors
import traceback
import xmlrpc
import version

appErrorLog = errors.appErrorLog

class ErrorDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("%s Fatal Error" % wx.GetApp().GetAppName()), wx.DefaultPosition, wx.Size(500, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        
        wx.StaticText(pane, -1, _("An Unexpected Error Has Occurred in %s" % wx.GetApp().GetAppName()))
        wx.StaticText(pane, -1, _("If you click on '%s', it will send only the error information\nto the project. This is helpful for us to diagnose any problems that may occur.") % _("Send Error Report"))
        self.detailsButton = wx.Button(pane, -1, _("Show Details"))

        self.detailsText = wx.TextCtrl(pane, -1, size=(-1,300), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.detailsText.Show(False)
        pane.GetSizer().Detach(self.detailsText)
        
        line = wx.StaticLine(pane, -1)
        line.SetSizerProps(expand=True)
        
        btnPanel = sc.SizedPanel(pane)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(expand=True, proportion=1)
        spacer = sc.SizedPanel(btnPanel, -1)
        spacer.SetSizerProps({"expand":True, "proportion":1})
        
        self.sendBtn = wx.Button(btnPanel, -1, _("Send Error Report"))
        
        self.Bind(wx.EVT_BUTTON, self.OnPaneChanged, self.detailsButton)
        self.Bind(wx.EVT_BUTTON, self.OnSubmitReport, self.sendBtn)
        
        self.Fit()
        
    def OnSubmitReport(self, event):
        server = xmlrpc.getEClassXMLRPCServer()
        result = server.sendError("Anonymous", "", "", self.detailsText.GetValue(), version.asString())
        if result == "success":
            wx.MessageBox(_("Error report sent successfully! Thanks!"))
            self.Destroy()
        else:
            wx.MessageBox(_("Unable to send error report. Error details can also be emailed to kevino@tulane.edu."))
            
    def OnPaneChanged(self, event):
        if not self.detailsText.IsShown(): 
            self.detailsText.Show()
            self.detailsButton.SetLabel(_("Hide Details"))
            self.GetContentsPane().GetSizer().Insert(4, self.detailsText, 0, wx.EXPAND)
            self.Layout()
            self.Fit()
        else:
            self.detailsText.Show(False)
            self.detailsButton.SetLabel(_("Show Details"))
            self.GetContentsPane().GetSizer().Detach(self.detailsText)
            self.Layout()
            self.Fit()
        
def guiExceptionHook(exctype, value, trace):
    errorText = errors.print_exc_plus(exctype, value, trace)
    
    print errorText
    
    if not wx.GetApp():
        app = wx.PySimpleApp()
        app.MainLoop()
    
    error = ErrorDialog()
    error.detailsText.WriteText(errorText)
    error.Centre()
    error.ShowModal()
    
    app = wx.GetApp()
    if app:
        app.ExitMainLoop()
    sys.exit(1)

class ErrorLogViewer(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Error log viewer"), wx.DefaultPosition, wx.Size(420, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        self.listCtrl = autolist.AutoSizeListCtrl(pane, -1, style=wx.LC_REPORT)
        self.listCtrl.SetSizerProps(expand=True, proportion=1) 
        
        self.lblDetails = wx.StaticText(pane, -1, _("Error Details"))
        self.details = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
        self.details.SetSizerProps(expand=True, proportion=1)
        
        self.itemCount = 0
        self.selItem = None
        self.listCtrl.InsertColumn(0, _("Time"))
        self.listCtrl.InsertColumn(1, _("Error Message"))
        self.listCtrl.SetColumnWidth(0, 100)
        self.listCtrl.SetColumnWidth(1, 280)
        self.SetMaxSize((-1, 700))

        btnpane = sc.SizedPanel(pane, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True) 
        
        self.saveBtn = wx.Button(btnpane, wx.ID_SAVE)
        spacer = sc.SizedPanel(btnpane, -1)
        spacer.SetSizerProps(expand=True, proportion=1)

        self.clearBtn = wx.Button(btnpane, -1, _("Clear"))

        wx.EVT_BUTTON(self, self.clearBtn.GetId(), self.OnClear)
        wx.EVT_BUTTON(self, self.saveBtn.GetId(), self.OnSave)
        #EVT_LEFT_DCLICK(self, self.listCtrl.GetId(), self.OnDblClick)
        wx.EVT_LIST_ITEM_SELECTED(self, self.listCtrl.GetId(), self.OnSelection)

        self.LoadErrorLog()
        self.Fit()
        self.SetMinSize(self.GetSize())
        wx.EVT_ACTIVATE(self, self.OnActivate)

    def OnSelection(self, evt):
        self.details.SetValue(self.errList[self.listCtrl.GetItemData(evt.m_itemIndex)][2])
        
    def OnActivate(self, evt):
        self.LoadErrorLog()

#   def OnDblClick(self, evt):
#       wxMessageBox(self.

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
