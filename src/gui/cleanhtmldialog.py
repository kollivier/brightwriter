import wx
import wx.webkit
#import wx.lib.flatnotebook as fnb
import wx.lib.sized_controls as sc
import wx.stc

def _(text):
    return text


class HTMLCleanUpDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__(self, *args, **kwargs)
        
        pane = self.GetContentsPane()
        
        label_pane = sc.SizedPanel(pane, -1)
        label_pane.SetSizerType("horizontal")
        label_pane.SetSizerProps(expand=True)
        
        original_label = wx.StaticText(label_pane, -1, _("Original page"))
        original_label.SetSizerProps(align="center", expand=True, proportion=1)
        
        new_label = wx.StaticText(label_pane, -1, _("Cleaned page"))
        new_label.SetSizerProps(align="center", expand=True, proportion=1)
        
        self.splitter1 = wx.SplitterWindow(pane, -1, style=wx.NO_BORDER)
        self.splitter1.SetSashSize(1)
        self.splitter1.SetSizerProps({"expand":True, "proportion":1})

        #fnbStyle = fnb.FNB_NO_X_BUTTON | fnb.FNB_NO_NAV_BUTTONS

        #self.originalBook = fnb.FlatNotebook(self.splitter1, wx.ID_ANY, style=fnbStyle)
        #self.newBook = fnb.FlatNotebook(self.splitter1, wx.ID_ANY, style=fnbStyle)

        self.original = wx.webkit.WebKitCtrl(self.originalBook, -1)
        self.originalSource = wx.stc.StyledTextCtrl(self.originalBook, -1)
        
        self.new = wx.webkit.WebKitCtrl(self.newBook, -1)
        self.newSource = wx.stc.StyledTextCtrl(self.newBook, -1)
        
        self.originalBook.AddPage(self.original, _("Original Page"))
        self.newBook.AddPage(self.new, _("Cleaned Page"))
        
        self.originalBook.AddPage(self.originalSource, _("Original HTML"))
        self.newBook.AddPage(self.newSource, _("Cleaned HTML"))
        
        self.splitter1.SplitVertically(self.originalBook, self.newBook, 300)

        self.log = wx.TextCtrl(pane, -1, size=(-1, 120), style=wx.TE_MULTILINE)
        self.log.SetSizerProps(expand=True)
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        ok = self.FindWindowById(wx.ID_OK)
        ok.SetLabel(_("Apply Changes"))
        
        
    def SetOriginalHTML(self, html):
        self.original.SetPageSource(html)
        self.originalSource.SetText(html)
        
    def SetCleanedHTML(self, html):
        self.new.SetPageSource(html)
        self.newSource.SetText(html)
        
