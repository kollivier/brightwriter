import string, sys, os
import wx
import wx.lib.sized_controls as sc
#import wx.lib.hyperlink as hl
import version

import settings

rootdir = os.path.join(os.path.dirname(__file__), "..")


class EClassAboutDialog(sc.SizedDialog):
    def __init__(self, parent):
        sc.SizedDialog.__init__ (self, parent, -1, _("About %(appname)s") + {"appname": settings.app_name}, wx.Point(100,100), size=(300, -1))
        self.parent = parent
        
        panel = self.GetContentsPane()
        
        icon = wx.StaticBitmap(panel, -1, wx.Bitmap(os.path.join(rootdir, "icons", "eclass_builder.png")))
        icon.SetSizerProps(halign="center")
        
        app_name = wx.StaticText(panel, -1, settings.app_name)
        app_name.SetSizerProps(halign="center")
        name_font = app_name.GetFont()
        name_font.SetWeight(wx.FONTWEIGHT_BOLD)
        app_name.SetFont(name_font)

        app_version = wx.StaticText(panel, -1, version.asString())
        app_version.SetSizerProps(halign="center")
        
        # app_copyright = wx.StaticText(panel, -1, "Copyright 2002-2010 Tulane University")
        # app_copyright.SetSizerProps(halign="center")
        
        # app_license = wx.StaticText(panel, -1, "This program is BSD licensed")
        # app_license.SetSizerProps(halign="center")
        
        # acknowledgements = wx.StaticText(panel, -1, "Thanks and Acknowledgements")
        # acknowledgements.SetSizerProps(halign="center")
        # ack_font = acknowledgements.GetFont()
        # ack_font.SetWeight(wx.FONTWEIGHT_BOLD)
        # acknowledgements.SetFont(ack_font)
        
        #wxpy_link = hl.HyperLinkCtrl(panel, -1, "Built with wxPython", URL="http://www.wxpython.org")
        #wxpy_link.SetSizerProps(halign="center")
        
        #fatcow_link = hl.HyperLinkCtrl(panel, -1, "EClass.Builder uses FatCow free icons", URL="http://www.fatcow.com/free-icons/")
        #fatcow_link.SetSizerProps(halign="center")

        #program_icon = hl.HyperLinkCtrl(panel, -1, "EClass.Builder icon created from iconaholic.com icons", URL="http://www.iconaholic.com/")
