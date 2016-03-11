import __builtin__

import string 

import wx
import wx.lib.sized_controls as sc

import  wx.lib.filebrowsebutton as filebrowse

class EmbedVideoDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        
        self.useJWPlayer = False
        
        panel = self.GetContentsPane()
        video_panel = sc.SizedPanel(panel, -1)
        video_panel.SetSizerProps(expand=True, proportion=1)
        
        video_panel.SetSizerType("form")
        
        wx.StaticText(video_panel, -1, "MP4 Video").SetSizerProps(halign="right")
        self.mp4_text = filebrowse.FileBrowseButton(video_panel, -1, labelText="", fileMask="MP4 Video (*.mp4,*.m4v)|*.mp4;*.m4v")
        self.mp4_text.SetSizerProps(expand=True)
        
        wx.StaticText(video_panel, -1, _("Width")).SetSizerProps(halign="right")
        self.width_text = wx.TextCtrl(video_panel, -1, "", validator=TextValidator(DIGIT_ONLY))
        
        wx.StaticText(video_panel, -1, _("Height")).SetSizerProps(halign="right")
        self.height_text = wx.TextCtrl(video_panel, -1, "", validator=TextValidator(DIGIT_ONLY))
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        self.Fit()    
