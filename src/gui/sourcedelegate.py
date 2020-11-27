from __future__ import absolute_import
import wx
from wx.lib.pubsub import pub

from .editactions import *

class STCFindReplaceController(wx.EvtHandler):
    '''
    This class controls Find and Replace behaviors for wxSTC, e.g. adding
    "move to selection" behavior and setting up the keyboard shortcuts.
    '''
    def __init__(self, stc, *args, **kwargs):
        wx.EvtHandler.__init__(self)
        self.stc = stc
        self.searchText = None
        self.lastFindResult = -1
        self.BindEvents()
        
    def OnKeyDown(self, event):
        is_search = event.MetaDown() and event.KeyCode == 'G'
        
        if self.searchText and is_search:
            self.DoInlineSearch(self.searchText, next=True)
        else:
            event.Skip()
        
    def DoInlineSearch(self, text, next=False, back=False):
        self.searchText = text
        startPos = 0
        if self.lastFindResult > 0 and next:
            startPos = self.lastFindResult + 1

        self.lastFindResult = self.stc.FindText(startPos, self.stc.GetLength(), text)
        if self.lastFindResult != -1:
            self.stc.SetCurrentPos(self.lastFindResult)
            self.stc.EnsureCaretVisible()
            self.stc.SetSelectionStart(self.lastFindResult)
            self.stc.SetSelectionEnd(self.lastFindResult + len(text))
                
    def BindEvents(self):
        self.stc.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

class HTMLSourceEditorDelegate(wx.EvtHandler):
    def __init__(self, source, *args, **kwargs):
        wx.EvtHandler.__init__(self)
        self.source = source
        self.sourceFindHandler = STCFindReplaceController(self.source)
        pub.subscribe(self.OnFind, ('search', 'find'))
        pub.subscribe(self.OnFindNext, ('search', 'findnext'))
        
    def RegisterHandlers(self, event=None):       
        app = wx.GetApp()
        app.AddHandlerForID(ID_UNDO, self.OnUndo)
        app.AddHandlerForID(ID_REDO, self.OnRedo)
        app.AddHandlerForID(ID_SELECTALL, self.OnSelectAll)
        app.AddHandlerForID(ID_SELECTNONE, self.OnSelectNone)
        
    def RemoveHandlers(self, event=None):
        app = wx.GetApp()
        app.RemoveHandlerForID(ID_UNDO)
        app.RemoveHandlerForID(ID_REDO)
        app.RemoveHandlerForID(ID_SELECTALL)
        app.RemoveHandlerForID(ID_SELECTNONE)
        
    def OnUndo(self, event):
        self.source.Undo()
        
    def OnRedo(self, event):
        self.source.Redo()
        
    def OnFind(self, text):
        if wx.GetTopLevelParent(self.source).IsActive():
            self.sourceFindHandler.DoInlineSearch(text)

    def OnFindNext(self, text):
        if wx.GetTopLevelParent(self.source).IsActive():
            self.sourceFindHandler.DoInlineSearch(text, next=True)

    def OnSelectAll(self, evt):
        self.source.SelectAll()

    def OnSelectNone(self, evt):
        self.source.SetSelection(-1, self.source.GetCurrentPos())    

    def OnCut(self, evt):
        self.source.Cut()

    def OnCopy(self, evt):
        self.source.Copy()

    def OnPaste(self, evt):
        self.source.Paste()
