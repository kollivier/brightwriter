import os
import sys
import shutil
import urllib

import wx
import wx.stc
import wx.lib.eventStack as events
import wx.lib.flatnotebook as fnb
import wx.lib.mixins.inspection
import wx.lib.sized_controls as sc

from wx.lib.pubsub import Publisher

thisfile = sys.executable
if not hasattr(sys, 'frozen'):
    thisfile = __file__

import htmledit.htmlattrs as htmlattrs

import editordelegate
import edittoolbar
import htmlutils
import aboutdialog
import cleanhtmldialog

from constants import *

ID_NEW = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_SAVE_AS = wx.NewId()
ID_QUIT = wx.NewId()

try:
    import wx.webview
    webkit_available = True
except:
    import traceback
    print traceback.print_exc()
    webkit_available = False

def _(text):
    return text

# should be part of the frame?
webPageWildcard = _("Web Pages") + "(*.htm,*.html)|*.html;*.htm"

def getMimeTypeForHTML(html):
    mimetype = 'text/html'
    if html.find("//W3C//DTD XHTML") != -1:
        mimetype = 'application/xhtml+xml'
    return mimetype

class STCFindReplaceController(wx.EvtHandler):
    '''
    This class controls Find and Replace behaviors for wxSTC, e.g. adding
    "move to selection" behavior and setting up the keyboard shortcuts.
    '''
    def __init__(self, stc, *args, **kwargs):
        wx.EvtHandler.__init__(self, *args, **kwargs)
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

        self.lastFindResult = self.stc.FindText(0, self.stc.GetLength(), text)
        if self.lastFindResult != -1:
            self.stc.SetCurrentPos(self.lastFindResult)
            self.stc.EnsureCaretVisible()
            self.stc.SetSelectionStart(self.lastFindResult)
            self.stc.SetSelectionEnd(self.lastFindResult + len(text))
                
    def BindEvents(self):
        self.stc.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

class HTMLSourceEditorDelegate(wx.EvtHandler):
    def __init__(self, source, *args, **kwargs):
        wx.EvtHandler.__init__(self, *args, **kwargs)
        self.source = source
        self.sourceFindHandler = STCFindReplaceController(self.source)
        self.searchId = None
        Publisher().subscribe(self.OnDoSearch, ('search', 'text', 'changed'))
        
    def RegisterHandlers(self, event=None):       
        app = wx.GetApp()
        app.AddHandlerForID(ID_UNDO, self.OnUndo)
        app.AddHandlerForID(ID_REDO, self.OnRedo)
        app.AddHandlerForID(ID_SELECTALL, self.OnSelectAll)
        app.AddHandlerForID(ID_SELECTNONE, self.OnSelectNone)
        
        search = self.source.FindWindowByName("searchctrl")
        if search:
            self.searchId = search.GetId()
            app.AddHandlerForID(self.searchId, self.OnDoSearch)
        
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
        
    def OnDoSearch(self, message):
        if wx.GetTopLevelParent(self.source).IsActive():
            self.sourceFindHandler.DoInlineSearch(message.data)

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

