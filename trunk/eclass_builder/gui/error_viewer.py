import sys, string, os
import utils
import guiutils
import time

import wx
import wx.lib.sized_controls as sc

import autolist
import errors
import persistence
import settings
import traceback
import version
import xmlrpc

class ErrorDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("%s - Error Occurred" % wx.GetApp().GetAppName()), wx.DefaultPosition, wx.Size(500, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        
        
        title = wx.StaticText(pane, -1, _("An Unexpected Error Has Occurred in %s" % wx.GetApp().GetAppName()))
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(font.GetPointSize() + 2)
        title.SetFont(font)
        wx.StaticText(pane, -1, _("If you click on '%s', it will send only the error information listed below\nto the project. This is helpful for us to diagnose any problems that may occur.") % _("Send Error Report"))

        options = wx.StaticText(pane, -1, _("Optional"))
        options.SetFont(font)
        wx.StaticText(pane, -1, _("If you do not mind being contacted for more details on the problem, please enter your name and email below.\nThis information will not be sold or used in any way other than to help track and fix this bug."))
        
        infoPanel = sc.SizedPanel(pane, -1)
        infoPanel.SetSizerType("horizontal")
        infoPanel.SetSizerProps(expand=True)
        
        wx.StaticText(infoPanel, -1, _("Name"))
        self.nameText = wx.TextCtrl(infoPanel, -1)
        self.nameText.SetSizerProps(expand=True, proportion=1)
        
        wx.StaticText(infoPanel, -1, _("Email"))
        self.emailText = wx.TextCtrl(infoPanel, -1)
        self.emailText.SetSizerProps(expand=True, proportion=1)
        
        wx.StaticText(pane, -1, _("Please describe what you were doing at the time of the crash."))
        self.descriptionText = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
        self.descriptionText.SetSizerProps(expand=True, proportion=1)

        self.detailsButton = wx.Button(pane, -1, _("Show Details"))

        self.detailsText = wx.TextCtrl(pane, -1, size=(-1,300), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.detailsText.Show(False)
        pane.GetSizer().Detach(self.detailsText)
        
        line = wx.StaticLine(pane, -1)
        line.SetSizerProps(expand=True)
        
        btnPanel = sc.SizedPanel(pane)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(expand=True)
        spacer = sc.SizedPanel(btnPanel, -1)
        spacer.SetSizerProps(expand=True, proportion=1)
        
        self.sendBtn = wx.Button(btnPanel, -1, _("Send Error Report"))
        
        self.Bind(wx.EVT_BUTTON, self.OnPaneChanged, self.detailsButton)
        self.Bind(wx.EVT_BUTTON, self.OnSubmitReport, self.sendBtn)
        
        self.Fit()
        
    def OnSubmitReport(self, event):
        server = xmlrpc.getEClassXMLRPCServer()
        result = server.sendError(self.nameText.GetValue(), self.emailText.GetValue(), self.descriptionText.GetValue(), self.detailsText.GetValue(), version.asString())
        if result == "success":
            wx.MessageBox(_("Error report sent successfully! Thanks!"))
        else:
            wx.MessageBox(_("Unable to send error report. Error details can also be emailed to kevino@tulane.edu."))
        self.EndModal(wx.ID_OK)
            
    def OnPaneChanged(self, event):
        if not self.detailsText.IsShown(): 
            self.detailsText.Show()
            self.detailsButton.SetLabel(_("Hide Details"))
            self.GetContentsPane().GetSizer().Insert(8, self.detailsText, 0, wx.EXPAND)
            self.Layout()
            self.Fit()
        else:
            self.detailsText.Show(False)
            self.detailsButton.SetLabel(_("Show Details"))
            self.GetContentsPane().GetSizer().Detach(self.detailsText)
            self.Layout()
            self.Fit()
        
def guiExceptionHook(exctype, value, trace):    
    errorText = errors.get_platform_info()
    errorText += errors.print_exc_plus(exctype, value, trace)
    
    if not wx.GetApp():
        app = wx.PySimpleApp()
        app.MainLoop()
    
    errorShowing = False
    for win in wx.GetTopLevelWindows():
        if isinstance(win, ErrorDialog):
            errorShowing = True
    
    if not errorShowing:
        error = ErrorDialog()
        error.detailsText.WriteText(errorText)
        error.Centre()
        error.ShowModal()
        error.Destroy()
        wx.GetApp().ExitMainLoop()

class ErrorLogViewer(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Log viewer"), wx.DefaultPosition, wx.Size(420, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        self.listCtrl = autolist.AutoSizeListCtrl(pane, -1, style=wx.LC_REPORT)
        self.listCtrl.SetSizerProps(expand=True, proportion=1) 
        
        #self.lblDetails = wx.StaticText(pane, -1, _("Error Details"))
        #self.details = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
        #self.details.SetSizerProps(expand=True, proportion=1)
        
        self.itemCount = 0
        self.selItem = None
        self.listCtrl.InsertColumn(0, _("Time"))
        self.listCtrl.InsertColumn(1, _("Message"))
        self.listCtrl.SetColumnWidth(0, 100)
        self.listCtrl.SetColumnWidth(1, 280)
        self.SetMaxSize((-1, 700))

        btnpane = sc.SizedPanel(pane, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True) 

        self.LoadErrorLog()
        self.Fit()
        self.SetMinSize(self.GetSize())
        wx.EVT_ACTIVATE(self, self.OnActivate)
        
    def OnActivate(self, evt):
        self.LoadErrorLog()

    def LoadErrorLog(self):
        self.listCtrl.DeleteAllItems()
        self.itemCount = 0
        if settings.logfile:
            errorList = open(settings.logfile, 'r').read().split('\n')
            self.errList = []
            for err in errorList:
                if err != "":
                    errArray = err.split('\t')
                    self.errList.append(errArray)
                    index = self.errList.index(errArray)
                    self.listCtrl.InsertStringItem(self.itemCount, errArray[0])
                    if len(errArray) > 1:
                        self.listCtrl.SetStringItem(self.itemCount, 1, "%s : %s" % (errArray[1], errArray[2]))
                    self.listCtrl.SetItemData(self.itemCount, index)
                    self.itemCount += 1

class PublishErrorLogViewer(sc.SizedDialog):
    def __init__(self, parent=None, errorString=""):
        sc.SizedDialog.__init__(self, parent, -1, _("Publishing Errors"), wx.DefaultPosition, wx.Size(420, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        
        self.textCtrl = wx.TextCtrl(pane, -1, errorString, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textCtrl.SetSizerProps(expand=True, proportion=1)
        
        self.saveButton = wx.Button(pane, -1, _("Save Error Log"))
        self.saveButton.SetSizerProps(halign="right")
        
        self.saveButton.Bind(wx.EVT_BUTTON, self.OnButton)
        
    def OnButton(self, event):
        filedlg = wx.FileDialog(self, _("Save Log File"), wildcard="Text Files (*.txt);*.txt", style=wx.FD_SAVE)
        if filedlg.ShowModal() == wx.ID_OK:
            filename = filedlg.GetPath()
            afile = open(filename, "w")
            afile.write(self.textCtrl.GetValue())
            afile.close()
        
