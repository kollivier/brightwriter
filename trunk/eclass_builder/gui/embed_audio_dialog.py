import __builtin__

import string 

import wx
import wx.lib.sized_controls as sc

import  wx.lib.filebrowsebutton as filebrowse

class EmbedAudioDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        
        self.useJWPlayer = False
        
        panel = self.GetContentsPane()
        audio_panel = sc.SizedPanel(panel, -1)
        audio_panel.SetSizerProps(expand=True, proportion=1)
        
        audio_panel.SetSizerType("form")
        
        wx.StaticText(audio_panel, -1, "MP3 Audio").SetSizerProps(halign="right")
        self.mp3_text = filebrowse.FileBrowseButton(audio_panel, -1, labelText="", fileMask="MP3 Audio (*.mp3)|*.mp3")
        self.mp3_text.SetSizerProps(expand=True)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        self.Fit()
