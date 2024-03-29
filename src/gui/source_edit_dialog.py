from __future__ import absolute_import
import wx
import wx.lib.sized_controls as sc
import wx.stc

from wx.lib.pubsub import pub

from . import sourcedelegate

class SourceEditDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        
        pane = self.GetContentsPane()
        
        self.searchCtrl = wx.SearchCtrl(pane, -1)
        self.searchCtrl.SetSizerProps(expand=True)
        
        self.source = wx.stc.StyledTextCtrl(pane, -1)
        self.source.SetSizerProps(expand=True, proportion=1)
        
        self.isDirty = False

        self.source.SetLexer(wx.stc.STC_LEX_HTML)
        self.source.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "fore:#000000,size:12,face:Arial")
        self.source.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "fore:#000000")
        self.source.StyleSetSpec(wx.stc.STC_H_TAG, "fore:#000099")
        self.source.StyleSetSpec(wx.stc.STC_H_ATTRIBUTE, "fore:#009900")
        self.source.StyleSetSpec(wx.stc.STC_H_VALUE, "fore:#009900")
        self.source.SetProperty("fold.html", "1")
        self.source.SetWrapMode(wx.stc.STC_WRAP_WORD)

        self.sourceDelegate = sourcedelegate.HTMLSourceEditorDelegate(self.source, searchCtrl=self.searchCtrl)
        self.sourceDelegate.RegisterHandlers()
        
        self.searchCtrl.Bind(wx.EVT_TEXT, self.OnDoSearch)
        self.searchCtrl.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
    def OnKeyDown(self, event):
        # FIXME: Figure out why this doesn't fire on Mac
        is_search = event.MetaDown() and event.KeyCode == ord('G')
        searchText = self.searchCtrl.GetValue()
        
        if searchText and is_search:
            pub.sendMessage(('search', 'findnext'), text=searchText)
        else:
            event.Skip()

    def OnDoSearch(self, event):
        # wx bug: event.GetString() doesn't work on Windows
        text = event.GetEventObject().GetValue()
        pub.sendMessage(('search', 'find'), text=text)
        event.Skip()

    def OnSavePointReached(self, event):
        self.isDirty = False
        
    def OnSavePointLeft(self, event):
        self.isDirty = True

    def SetSource(self, html):
        self.source.SetText(html)
        
    def GetSource(self):
        return self.source.GetText()

    
