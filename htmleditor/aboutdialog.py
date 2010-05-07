import os

import wx
import wx.lib.hyperlink as hl
import wx.lib.sized_controls as sc

class AboutDialog(sc.SizedFrame):
    def __init__(self, *a, **k):
        sc.SizedFrame.__init__(self, *a, **k)
        
        icondir = os.path.join("htmledit", "icons")
        icon = wx.Image(os.path.join(icondir, "eclass_htmledit.ico"), wx.BITMAP_TYPE_ICO)
        
        pane = self.GetContentsPane()
        wx.StaticBitmap(pane, -1, icon.ConvertToBitmap()).SetSizerProps(align="center")
        wx.StaticText(pane, -1, wx.GetApp().GetAppName()).SetSizerProps(align="center")
        
        wx.StaticText(pane, -1, "%s icon provided by:" % wx.GetApp().GetAppName()).SetSizerProps(align="center")
        hl.HyperLinkCtrl(pane, -1, "Iconaholic", URL="http://www.iconaholic.com").SetSizerProps(align="center")
        
        wx.StaticText(pane, -1, "Other icons provided by:").SetSizerProps(align="center")
        hl.HyperLinkCtrl(pane, -1, "The Tango Project", URL="http://tango.freedesktop.org").SetSizerProps(align="center")
        hl.HyperLinkCtrl(pane, -1, "FatCow", URL="http://www.fatcow.com/free-icons").SetSizerProps(align="center")

        self.Fit()
        self.SetSize((360, self.GetSize().y))
        
        if "__WXMAC__" in wx.PlatformInfo:
            self.CentreOnScreen()
        else:
            self.CentreOnParent()
