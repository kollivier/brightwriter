import types, string
import wx
import wx.grid
import wxaddons.persistence
import wxaddons.sized_controls as sc
import index

# I'd like to move towards making these more dynamic, to reduce hardcoded
# initialization, etc. That's what the below methods are for.

def getName():
    return _("Properties")

def createFrame(parent, id=-1):
    return PropsMiniFrame(parent, id, getName(), style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX)

def Init():
    pass

class PropsView(sc.SizedPanel):
    def __init__(self, *args, **kwargs):
        sc.SizedPanel.__init__(self, *args, **kwargs)
        
        # used to track if an actual change was made during an edit
        self.oldValue = ""
        
        self.grid = wx.grid.Grid(self, -1)
        self.grid.CreateGrid(0, 2)
        self.grid.EnableGridLines(False)
        self.grid.EnableEditing(True)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelSize(0)
        
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        font = self.grid.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        attr.SetFont(font)
        attr.SetBackgroundColour(wx.LIGHT_GREY)
        attr.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        self.grid.SetColAttr(0, attr)

        self.grid.SetSizerProps(expand=True, proportion=1)
        
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnEditorHidden, self.grid)
        self.Bind(wx.EVT_SIZE, self.OnSize)
    
    def OnEditorShown(self, event):
        self.oldValue = self.grid.GetCellValue(event.GetRow(), 1)
        event.Skip()
        
    def OnSize(self, event):
        width = event.GetSize().GetWidth()
        freespace = width - self.grid.GetColSize(0)
        self.grid.SetColSize(1, freespace - 20)
        event.Skip()
        
    def OnEditorHidden(self, event):
        #print "Editor for cell (%d, %d) hidden." % (event.GetCol(), event.GetRow())
        field = self.grid.GetCellValue(event.GetRow(), 0)
        value = self.grid.GetCellValue(event.GetRow(), 1)
        value = value.split(",")
        if value != self.oldValue:
            mainFrame = wx.GetApp().GetTopWindow()
            if mainFrame:
                mainFrame.updateMetadataForSelectedFiles(field, value)
        
    def loadProps(self, props={}, allprops=[]):
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())
        counter = 0
        for prop in allprops:
            if not prop in index.internalMetadata:
                self.grid.InsertRows(counter, 1)
                self.grid.SetCellValue(counter, 0, prop)
                if props and props.has_key(prop):
                    value = props[prop]
                    if not isinstance(value, types.StringTypes):
                        value = string.join(value, ",")
                    self.grid.SetCellValue(counter, 1, value)    
        self.grid.AutoSizeColumn(0)
        width = self.GetSize().GetWidth()
        freespace = width - self.grid.GetColSize(0)
        self.grid.SetColSize(1, freespace - 20)
    
        
class PropsMiniFrame(wx.MiniFrame):
    def __init__(self, *args, **kwargs):
        wx.MiniFrame.__init__(self, *args, **kwargs)
        self.props = PropsView(self, -1) 
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnClose(self, event):
        self.Hide()