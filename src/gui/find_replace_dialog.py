import wx
import wx.lib.sized_controls as sc

from wx.lib.pubsub import pub

from ids import *

class WebViewFindReplaceController(wx.EvtHandler):
    def __init__(self, webview):
        wx.EvtHandler.__init__(self)
        self.webview = webview
        self.hasResult = False
        
        pub.subscribe(self.OnFindNext, ('find_replace', 'find_next'))
        pub.subscribe(self.OnFindPrevious, ('find_replace', 'find_previous'))
        pub.subscribe(self.OnReplace, ('find_replace', 'replace'))
        pub.subscribe(self.OnReplaceFind, ('find_replace', 'replace_find'))
        pub.subscribe(self.OnReplaceAll, ('find_replace', 'replace_all'))
        
    def FindText(self, text, caseSensitive=False, forward=True):
        self.hasResult = self.webview.FindString(text, forward, caseSensitive)
    
    def ReplaceText(self, text):
        if self.hasResult:
            self.webview.ExecuteEditCommand("InsertText", text)
    
    def OnFindNext(self, message):
        find_text, match_case = message.data
        self.FindText(find_text, match_case)
        if not self.hasResult:
            wx.Bell()

    def OnFindPrevious(self, message):
        find_text, match_case = message.data
        self.FindText(find_text, match_case, forward=False)
        if not self.hasResult:
            wx.Bell()

    def OnReplace(self, message):
        self.ReplaceText(message.data)
    
    def OnReplaceFind(self, message):
        find_text, replace_text, match_case = message.data
        self.ReplaceText(replace_text)
        self.FindText(find_text, match_case)

    def OnReplaceAll(self, message):
        find_text, replace_text, match_case = message.data
        self.ReplaceText(replace_text)
        self.FindText(find_text, match_case)
        while self.hasResult:
            self.ReplaceText(replace_text)
            self.FindText(find_text, match_case)

class FindReplaceDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        
        pane = self.GetContentsPane()
        
        fr_panel = sc.SizedPanel(pane, -1)
        fr_panel.SetSizerType("form")
        fr_panel.SetSizerProps(expand=True, proportion=1)
        
        wx.StaticText(fr_panel, -1, _("Find:"))
        self.find_text = wx.TextCtrl(fr_panel, -1)
        self.find_text.SetSizerProps(expand=True)
        
        wx.StaticText(fr_panel, -1, _("Replace:"))
        self.replace_text = wx.TextCtrl(fr_panel, -1)
        self.replace_text.SetSizerProps(expand=True)
        
        self.case_checkbox = wx.CheckBox(pane, -1, _("Match Case"))
        
        button_panel = sc.SizedPanel(pane, -1)
        button_panel.SetSizerType("horizontal")
        
        replace_all_button = wx.Button(button_panel, ID_REPLACE_ALL, _("Replace All"))
        replace_button = wx.Button(button_panel, ID_REPLACE, _("Replace"))
        replace_find_button = wx.Button(button_panel, ID_REPLACE_FIND, _("Replace && Find"))
        next_button = wx.Button(button_panel, ID_FIND_NEXT, _("Next"))
        previous_button = wx.Button(button_panel, ID_FIND_PREVIOUS, _("Previous"))
        
        next_button.Bind(wx.EVT_BUTTON, self.OnFindNext)
        previous_button.Bind(wx.EVT_BUTTON, self.OnFindPrevious)
        replace_button.Bind(wx.EVT_BUTTON, self.OnReplace)
        replace_find_button.Bind(wx.EVT_BUTTON, self.OnReplaceFind)
        replace_all_button.Bind(wx.EVT_BUTTON, self.OnReplaceAll)
        
        self.find_text.SetFocus()
        
        self.Fit()
        
    def OnFindNext(self, event):
        pub.sendMessage(('find_replace', 'find_next'), (self.find_text.GetValue(), self.case_checkbox.IsChecked()))

    def OnFindPrevious(self, event):
        pub.sendMessage(('find_replace', 'find_previous'), (self.find_text.GetValue(), self.case_checkbox.IsChecked()))

    def OnReplace(self, event):
        pub.sendMessage(('find_replace', 'replace'), self.replace_text.GetValue())

    def OnReplaceFind(self, event):
        pub.sendMessage(('find_replace', 'replace_find'), (self.find_text.GetValue(), self.replace_text.GetValue(), self.case_checkbox.IsChecked()))

    def OnReplaceAll(self, event):
        pub.sendMessage(('find_replace', 'replace_all'), (self.find_text.GetValue(), self.replace_text.GetValue(), self.case_checkbox.IsChecked()))
