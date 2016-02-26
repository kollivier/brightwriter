import logging
import os
import sys
import time
import traceback

import utils
import guiutils

import wx
import wx.lib.sized_controls as sc

import autolist
import errors
import settings
import version

from rest import brightsparc

class ErrorDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("%s: Unexpected Error" % wx.GetApp().GetAppName()), wx.DefaultPosition, wx.Size(500, 340), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        
        
        title = wx.StaticText(pane, -1, _("An Unexpected Error Has Occurred in %s" % wx.GetApp().GetAppName()))
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(font.GetPointSize() + 2)
        title.SetFont(font)
        # wx.StaticText(pane, -1, _("If you click on '%s', it will send the error report below\nto the project. This is helpful for us to diagnose any problems that may occur.") % _("Send Error Report"))

        # options = wx.StaticText(pane, -1, _("Optional"))
        # options.SetFont(font)
        # wx.StaticText(pane, -1, _("Please enter your email so we can contact you with updates or questions."))
        
        # infoPanel = sc.SizedPanel(pane, -1)
        # infoPanel.SetSizerType("horizontal")
        # infoPanel.SetSizerProps(expand=True)
        
        # wx.StaticText(infoPanel, -1, _("Name"))
        # self.nameText = wx.TextCtrl(infoPanel, -1)
        # self.nameText.SetSizerProps(expand=True, proportion=1)
        
        # wx.StaticText(infoPanel, -1, _("Email"))
        # self.emailText = wx.TextCtrl(infoPanel, -1)
        # self.emailText.SetSizerProps(expand=True, proportion=1)
        
        wx.StaticText(pane, -1, _("Please describe the events leading to the crash."))
        self.descriptionText = wx.TextCtrl(pane, -1, size=(-1, 100), style=wx.TE_MULTILINE)
        self.descriptionText.SetSizerProps(expand=True, proportion=1)

        self.detailsButton = wx.Button(pane, -1, _("Show Details"))

        self.detailsText = wx.TextCtrl(pane, -1, size=(-1,300), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.detailsText.SetSizerProps(expand=True)
        self.detailsText.Show(False)
        pane.GetSizer().Hide(self.detailsText)
        
        line = wx.StaticLine(pane, -1)
        line.SetSizerProps(expand=True)
        
        btnPanel = sc.SizedPanel(pane)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(expand=True)
        spacer = sc.SizedPanel(btnPanel, -1)
        spacer.SetSizerProps(expand=True, proportion=1)
        
        wx.Button(btnPanel, wx.ID_CANCEL, "Cancel")
        self.sendBtn = wx.Button(btnPanel, wx.ID_OK, _("Send Error Report"))
        
        self.Bind(wx.EVT_BUTTON, self.OnPaneChanged, self.detailsButton)
        self.Bind(wx.EVT_BUTTON, self.OnSubmitReport, self.sendBtn)
        
        self.Fit()
        
    def OnSubmitReport(self, event):
        self.EndModal(wx.ID_OK)
            
    def OnPaneChanged(self, event):
        if not self.detailsText.IsShown(): 
            self.detailsText.Show()
            self.detailsButton.SetLabel(_("Hide Details"))
            self.GetContentsPane().GetSizer().Show(self.detailsText)
            self.Layout()
            self.Fit()
        else:
            self.detailsText.Show(False)
            self.detailsButton.SetLabel(_("Show Details"))
            self.GetContentsPane().GetSizer().Hide(self.detailsText)
            self.Layout()
            self.Fit()
        
def guiExceptionHook(exctype, value, trace):
    errorText = errors.get_platform_info()
    errorText += errors.print_exc_plus(exctype, value, trace)

    logging.error(errorText)
    
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
        description = ""
        result = error.ShowModal()
        if result == wx.ID_CANCEL:
            description = "Cancel selected"

        if result == wx.ID_OK:
            logging.info("result = wx.ID_OK")
            description = error.descriptionText.GetValue()

        try:
            server = brightsparc.BrightSparcClient()
            log = ""
            if os.path.exists(settings.logfile):
                log = open(settings.logfile, "r").read()
                logging.info("Added log to report.")

            report = {
                "version_major": version.major,
                "version_minor": version.minor,
                "version_revision": version.release,
                "version_build": version.build_number,
                "description": description,
                "error": errorText,
                "application_log": log
            }

            logging.info("posting error report")
            server.post_error_report(report)
            success = True
        except Exception, e:
            import traceback
            logging.error(traceback.format_exc(e))
            success = False

        error.Destroy()

        if result == wx.ID_OK:
            logging.info("OK clicked, reporting error submission state.")
            if success:
                wx.MessageBox(_("Error report sent successfully! Thanks!"))
            else:
                wx.MessageBox(_("Unable to send error report. Error details can also be emailed to kevin@kosoftworks.com."))
        
        # wx.GetApp().ExitMainLoop()

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
        
