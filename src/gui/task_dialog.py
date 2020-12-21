import logging
import threading

import wx
import wx.lib.newevent
import wx.lib.sized_controls as sc

# create event type
wxLogEvent, EVT_WX_LOG_EVENT = wx.lib.newevent.NewEvent()
wxDoneEvent, EVT_WX_DONE_EVENT = wx.lib.newevent.NewEvent()


class wxLogHandler(logging.Handler):
    """
    A handler class which sends log strings to a wx object
    """
    def __init__(self, wx_target=None):
        """
        Initialize the handler
        @param wxDest: the destination object to post the event to
        @type wxDest: wx.Window
        """
        logging.Handler.__init__(self)
        self.wx_target = wx_target
        self.level = logging.DEBUG

    def flush(self):
        """
        does nothing for this handler
        """


    def emit(self, record):
        """
        Emit a record.

        """
        try:
            msg = self.format(record)
            evt = wxLogEvent(message=msg, levelname=record.levelname)
            wx.PostEvent(self.wx_target, evt)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class TaskDialog(sc.SizedDialog):
    def __init__(self, task_func, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Activity Monitor"),
                                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        pane = self.GetContentsPane()

        self.task_func = task_func
        self.task_details = wx.TextCtrl(pane, -1, style=wx.TE_MULTILINE)
        self.task_details.SetSizerProps(proportion=1, expand=True)
        self.task_details.SetMinSize((500, 300))
        self.task_button = wx.Button(pane, -1, _("Start"))
        self.task_button.Bind(wx.EVT_BUTTON, self.OnTaskButton)

        self.task_thread = None

        self.Bind(EVT_WX_LOG_EVENT, self.OnLogEvent)
        self.Bind(EVT_WX_DONE_EVENT, self.OnTaskDone)

        self.Fit()
        self.SetMinSize(self.GetSize())

        # self.timer = wx.Timer(self, -1)
        # self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        # self.timer.Start(100)  # 10ms timer

    def OnTaskButton(self, event):
        if not self.task_thread and self.task_button.GetLabelText() == _("Start"):
            self.task_thread = threading.Thread(target=self.task_func)
            self.task_thread.start()
            self.task_button.SetLabelText(_("Stop"))
        elif self.task_button.GetLabelText() == _("Stop"):
            self.task_thread.raise_exception()
            self.task_button.SetLabelText(_("Close"))
        else:
            self.EndModal(wx.ID_CANCEL)

    def OnTaskDone(self, event):
        self.task_button.SetLabelText(_("Close"))

    def OnLogEvent(self,event):
        '''
        Add event.message to text window
        '''
        msg = event.message.strip("\r")+"\n"
        self.task_details.AppendText(msg) # or whatevery
        event.Skip()
