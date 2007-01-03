import wx
#import wxaddons.persistence
import wxaddons.sized_controls as sc
import  wx.lib.filebrowsebutton as filebrowse

class NewLibraryDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__(self, *args, **kwargs)
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        
        wx.StaticText(pane, -1, _("Library Name"))
        self.txtName = wx.TextCtrl(pane, -1, "")
        self.txtName.SetSizerProps(expand=True, proportion=1)
        self.txtName.SetFocus()
        
        wx.StaticText(pane, -1, _("Contents Directory"))
        self.txtDir = filebrowse.DirBrowseButton(
            pane, -1, labelText="")
        self.txtDir.SetSizerProps(expand=True, proportion=1)
        self.txtDir.MinSize = (400, -1)
            
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.CentreOnScreen()
        self.Fit()
        
    def GetName(self):
        return self.txtName.GetValue()
        
    def GetContentsDir(self):
        return self.txtDir.GetValue()