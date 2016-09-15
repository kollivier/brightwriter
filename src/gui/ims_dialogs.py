import wx
import wx.lib.sized_controls as sc

class IMSCleanUpDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__(self, *args, **kwargs)
        
        pane = self.GetContentsPane()
        
        title = wx.StaticText(pane, -1, _("References to Unused Files in Project"))
        boldfont = title.GetFont()
        boldfont.SetWeight(wx.FONTWEIGHT_BOLD)
        boldfont.SetPointSize(boldfont.GetPointSize() + 4)
        title.SetFont(boldfont)
        
        wx.StaticText(pane, -1, _("The following files are not being referenced by any page in your module.\nIt is recommended that these references be removed to avoid problems displaying the module\nin certain learning management systems. Unused Files will be moved to an 'Unused files' folder.\nWould you like to do this now?"))
        
        self.filelist = wx.TextCtrl(pane, -1, "", size=(-1, 160), style=wx.TE_MULTILINE)
        self.filelist.SetSizerProps(expand=True, proportion=1)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.YES | wx.NO | wx.CANCEL))
        
        self.Fit()
        
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=wx.ID_NO)
        
    def OnButton(self, event):
        self.EndModal(event.GetId())