class EditorFrame (sc.SizedFrame):
    def __init__(self, parent, filename, pos=wx.DefaultPosition, size=(660,400)):
        
        sc.SizedFrame.__init__(self, None, -1, "Document Editor", pos=pos)
        
        self.running = True
        self.filename = filename
        self.current = "about:blank"
        self.parent = parent
        self.currentItem = None
        self.findtext = ""
        
        self.menu = wx.MenuBar()
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_NEW, _("New"))
        self.filemenu.Append(ID_OPEN, _("Open"))
        self.filemenu.Append(ID_SAVE, _("Save") +"\tCTRL+S")
        self.filemenu.Append(ID_SAVE_AS, _("Save As..."))
        self.filemenu.Append(ID_QUIT, _("Exit") +"\tCTRL+Q")
        self.editmenu = wx.Menu()
        self.editmenu.Append(ID_UNDO, _("Undo") + "\tCTRL+Z")
        self.editmenu.Append(ID_REDO, _("Redo") + "\tCTRL+Y")
        self.editmenu.AppendSeparator()
        self.editmenu.Append(ID_CUT, _("Cut") + "\tCTRL+X")
        self.editmenu.Append(ID_COPY, _("Copy") + "\tCTRL+C")
        self.editmenu.Append(ID_PASTE, _("Paste") + "\tCTRL+V")
        self.editmenu.AppendSeparator()
        self.editmenu.Append(ID_SELECTALL, _("Select All") + "\tCTRL+A")
        self.editmenu.Append(ID_SELECTNONE, _("Select None"))
        self.editmenu.AppendSeparator()
        if wx.Platform != "__WXMAC__":
            self.editmenu.Append(ID_FIND_NEXT, _("Find Next") + "\tF3")
        else:
            self.editmenu.Append(ID_FIND_NEXT, _("Find Next") + "\tCTRL+G")

        self.insertmenu = wx.Menu()
        self.insertmenu.Append(ID_INSERT_LINK, _("Hyperlink") + "\tCTRL+L")
        self.insertmenu.Append(ID_INSERT_BOOKMARK, _("Bookmark") + "\tCTRL+SHIFT+B")
        self.insertmenu.AppendSeparator()
        self.insertmenu.Append(ID_INSERT_IMAGE, _("Image..."))
        self.insertmenu.Append(ID_INSERT_TABLE, _("Insert Table"))
        

        self.formatmenu = wx.Menu()
        textstylemenu = wx.Menu()
        textstylemenu.Append(ID_BOLD, _("Bold") + "\tCTRL+B")
        textstylemenu.Append(ID_ITALIC, _("Italic") + "\tCTRL+I")
        textstylemenu.Append(ID_UNDERLINE, _("Underline") + "\tCTRL+U")
        textstylemenu.AppendSeparator()
        textstylemenu.Append(ID_TEXT_SUP, _("Superscript"))
        textstylemenu.Append(ID_TEXT_SUB, _("Subscript"))
        textstylemenu.AppendSeparator()
        textstylemenu.Append(ID_TEXT_REMOVE_STYLES, _("Remove Formatting"))
        textstylemenu.Append(ID_REMOVE_LINK, _("Remove Link"))
        self.formatmenu.AppendMenu(wx.NewId(), _("Text Style"), textstylemenu)
        self.formatmenu.AppendSeparator()
        self.formatmenu.Append(ID_CLEANUP_HTML, _("Clean Up HTML"))
                
        self.helpmenu = wx.Menu()
        self.helpmenu.Append(wx.ID_ABOUT, _("About %s" % wx.GetApp().GetAppName()))

        self.menu.Append(self.filemenu, _("File"))
        self.menu.Append(self.editmenu, _("Edit"))
        self.menu.Append(self.insertmenu, _("Insert"))
        self.menu.Append(self.formatmenu, _("Format"))
        self.menu.Append(self.helpmenu, _("Help"))
        
        self.SetMenuBar(self.menu)
        self.dirty = False
        
        self.fileHistory = wx.FileHistory()
        self.fileConfig = wx.FileConfig(appName="EClass.HTMLEditor", vendorName="Tulane University")
        self.fileHistory.UseMenu(self.filemenu)
        self.fileHistory.Load(self.fileConfig)

        #load icons
        icondir = os.path.join("htmledit", "images")
        
        icnNew = wx.Bitmap(os.path.join(icondir, "document-new.png"))
        icnOpen = wx.Bitmap(os.path.join(icondir, "document-open.png"))
        icnSave = wx.Bitmap(os.path.join(icondir, "document-save.png"))
        
        icnCut = wx.Bitmap(os.path.join(icondir, "edit-copy.png"))
        icnCopy = wx.Bitmap(os.path.join(icondir, "edit-cut.png"))
        icnPaste = wx.Bitmap(os.path.join(icondir, "edit-paste.png"))
        
        #icnHR = wx.Bitmap(os.path.join(icondir, "horizontal_line16.gif"))
        #create toolbar

        self.fonts = ["Times New Roman, Times, serif", "Helvetica, Arial, sans-serif", "Courier New, Courier, monospace"]

        self.panel = self.GetContentsPane()
        
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize(wx.Size(32,32))
        self.toolbar.AddSimpleTool(ID_NEW, icnNew, _("New"), _("Create a New File"))
        self.toolbar.AddSimpleTool(ID_OPEN, icnOpen, _("Open"), _("Open File on Disk"))
        self.toolbar.AddSimpleTool(ID_SAVE, icnSave, _("Save"), _("Save File to Disk"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_CUT, icnCut, _("Cut"))
        self.toolbar.AddSimpleTool(ID_COPY, icnCopy, _("Copy"))
        self.toolbar.AddSimpleTool(ID_PASTE, icnPaste, _("Paste"))
        self.toolbar.AddSeparator()
        self.searchCtrl = wx.SearchCtrl(self.toolbar, -1, size=(200,-1))
        self.toolbar.AddControl(self.searchCtrl)
        
        self.toolbar.Realize()

        self.SetToolBar(self.toolbar)

        self.toolbar2 = edittoolbar.editToolBar(self.panel)

        self.notebook = fnb.FlatNotebook(self.panel, -1, style=fnb.FNB_NODRAG)
        self.notebook.SetSizerProps(expand=True,proportion=1)
        webpanel = sc.SizedPanel(self.notebook, -1)
        #webpanel.SetSizerProps(expand=True,proportion=1)
        self.notebook.AddPage(webpanel, "Edit")
        self.webview = wx.webview.WebView(webpanel, -1, size=(200, 200), style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self.webview.MakeEditable(True)
        self.webdelegate = editordelegate.HTMLEditorDelegate(source=self.webview)
        
        webpanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        webpanelsizer.Add(self.webview, 1, wx.EXPAND)
        #webpanel.SetAutoLayout(True)
        webpanel.SetSizerAndFit(webpanelsizer)

        sourcepanel = sc.SizedPanel(self.notebook, -1)
        self.notebook.AddPage(sourcepanel, "HTML")

        self.source = wx.stc.StyledTextCtrl(sourcepanel, -1)
        sourcepanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        sourcepanelsizer.Add(self.source, 1, wx.EXPAND)
        sourcepanel.SetSizerAndFit(sourcepanelsizer)

        self.source.SetLexer(wx.stc.STC_LEX_HTML)
        self.source.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "fore:#000000,size:12,face:Arial")
        self.source.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "fore:#000000")
        self.source.StyleSetSpec(wx.stc.STC_H_TAG, "fore:#000099")
        self.source.StyleSetSpec(wx.stc.STC_H_ATTRIBUTE, "fore:#009900")
        self.source.StyleSetSpec(wx.stc.STC_H_VALUE, "fore:#009900")
        self.source.SetProperty("fold.html", "1")

        self.sourceDelegate = HTMLSourceEditorDelegate(self.source)

        accelerators = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('B'), ID_BOLD),(wx.ACCEL_CTRL, ord('I'), ID_ITALIC), (wx.ACCEL_CTRL, ord('U'), ID_UNDERLINE), (wx.ACCEL_CTRL, ord('S'), ID_SAVE)]) 
        self.SetAcceleratorTable(accelerators)

        # self.fontlist.Bind(wx.EVT_COMBOBOX, self.OnFontSelect)
        # wx.EVT_TEXT_ENTER(self, self.fontlist.GetId(), self.OnFontSelect)
        # wx.EVT_COMBOBOX(self, self.fontsizelist.GetId(), self.OnFontSizeSelect)
        self.Bind(wx.EVT_MENU, self.OnNew, id=ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id=ID_SAVE_AS)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=ID_QUIT)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnCleanHTML, id=ID_CLEANUP_HTML)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.Bind(wx.EVT_TEXT, self.OnDoSearch, self.searchCtrl)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)

        self.Fit()
        
        self.notebook.SetSelection(0)
        self.baseurl = os.path.abspath(os.path.dirname(thisfile))
        self.CreateNewPage()
        
        self.CentreOnScreen()
        
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_CLOSE(self, self.OnQuit)

        wx.EVT_NOTEBOOK_PAGE_CHANGING(self.notebook, self.notebook.GetId(), self.OnPageChanging)
        if wx.Platform == '__WXMSW__':
            wx.EVT_CHAR(self.notebook, self.SkipNotebookEvent)
            
        self.webview.Bind(wx.EVT_MOUSE_EVENTS, self.UpdateStatus)
        self.Size = size
        
        self.webview.SetFocus()

    def GetCommandState(self, command):
        if self.FindFocus() == self.webview:
            state = self.webview.GetEditCommandState(command) 
            if state in [wx.webview.EditStateMixed, wx.webview.EditStateTrue]:
                return True
        
        return False
        
    def OnFileHistory(self, event):
        filename = self.fileHistory.GetHistoryFile(event.GetId() - wx.ID_FILE1)
        self.LoadPage(filename)

    def OnActivate(self, event):
        delegate = self.webdelegate
        if self.FindFocus() is not self.webview:
            delegate = self.sourceDelegate

        if event.GetActive():
            delegate.RegisterHandlers()
        else:
            delegate.RemoveHandlers()

    def OnAbout(self, event):
        aboutdlg = aboutdialog.AboutDialog(self, -1, pos=(40,40), style=wx.CLOSE_BOX|wx.FRAME_NO_TASKBAR)
        aboutdlg.Show()

    def UpdateStatus(self, evt):
        self.toolbar2.ToggleTool(ID_BOLD, self.GetCommandState("Bold"))
        self.toolbar2.ToggleTool(ID_ITALIC, self.GetCommandState("Italic"))
        self.toolbar2.ToggleTool(ID_UNDERLINE, self.GetCommandState("Underline"))
        self.toolbar2.ToggleTool(ID_BULLETS, self.GetCommandState("InsertUnorderedList"))
        self.toolbar2.ToggleTool(ID_NUMBERING, self.GetCommandState("InsertOrderedList"))
        self.toolbar2.ToggleTool(ID_ALIGN_LEFT, self.GetCommandState("AlignLeft"))
        self.toolbar2.ToggleTool(ID_ALIGN_CENTER, self.GetCommandState("AlignCenter"))
        self.toolbar2.ToggleTool(ID_ALIGN_RIGHT, self.GetCommandState("AlignRight"))
        self.toolbar2.ToggleTool(ID_ALIGN_JUSTIFY, self.GetCommandState("AlignJustify"))
        self.fontsizelist.SetValue(self.webview.GetEditCommandValue("FontSize"))
        self.fontlist.SetValue(self.webview.GetEditCommandValue("FontName"))
        
        evt.Skip()

    def CreateNewPage(self):
        self.webview.SetPageSource("<html><head><title>New Page</title></head><body><p></p></body></html>", 'file://' + self.baseurl + "/")

    def OnDoSearch(self, event):
        # wx bug: event.GetString() doesn't work on Windows 
        text = event.GetEventObject().GetValue()
        Publisher().sendMessage(('search', 'text', 'changed'), text)

    def OnFontSelect(self, evt):
        self.webview.ExecuteEditCommand("FontName", self.fontlist.GetStringSelection())
        self.dirty = True

    def OnFontSizeSelect(self, evt):
        self.webview.ExecuteEditCommand("FontSize", self.fontsizelist.GetStringSelection())
        self.dirty = True

    def LoadPage(self, filename):
        if os.path.exists(filename):
            self.fileHistory.AddFileToHistory(filename)
            fileurl = urllib.quote(os.path.dirname(filename)) + "/"
            self.baseurl = 'file://' + fileurl
            html = htmlutils.getUnicodeHTMLForFile(filename)
            
            self.webview.SetPageSource(html, self.baseurl, getMimeTypeForHTML(html))
            self.SetTitle(os.path.basename(filename))
            self.filename = filename

    def OnLinkClicked(self, event):
        event.Cancel()
        
    def SkipNotebookEvent(self, evt):
        evt.Skip()

    def SkipEvent(self, evt):
        pass

    def OnLoadComplete(self, evt):
        source = self.webview.GetPageSource()
        if source.find('<base href="about:blank">') != -1:
            pagetext = source.replace('<base href="about:blank">', '')
            self.webview.SetPageSource(pagetext, self.baseurl)
            self.SetTitle(self.webview.GetPageTitle())
            #self.webview.UpdateBaseURI()
            self.webview.Reload()

    def OnPageChanging(self, evt):
        if evt.GetOldSelection() == 1:
            self.webview.Show()
            self.webview.SetPageSource(self.source.GetText(), self.baseurl)
            self.toolbar2.Parent.GetSizer().Show(self.toolbar2)
            self.toolbar2.Parent.Layout()
        else:
            pagetext = self.webview.GetPageSource()
            self.source.SetText(pagetext)
            seltext = self.webview.GetSelectionAsHTML()
            if seltext != "":
                index = pagetext.find(seltext)
                self.source.SetSelection(index, index+len(seltext))
            self.toolbar2.Parent.GetSizer().Hide(self.toolbar2)
            self.toolbar2.Parent.Layout()

    def OnQuit(self, evt):
        self.running = False
        if self.dirty == True:
            dlg = wx.MessageDialog(self, _("Your file contains unsaved changes. Would you like to save now?"), _("Save File?"), wx.YES_NO)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.OnSave(evt)
            elif result == wx.ID_CANCEL:
                return
        self.fileHistory.Save(self.fileConfig)
        self.MakeModal(False)
        self.Show(False)
        self.Destroy()
            
    def OnRightClick(self, evt):
        popupmenu = wx.Menu()
        if evt.GetImageSrc() != "" and self.GetParent("img"):
            popupmenu.Append(ID_EDITIMAGE, "Image Properties")
        if evt.GetLink() != "" and self.GetParent("href"):
            popupmenu.Append(ID_EDITLINK, "Link Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Link")
        elif evt.GetLink() != "" and self.GetParent("a"):
            popupmenu.Append(ID_EDITBOOKMARK, "Bookmark Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Bookmark")
        if self.GetParent("ol") or self.GetParent("ul"):
            popupmenu.Append(ID_EDITOL, "Bullets and Numbering")
        if self.GetParent("table"):
            popupmenu.Append(ID_EDITTABLE, "Table Properties")
        if self.GetParent("tr"):
            popupmenu.Append(ID_EDITROW, "Row Properties")
        if self.GetParent("td"):
            popupmenu.Append(ID_EDITCELL, "Cell Properties")
        position = evt.GetPosition()
        position[0] = position[0] + self.notebook.GetPosition()[0]
        position[1] = position[1] + self.notebook.GetPosition()[1]
        self.PopupMenu(popupmenu, position)

    def OnCleanHTML(self, event):
        try:
            import tidylib
        except:
            wx.MessageBox(_("Your system appears not to have the HTMLTidy library installed. Cannot run HTML clean up."))
            return
        
        html, errors = htmlutils.cleanUpHTML(self.webview.GetPageSource())
    
        dialog = cleanhtmldialog.HTMLCleanUpDialog(self, -1, size=(600,400), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        dialog.SetOriginalHTML(self.webview.GetPageSource())
        dialog.SetCleanedHTML(html)
        dialog.log.SetValue(errors)
        if dialog.ShowModal() == wx.ID_OK:
            self.webview.SetPageSource(html, self.baseurl, getMimeTypeForHTML(html))
        

    def OnSize(self, evt):
        self.Layout()

    def OnCharEvent(self, evt):
        self.dirty = True
        self.OnKeyEvent(evt)

    def OnKeyEvent(self, evt):
        #for now, we're just interested in knowing when to ask for save
        self.UpdateStatus(evt)

    def OnFind(self, evt):
        self.searchCtrl.SetFocus()
        self.searchCtrl.SetSelection(-1, -1)

    def OnLocationSelect(self, evt):
        #url = self.location.GetStringSelection()
        self.log.write('OnLocationSelect: %s\n' % url)
        self.webview.LoadURL(url)

    def OnLocationKey(self, evt):
        if evt.KeyCode() == WXK_RETURN:
            #URL = self.location.GetValue()
            #self.location.Append(URL)
            self.webview.LoadURL(URL)
        else:
            evt.Skip()

    def IgnoreReturn(self, evt):
        if evt.GetKeyCode() != WXK_RETURN:
            evt.Skip()

    def OnNew(self, event):
        wx.GetApp().CreateNewFrame()

    def OnOpen(self, event):
        global webPageWildcard
        dlg = wx.FileDialog(self, _("Select a file"), "", "", webPageWildcard, wx.OPEN)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.LoadPage(dlg.GetPath())
        dlg.Destroy()

    def OnSaveAs(self, event):
        dlg = wx.FileDialog(self, _("Save File As"), "", "", webPageWildcard, wx.SAVE)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.current = dlg.GetPath()
            self.SaveToDisk(self.current)
        dlg.Destroy()

    def OnSave(self, event):
        filename = self.filename
        if not filename or not os.path.exists(filename):
            self.OnSaveAs(event)
        else:
            self.SaveToDisk(filename)
        
    def SaveToDisk(self, filename):
        source = self.webview.GetPageSource()
        if self.notebook.GetSelection() == 1:
            source = self.source.GetText()
            
        encoding = htmlutils.GetEncoding(source)
        try:
            if not encoding:
                encoding = htmlutils.getCurrentEncoding()
            print "encoding to %s" % encoding
            source = source.encode(encoding)
        except:
            raise
                
        afile = open(filename, "wb")
        afile.write(source)
        afile.close()
        self.dirty = False
        self.filename = filename

    def logEvt(self, name, event):
        self.log.write('%s: %s\n' %
                       (name, (event.GetLong1(), event.GetLong2(), event.GetText1())))

    def OnBeforeNavigate2(self, evt):
        self.logEvt('OnBeforeNavigate2', evt)

    def OnNewWindow2(self, evt):
        self.logEvt('OnNewWindow2', evt)
        evt.Veto() # don't allow it

def strict(char):
    print "Unicode Error on character: " + chr(char)

class MyApp(wx.App, events.AppEventHandlerMixin, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        events.AppEventHandlerMixin.__init__(self)
        wx.lib.mixins.inspection.InspectionMixin.__init__(self)
        self.SetAppName("EClass.HTMLEdit")
        self.frame = EditorFrame(None, None)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        
        for arg in sys.argv[1:]:
            if os.path.exists(arg):
                self.frame.LoadPage(arg)
        
        return True
        
    def CreateNewFrame(self, filename=None):
        newframe = EditorFrame(None, None)
        if filename:
            newframe.LoadPage(filename)
        newframe.Show()
        
    def MacOpenFile(self, filename):
        self.CreateNewFrame(filename)

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
