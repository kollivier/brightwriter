import wx
import wx.stc

import sourcedelegate

class SourceEditDialog(wx.Dialog):
    def __init__(self, *a, **kw):
        wx.Dialog.__init__(self, *a, **kw)
        
        self.source = wx.stc.StyledTextCtrl(self, -1)
        
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

    
