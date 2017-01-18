import wx
import persistence
import wx.lib.sized_controls as sc
import tasks
import string, os

class ActivityList(wx.ListBox):
    
    def OnGetItem(self, n):
        numTasks = len(tasks.activeTasks)
        if numTasks > 0 and numTasks > n:
            item = tasks.activeTasks[n]
            finished = not item.isAlive()
            atime = item.elapsedTime()
            name = item.taskRunner.name
            if not finished:
                return "<h4>%s</h4><br>Time: %s" % (name, atime)
            if item.taskRunner.errorOccurred():
                return "<h4>Error: %s</h4>" % (name)
        
        return ""

class ActivityMonitor(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Activity Monitor"), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        self.taskList = ActivityList(pane, -1)
        #self.taskList.SetItemCount(5)
        self.taskList.SetSizerProp("proportion", 1)
        self.taskList.SetSizerProp("expand", "true")
        
        self.details = wx.Button(pane, -1, _("Task Log"))
        self.Bind(wx.EVT_BUTTON, self.OnDetailsClick, self.details)
        self.Fit()
        self.SetMinSize(self.GetSize())
        
    def OnDetailsClick(self, event):
        sel = self.taskList.GetSelection()
        if sel >= 0 and sel < len(tasks.activeTasks):
            item = tasks.activeTasks[sel]
            job = item.tasks[0].activeJob()
            if job:
                logfile = os.path.join(job.LOGBASE, job.label)
                print `logfile`
                if os.path.exists(logfile):
                    print "opening..."
                    text = utils.openFile(utils.escapeFilename(logfile), "r").read()
                    dlg = wx.lib.dialogs.ScrolledMessageDialog(self, text, _("Log Contents"))
                    dlg.ShowModal()
        
    def OnTimerFired(self, event):
        # this should fire OnGetItem and refresh the task list
        self.taskList.RefreshAll()
        
