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
        self.settingsPane.SetSizerProps(expand=True, proportion=1)
        
        self.settingsPane.indexChooser.SetValue(indexDir)
        self.settingsPane.contentsChooser.SetValue(contentsDir)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL) )
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        okbutton = self.FindWindowById(wx.ID_OK)
        okbutton.Bind(wx.EVT_BUTTON, self.OnButton)
        cancelbutton = self.FindWindowById(wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=wx.CANCEL)
        
        self.Fit()
        self.SetMinSize(self.GetSize())
        
        self.LoadState("LibSettingsDialog")
        
    def Takedown(self):
        self.SaveState("LibSettingsDialog")
                
    def OnButton(self, evt):
        self.Takedown()
        evt.Skip()
        
    def OnClose(self, evt):
        self.Takedown()
        evt.Skip()
        
    def GetIndexDir(self):
        return self.settingsPane.indexChooser.GetValue()
        
    def GetContentsDir(self):
        return self.settingsPane.contentsChooser.GetValue()