import wx
import wx.lib.filebrowsebutton as filebrowse
import persistence
import wx.lib.sized_controls as sc

class LibSettingsPanel(sc.SizedPanel):
    def __init__(self, *args, **kwargs):
        sc.SizedPanel.__init__(self, *args, **kwargs)
        
        wx.StaticText(self, -1, _("Index Directory"))
        self.indexChooser = filebrowse.DirBrowseButton(
            self, -1, size=(300, -1), labelText="")
        self.indexChooser.SetSizerProps(expand=True)
            
        wx.StaticText(self, -1, _("Contents Directory"))
        self.contentsChooser = filebrowse.DirBrowseButton(
            self, -1, size=(300, -1), labelText="")
        self.contentsChooser.SetSizerProps(expand=True)
        
class LibSettingsDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        indexDir = ""
        contentsDir = ""
        
        if (kwargs.has_key('indexDir')):
            indexDir = kwargs['indexDir']
            del kwargs['indexDir']
        
        if (kwargs.has_key('contentsDir')):
            contentsDir = kwargs['contentsDir']
            del kwargs['contentsDir']
            
        sc.SizedDialog.__init__(self, *args, **kwargs)
        
        pane = self.GetContentsPane()
        
        self.settingsPane = LibSettingsPanel(pane, -1)
        self.settingsPane.SetSizerProps(expand=True)
        
        self.settingsPane.indexChooser.SetValue(indexDir)
        self.settingsPane.contentsChooser.SetValue(contentsDir)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL) )
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.Fit()
        
        self.LoadState("LibSettingsDialog")
        
    def OnClose(self, evt):
        self.SaveState("LibSettingsDialog")
        
    def GetIndexDir(self):
        return self.settingsPane.indexChooser.GetValue()
        
    def GetContentsDir(self):
        return self.settingsPane.contentsChooser.GetValue()