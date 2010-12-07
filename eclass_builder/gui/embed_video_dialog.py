import __builtin__

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
        self.mp4_text = filebrowse.FileBrowseButton(video_panel, -1, labelText="")
        self.mp4_text.SetSizerProps(expand=True)
        
        wx.StaticText(video_panel, -1, _("Poster Image")).SetSizerProps(halign="right")
        self.poster_text = filebrowse.FileBrowseButton(video_panel, -1, labelText="")
        self.poster_text.SetSizerProps(expand=True)

        self.ogg_label = wx.StaticText(video_panel, -1, "OGG Video")
        self.ogg_label.SetSizerProps(halign="right")
        self.ogg_text = filebrowse.FileBrowseButton(video_panel, -1, labelText="")
        self.ogg_text.SetSizerProps(expand=True)
        
        self.http_streaming_check = wx.CheckBox(panel, -1, _("Use HTTP Streaming (requires server support)"))
        self.http_streaming_check.Enable(False)

        wx.StaticText(panel, -1, _("Choose video player to embed:"))
        self.jwplayer_radio = wx.RadioButton(panel, -1, _("(Recommended) Use Free JW Player. I agree this is for non-commercial purposes\nand I agree to the JW Player license."), style=wx.RB_GROUP)
        self.html5video_radio = wx.RadioButton(panel, -1, _("Use HTML5 video support. (Must supply OGV file for Firefox support.)"))
        
        self.html5video_radio.SetValue(True)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        self.Fit()
        
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadio)
    
        
    def OnRadio(self, event):
        if event.GetId() == self.jwplayer_radio.GetId():
            self.useJWPlayer = True
            print "radio button %d selected" % event.GetId()
            self.ogg_label.Enable(False)
            self.ogg_text.Enable(False)
            self.http_streaming_check.Enable()
        else:
            self.useJWPlayer = False
            self.ogg_label.Enable()
            self.ogg_text.Enable()
            self.http_streaming_check.Enable(False)
            
