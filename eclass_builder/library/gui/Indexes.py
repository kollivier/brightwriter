import wx
import wx.lib.sized_controls as sc

class IndexList(sc.SizedPanel):
    def __init__(self, parent, id, indexList=[]):
        sc.SizedPanel.__init__(self, parent, id)
        