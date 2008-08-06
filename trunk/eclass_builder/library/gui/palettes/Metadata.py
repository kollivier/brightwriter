import wx
import wx.lib.sized_controls as sc
import persistence

def getName():
    return _("Field Editor")

def createFrame(parent, id=-1):
    return MetadataMiniFrame(parent, id, getName(), style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX)

class MetadataPanel(sc.SizedPanel):
    def __init__(self, *args, **kwargs):
        sc.SizedPanel.__init__(self, *args, **kwargs)
        
        # FIXME: we need to make metadata more intelligent,
        # but this is just a start.
        
        self.fieldList = wx.ListBox(self, -1)
        self.fieldList.SetSizerProps(expand=True, proportion=1)
        
        panel = sc.SizedPanel(self, -1)
        panel.SetSizerType("horizontal")
        
        self.addBtn = wx.Button(panel, -1, _("Add"))
        self.addBtn.SetSizerProps(align="center")
        self.removeBtn = wx.Button(panel, -1, _("Remove"))
        self.removeBtn.SetSizerProps(align="center")
        
    def LoadFields(self, fields):
        self.fieldList.Clear()
        for field in fields:
            self.fieldList.Append(field)
        
    def GetFields(self):
        return self.fieldList.GetStrings()

class MetadataMiniFrame(wx.MiniFrame):
    def __init__(self, *args, **kwargs):
        wx.MiniFrame.__init__(self, *args, **kwargs)
        self.metadata = MetadataPanel(self, -1)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnClose(self, event):
        self.Hide()