import wx
import wx.lib.sized_controls as sc
import wx.stc

import sourcedelegate

class SourceEditDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        
        self.source = wx.stc.StyledTextCtrl(self.GetContentsPane(), -1)
        self.source.SetSizerProps(expand=True, proportion=1)
        
        self.isDirty = False

        self.source.SetLexer(wx.stc.STC_LEX_HTML)
        self.source.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "fore:#000000,size:12,face:Arial")
        self.source.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "fore:#000000")
        self.source.StyleSetSpec(wx.stc.STC_H_TAG, "fore:#000099")
        self.source.StyleSetSpec(wx.stc.STC_H_ATTRIBUTE, "fore:#009900")
        self.source.StyleSetSpec(wx.stc.STC_H_VALUE, "fore:#009900")
        self.source.SetProperty("fold.html", "1")

        self.sourceDelegate = sourcedelegate.HTMLSourceEditorDelegate(self.source)

    def OnSavePointReached(self, event):
        self.isDirty = False
        
    def OnSavePointLeft(self, event):
        self.isDirty = True

    def SetSource(self, html):
        self.source.SetText(html)
        
    def GetSource(self):
        return self.source.GetText()

    
