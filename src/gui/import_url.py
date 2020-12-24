import wx
import wx.lib.sized_controls as sc


class ImportURLDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Activity Monitor"),
                                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        pane = self.GetContentsPane()

        self.url_ctrl = wx.TextCtrl(pane, -1)
        self.url_ctrl.SetSizerProps(expand=True)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))

        self.Fit()
        self.SetMinSize(self.GetSize())
