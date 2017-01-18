import string, sys, os
import wx
import wx.lib.sized_controls as sc
#import wx.lib.hyperlink as hl
import version

import settings

import wxbrowser

class EClassAboutDialog(sc.SizedDialog):
    def __init__(self, parent):
        sc.SizedDialog.__init__ (self, parent, -1, _("About %(appname)s" % {"appname": settings.app_name}), wx.Point(100,100), size=(300, -1), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        
        panel = self.GetContentsPane()
        
        icon = wx.StaticBitmap(panel, -1, wx.Bitmap(os.path.join(settings.AppDir, "icons", "brightwriter.png")))
        icon.SetSizerProps(halign="center")
        
        app_name = wx.StaticText(panel, -1, settings.app_name)
        app_name.SetSizerProps(halign="center")
        name_font = app_name.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        app_name.SetFont(name_font)

        app_version = wx.StaticText(panel, -1, version.asString())
        app_version.SetSizerProps(halign="center")

        app_copyright = wx.StaticText(panel, -1, "Copyright 2010 Tulane University")
        app_copyright.SetSizerProps(halign="center")
        
        app_license = wx.StaticText(panel, -1, "This program is BSD licensed")
        app_license.SetSizerProps(halign="center")

        credits_label = wx.StaticText(panel, -1, _("Credits and Acknowledgments"))
        credits_label.SetSizerProps(halign="center", border=("all", 3))
        label_font = credits_label.GetFont()
        label_font.SetWeight(wx.FONTWEIGHT_BOLD)
        credits_label.SetFont(label_font)

        self.browser = wxbrowser.wxBrowser(panel, -1)
        self.browser.SetSizerProps(expand=True)
        self.browser.browser.SetSizerProps(expand=True, proportion=1)
        self.browser.browser.SetMinSize((400, 100))
        # FIXME: Move this to an html file on disk.
        self.browser.LoadPage(os.path.join(settings.AppDir, "gui", "html", "about.html"))

        self.Fit()
