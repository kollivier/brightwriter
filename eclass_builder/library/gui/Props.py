import wx
import wx.grid
#import wxaddons.persistence
import wxaddons.sized_controls as sc

class PropsPanel(sc.SizedPanel):
    def __init__(self, *args, **kwargs):
        sc.SizedPanel.__init__(self, *args, **kwargs)
        
        self.grid = wx.grid.Grid(self, -1)
        self.grid.EnableGridLines(False)
        self.grid.SetSizerProps(expand=True, proportion=1)
        
class PropsMiniFrame(wx.MiniFrame):
    def __init__(self, *args, **kwargs):
        wx.MiniFrame.__init__(self, *args, **kwargs)
        self.props = props.PropsPanel(self, -1) 