import sys, os, string
import settings
import wx
import wx.lib.sized_controls as sc

class EditListBox(sc.SizedPanel):
    def __init__(self, *args, **kwargs):
        sc.SizedPanel.__init__(self, *args, **kwargs)
        
        self.listbox = wx.ListBox(self, -1)
        self.listbox.SetSizerProps(expand=True, proportion=1)
        
        icnNew = wx.Bitmap(os.path.join(settings.AppDir, "icons", "plus16.gif"), wx.BITMAP_TYPE_GIF)
        icnCopy = wx.Bitmap(os.path.join(settings.AppDir, "icons", "copy16.gif"), wx.BITMAP_TYPE_GIF)
        icnDelete = wx.Bitmap(os.path.join(settings.AppDir, "icons", "minus16.gif"), wx.BITMAP_TYPE_GIF)

        themeListBtnPane = sc.SizedPanel(self, -1)
        themeListBtnPane.SetSizerType("horizontal")
        themeListBtnPane.SetSizerProps(align="center")
        self.btnNew = wx.BitmapButton(themeListBtnPane, -1, icnNew)
        self.btnCopy = wx.BitmapButton(themeListBtnPane, -1, icnCopy)
        self.btnDelete = wx.BitmapButton(themeListBtnPane, -1, icnDelete)
        
    def GetListBox(self):
        return self.listbox
        
    def GetNewButton(self):
        return self.btnNew
        
    def GetCopyButton(self):
        return self.btnCopy
        
    def GetDeleteButton(self):
        return self.btnDelete
        
    def SetChoices(self, choices):
        self.listbox.Set(choices)