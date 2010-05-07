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

import htmlutils
import aboutdialog
import cleanhtmldialog

try:
    import wx.webview
    webkit_available = True
except:
    import traceback
    print traceback.print_exc()
    webkit_available = False

ID_NEW = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_SAVE_AS = wx.NewId()
ID_QUIT = wx.NewId()

ID_BOLD = wx.NewId()
ID_ITALIC = wx.NewId()
ID_UNDERLINE = wx.NewId()

ID_ALIGN_LEFT = wx.NewId()
ID_ALIGN_CENTER = wx.NewId()
ID_ALIGN_RIGHT = wx.NewId()
ID_ALIGN_JUSTIFY = wx.NewId()

ID_INDENT = wx.NewId()
ID_DEDENT = wx.NewId()

ID_BULLETS = wx.NewId()
ID_NUMBERING = wx.NewId()

ID_EDITOL = wx.NewId()

ID_FONT_COLOR = wx.NewId()

ID_INSERT_IMAGE = wx.NewId()
ID_INSERT_LINK = wx.NewId()
ID_INSERT_HR = wx.NewId()
ID_INSERT_TABLE = wx.NewId()
ID_INSERT_BOOKMARK = wx.NewId()
ID_INSERT_FLASH = wx.NewId()

ID_EDITIMAGE = wx.NewId()
ID_EDITLINK = wx.NewId()
ID_EDITTABLE = wx.NewId()
ID_EDITROW = wx.NewId()
ID_EDITCOL = wx.NewId()
ID_EDITCELL = wx.NewId()
ID_EDITBOOKMARK = wx.NewId()

ID_UNDO = wx.NewId()
ID_REDO = wx.NewId()
ID_REMOVE_LINK = wx.NewId()

ID_FIND = wx.NewId()
ID_FIND_NEXT = wx.NewId()

ID_CUT = wx.NewId()
ID_COPY = wx.NewId()
ID_PASTE = wx.NewId()

ID_SPELLCHECK = wx.NewId()
ID_SELECTALL = wx.NewId()
ID_SELECTNONE = wx.NewId()

ID_TEXT_SUP = wx.NewId()
ID_TEXT_SUB = wx.NewId()
ID_TEXT_CODE = wx.NewId()
ID_TEXT_CITATION = wx.NewId()
ID_TEXT_REMOVE_STYLES = wx.NewId()
ID_CLEANUP_HTML = wx.NewId()

def _(text):
    return text

# should be part of the frame?
webPageWildcard = _("Web Pages") + "(*.htm,*.html)|*.html;*.htm"

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

class HTMLEditorDelegate(wx.EvtHandler):
    def __init__(self, source, *args, **kwargs):
        wx.EvtHandler.__init__(self, *args, **kwargs)
        self.webview = source
        settings = self.webview.GetWebSettings()
        settings.SetEditableLinkBehavior(wx.webview.EditableLinkOnlyLiveWithShiftKey)
        self.webview.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.webview.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.searchId = None
        Publisher().subscribe(self.OnDoSearch, ('search', 'text', 'changed'))
        
    def OnSetFocus(self, event):
        self.RegisterHandlers()
        event.Skip()
        
    def OnKillFocus(self, event):
        self.RemoveHandlers()
        event.Skip()
        
    def RegisterHandlers(self):
        app = wx.GetApp()
        app.AddHandlerForID(ID_UNDO, self.OnUndo)
        app.AddHandlerForID(ID_REDO, self.OnRedo)
        app.AddHandlerForID(ID_CUT, self.OnCut)
        app.AddHandlerForID(ID_COPY, self.OnCopy)
        app.AddHandlerForID(ID_PASTE, self.OnPaste)
        app.AddHandlerForID(ID_REMOVE_LINK, self.OnRemoveLink)
        app.AddHandlerForID(ID_BOLD, self.OnBoldButton)
        app.AddHandlerForID(ID_ITALIC, self.OnItalicButton)
        app.AddHandlerForID(ID_UNDERLINE, self.OnUnderlineButton)
        app.AddHandlerForID(ID_FONT_COLOR, self.OnFontColorButton)
        app.AddHandlerForID(ID_ALIGN_LEFT, self.OnLeftAlignButton)
        app.AddHandlerForID(ID_ALIGN_CENTER, self.OnCenterAlignButton)
        app.AddHandlerForID(ID_ALIGN_RIGHT, self.OnRightAlignButton)
        app.AddHandlerForID(ID_INDENT, self.OnIndentButton)
        app.AddHandlerForID(ID_DEDENT, self.OnOutdentButton)
        app.AddHandlerForID(ID_BULLETS, self.OnBullet)
        app.AddHandlerForID(ID_NUMBERING, self.OnNumbering)
        app.AddHandlerForID(ID_SELECTALL, self.OnSelectAll)
        app.AddHandlerForID(ID_SELECTNONE, self.OnSelectNone)

        app.AddHandlerForID(ID_INSERT_IMAGE, self.OnImageButton)
        app.AddHandlerForID(ID_INSERT_LINK, self.OnLinkButton)
        app.AddHandlerForID(ID_INSERT_HR, self.OnHRButton)
        app.AddHandlerForID(ID_INSERT_TABLE, self.OnTableButton)
        app.AddHandlerForID(ID_INSERT_BOOKMARK, self.OnBookmarkButton)

        app.AddHandlerForID(ID_EDITIMAGE, self.OnImageProps)
        app.AddHandlerForID(ID_EDITLINK, self.OnLinkProps)
        app.AddHandlerForID(ID_EDITOL, self.OnListProps)
        app.AddHandlerForID(ID_EDITTABLE, self.OnTableProps)
        app.AddHandlerForID(ID_EDITROW, self.OnRowProps)
        app.AddHandlerForID(ID_EDITCELL, self.OnCellProps)

        app.AddHandlerForID(ID_TEXT_SUP, self.OnSuperscript)
        app.AddHandlerForID(ID_TEXT_SUB, self.OnSubscript)
        app.AddHandlerForID(ID_TEXT_REMOVE_STYLES, self.OnRemoveStyle)
        
        self.webview.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClick)
        
    def RemoveHandlers(self):
        app = wx.GetApp()
        app.RemoveHandlerForID(ID_UNDO)
        app.RemoveHandlerForID(ID_REDO)
        app.RemoveHandlerForID(ID_CUT)
        app.RemoveHandlerForID(ID_COPY)
        app.RemoveHandlerForID(ID_PASTE)
        app.RemoveHandlerForID(ID_REMOVE_LINK)
        app.RemoveHandlerForID(ID_BOLD)
        app.RemoveHandlerForID(ID_ITALIC)
        app.RemoveHandlerForID(ID_UNDERLINE)
        app.RemoveHandlerForID(ID_FONT_COLOR)
        app.RemoveHandlerForID(ID_ALIGN_LEFT)
        app.RemoveHandlerForID(ID_ALIGN_CENTER)
        app.RemoveHandlerForID(ID_ALIGN_RIGHT)
        app.RemoveHandlerForID(ID_INDENT)
        app.RemoveHandlerForID(ID_DEDENT)
        app.RemoveHandlerForID(ID_BULLETS)
        app.RemoveHandlerForID(ID_NUMBERING)
        app.RemoveHandlerForID(ID_SELECTALL)
        app.RemoveHandlerForID(ID_SELECTNONE)

        app.RemoveHandlerForID(ID_INSERT_IMAGE)
        app.RemoveHandlerForID(ID_INSERT_LINK)
        app.RemoveHandlerForID(ID_INSERT_HR)
        app.RemoveHandlerForID(ID_INSERT_TABLE)
        app.RemoveHandlerForID(ID_INSERT_BOOKMARK)

        app.RemoveHandlerForID(ID_EDITIMAGE)
        app.RemoveHandlerForID(ID_EDITLINK)
        app.RemoveHandlerForID(ID_EDITOL)
        app.RemoveHandlerForID(ID_EDITTABLE)
        app.RemoveHandlerForID(ID_EDITROW)
        app.RemoveHandlerForID(ID_EDITCELL)

        app.RemoveHandlerForID(ID_TEXT_SUP)
        app.RemoveHandlerForID(ID_TEXT_SUB)
        app.RemoveHandlerForID(ID_TEXT_REMOVE_STYLES)
        
    def OnDoSearch(self, message):
        if wx.GetTopLevelParent(self.webview).IsActive():
            self.webview.FindString(message.data)

    def OnSelectAll(self, evt):
        self.webview.ExecuteEditCommand("SelectAll")

    def OnSelectNone(self, evt):
        self.webview.ExecuteEditCommand("Unselect")

    def OnRedo(self, evt):
        self.RunCommand("Redo", evt)

    def OnCut(self, evt):
        self.RunCommand("Cut", evt)

    def OnCopy(self, evt):
        self.webview.ExecuteEditCommand("Copy")

    def OnPaste(self, evt):
        self.RunCommand("Paste", evt)

    def OnTableButton(self, evt):
        tableProps = []
        mydialog = CreateTableDialog(self.webview, -1, _("Table Properties"), size=(400,400))
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            trows, tcolumns, twidth = mydialog.GetValues()
            tablehtml = """<table border="%s" width="%s">""" % ("1", twidth)
            for counter in range(0, int(trows)):
                tablehtml = tablehtml + "<tr>"
                for counter in range(0, int(tcolumns)):
                    tablehtml = tablehtml + "<td>&nbsp</td>"
                tablehtml = tablehtml + "</tr>"
            tablehtml = tablehtml + "</table>"
            self.webview.ExecuteEditCommand("InsertHTML", tablehtml)
            self.dirty = True
        mydialog.Destroy()
        
    def OnTableProps(self, evt):
        self.ShowEditorForTag("TABLE", TablePropsDialog)

    def OnRowProps(self, evt):
        self.ShowEditorForTag("TR", RowPropsDialog)

    def OnCellProps(self, evt):
        self.ShowEditorForTag("TD", CellPropsDialog)

    def OnImageProps(self, evt):
        self.ShowEditorForTag("IMG", ImagePropsDialog)
    
    def ShowEditorForTag(self, tagName, editorClass):
        props = {}
        tag = self.GetParent(tagName)
        attrs = htmlattrs.tag_attrs[tagName]
        all_attrs = attrs["required"] + attrs["optional"]
        for attr in all_attrs:
            props[attr] = tag.GetAttribute(attr)

        mydialog = editorClass(self.webview, props)
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            return_props = mydialog.getProps()
            editcmd = wx.webview.WebEditCommand(self.webview.GetMainFrame())        
            for prop in return_props:
                assert prop in all_attrs
                editcmd.SetNodeAttribute(tag, prop, return_props[prop])
            editcmd.Apply()
            self.dirty = True

        mydialog.Destroy()

    def OnLinkProps(self, evt):
        linkProps = {}
        link = self.GetParent("A")
        if link:
            url = link.GetAttribute("href")
            if url != "":
                self.ShowEditorForTag("A", LinkPropsDialog)

            elif link.GetAttribute("name") != "":
                self.ShowEditorForTag("A", BookmarkPropsDialog)

    def OnListProps(self, evt):
        listProps = []
        list = self.GetParent("ol")
        if list:
            self.ShowEditorForTag("OL", OLPropsDialog)
        
        else:
            self.ShowEditorForTag("UL", ULPropsDialog)

    def GetParent(self, elementName):
        elementName = elementName.upper()
        selection = self.webview.GetSelection().GetAsRange()
        if selection:                
            root = selection.GetStartContainer()
            children = root.GetChildNodes()
            
            # when selecting, say, an image, the container is actually the tag above the
            # image, so we need to find the image in the children.
            for index in xrange(children.GetLength()):
                child = children.Item(index)
                if isinstance(child, wx.webview.DOMElement) and child.GetTagName() == elementName:
                    return child
            
            while root:
                if isinstance(root, wx.webview.DOMElement) and root.GetTagName() == elementName:
                    return root
                
                root = root.GetParentNode()
        return None

    def OnLinkButton(self, evt):    
        linkProps = {}
        mydialog = LinkPropsDialog(self.webview, linkProps)
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:
            props = mydialog.getProps()
            self.webview.ExecuteEditCommand("CreateLink", props["href"])
            if "target" in props:
                url = self.GetParent("A")
                if url:
                    url.SetAttribute("target", props["target"])
        mydialog.Destroy()

    def OnBookmarkButton(self, evt):    
        dialog = BookmarkPropsDialog(self.webview, {})
        dialog.CentreOnParent()
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            props = dialog.getProps()
            html = "<a name=\"" + props["name"] + "\"></a>"
            self.webview.ExecuteEditCommand("InsertHTML", html)
            self.dirty = True
        dialog.Destroy()

    def OnImageButton(self, evt):
        imageFormats = _("Image files") +"|*.gif;*.jpg;*.png;*.jpeg;*.bmp"
        dialog = wx.FileDialog(self.webview, _("Select an image"), "","", imageFormats, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.webview.ExecuteEditCommand("InsertImage", 'file://' + dialog.GetPath())
        self.dirty = True

    def OnHRButton(self, evt):
        self.webview.ExecuteEditCommand("InsertHorizontalRule")
        self.dirty = True

    def OnFontColorButton(self, evt):
        dlg = wx.ColourDialog(self.webview)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData().GetColour().Get() #RGB tuple
            red = str(hex(data[0])).replace("0x", "")
            if len(red) == 1:
                red = "0" + red
            green = str(hex(data[1])).replace("0x", "")
            if len(green) == 1:
                green = "0" + green
            blue = str(hex(data[2])).replace("0x", "")
            if len(blue) == 1:
                blue = "0" + blue
            value = "#" + red + green + blue
            self.webview.ExecuteEditCommand("ForeColor", value)
        dlg.Destroy()
        self.dirty = True

    def OnRightClick(self, evt):
        popupmenu = wx.Menu()
        if self.GetParent("IMG"):
            popupmenu.Append(ID_EDITIMAGE, "Image Properties")
        link = self.GetParent("A")
        if link and link.GetAttribute('href') != '':
            popupmenu.Append(ID_EDITLINK, "Link Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Link")
        if self.GetParent("ol") or self.GetParent("ul"):
            popupmenu.Append(ID_EDITOL, "Bullets and Numbering")
        if self.GetParent("table"):
            popupmenu.Append(ID_EDITTABLE, "Table Properties")
        if self.GetParent("tr"):
            popupmenu.Append(ID_EDITROW, "Row Properties")
        if self.GetParent("td"):
            popupmenu.Append(ID_EDITCELL, "Cell Properties")
        position = evt.GetPosition()
        self.webview.PopupMenu(popupmenu, self.webview.ScreenToClient(position))

    def OnUndo(self, evt):
        self.webview.ExecuteEditCommand("Undo")

    def OnKeyEvent(self, evt):
        #for now, we're just interested in knowing when to ask for save
        self.UpdateStatus(evt)

    def OnSuperscript(self, evt):
        self.RunCommand("superscript", evt)

    def OnSubscript(self, evt):
        self.RunCommand("subscript", evt)

    def OnRemoveStyle(self, evt):
        self.RunCommand("RemoveFormat", evt)

    def OnRemoveLink(self, evt):
        self.RunCommand("removeLinks", evt)

    def OnBullet(self, evt):
        self.RunCommand("InsertUnorderedList", evt)

    def OnNumbering(self, evt):
        self.RunCommand("InsertOrderedList", evt)

    def OnBoldButton(self, evt):
        self.RunCommand("Bold", evt)
        
    def OnItalicButton(self, evt):
        self.RunCommand("Italic", evt)

    def OnUnderlineButton(self, evt):
        self.RunCommand("Underline", evt)

    def OnLeftAlignButton(self, evt):
        self.RunCommand("AlignLeft", evt)

    def OnCenterAlignButton(self, evt):
        self.RunCommand("AlignCenter", evt)
        
    def OnRightAlignButton(self, evt):
        self.RunCommand("AlignRight", evt)

    def OnOutdentButton(self, evt):
        self.RunCommand("Outdent", evt)

    def OnIndentButton(self, evt):
        self.RunCommand("Indent", evt)

    def RunCommand(self, command, evt):
        self.webview.ExecuteEditCommand(command)
        self.dirty = True

    def OnSuperscript(self, evt):
        self.RunCommand("Superscript", evt)

    def OnSubscript(self, evt):
        self.RunCommand("Subscript", evt)

    def OnRemoveStyle(self, evt):
        self.RunCommand("RemoveFormat", evt)

    def OnRemoveLink(self, evt):
        # FIXME: This only works when the entire link is in the selection. To make this
        # work from anywhere inside the link, we must expand the selection to contain
        # the whole link, which will require adding more of WebCore::SelectionController API
        # to wxWebKitSelection.
        self.RunCommand("Unlink", evt)

    def OnBullet(self, evt):
        self.RunCommand("InsertUnorderedList", evt)

    def OnNumbering(self, evt):
        self.RunCommand("InsertOrderedList", evt)

    def OnBoldButton(self, evt):
        self.RunCommand("Bold", evt)
        
    def OnItalicButton(self, evt):
        self.RunCommand("Italic", evt)

    def OnUnderlineButton(self, evt):
        self.RunCommand("Underline", evt)

    def OnLeftAlignButton(self, evt):
        self.RunCommand("AlignLeft", evt)

    def OnCenterAlignButton(self, evt):
        self.RunCommand("AlignCenter", evt)
        
    def OnRightAlignButton(self, evt):
        self.RunCommand("AlignRight", evt)

    def OnOutdentButton(self, evt):
        self.RunCommand("Outdent", evt)

    def OnIndentButton(self, evt):
        self.RunCommand("Indent", evt)


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
        
        self.tablemenu = wx.Menu()
        self.tablemenu.Append(ID_INSERT_TABLE, _("Insert Table"))
        
        self.helpmenu = wx.Menu()
        self.helpmenu.Append(wx.ID_ABOUT, _("About %s" % wx.GetApp().GetAppName()))

        self.menu.Append(self.filemenu, _("File"))
        self.menu.Append(self.editmenu, _("Edit"))
        self.menu.Append(self.insertmenu, _("Insert"))
        self.menu.Append(self.formatmenu, _("Format"))
        self.menu.Append(self.tablemenu, _("Table"))
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
        icnBold = wx.Bitmap(os.path.join(icondir, "format-text-bold.png"))
        icnItalic = wx.Bitmap(os.path.join(icondir, "format-text-italic.png"))
        icnUnderline = wx.Bitmap(os.path.join(icondir, "format-text-underline.png"))

        icnCut = wx.Bitmap(os.path.join(icondir, "edit-copy.png"))
        icnCopy = wx.Bitmap(os.path.join(icondir, "edit-cut.png"))
        icnPaste = wx.Bitmap(os.path.join(icondir, "edit-paste.png"))
        
        icnAlignLeft = wx.Bitmap(os.path.join(icondir, "format-justify-left.png")) 
        icnAlignCenter = wx.Bitmap(os.path.join(icondir, "format-justify-center.png"))
        icnAlignRight = wx.Bitmap(os.path.join(icondir, "format-justify-right.png"))
        icnAlignJustify = wx.Bitmap(os.path.join(icondir, "format-justify-fill.png"))

        icnIndent = wx.Bitmap(os.path.join(icondir, "format-indent-more.png")) 
        icnDedent = wx.Bitmap(os.path.join(icondir, "format-indent-less.png"))
        icnBullets = wx.Bitmap(os.path.join(icondir, "fatcow", "text_list_bullets.png"))
        icnNumbering = wx.Bitmap(os.path.join(icondir, "fatcow", "text_list_numbers.png"))

        #icnColour = wx.Bitmap(os.path.join(icondir, "colour16.gif"))

        icnLink = wx.Bitmap(os.path.join(icondir, "applications-internet.png"))
        icnImage = wx.Bitmap(os.path.join(icondir, "image-x-generic.png")) 
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

        self.toolbar2 = wx.ToolBar(self.panel, -1)
        self.toolbar2.SetSizerProps(expand=True, border=("all", 0))
        self.toolbar2.SetToolBitmapSize(wx.Size(24,24))
        self.fontlist = wx.ComboBox(self.toolbar2, wx.NewId(), self.fonts[0], choices=self.fonts,style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)

        self.fontsizes = ["1", "2", "3", "4", "5", "6", "7"]
        self.fontsizelist = wx.ComboBox(self.toolbar2, wx.NewId(), choices=self.fontsizes)
        if self.fontsizelist.GetCount() > 0:
            self.fontsizelist.SetSelection(0)

        #self.toolbar2.AddControl(self.headinglist)
        #self.toolbar2.AddSeparator()
        self.toolbar2.AddControl(self.fontlist)
        self.toolbar2.AddSeparator()
        self.toolbar2.AddControl(self.fontsizelist)
        self.toolbar2.AddSeparator()
        
        self.toolbar2.AddCheckTool(ID_BOLD, icnBold, shortHelp=_("Bold"))
        self.toolbar2.AddCheckTool(ID_ITALIC, icnItalic, shortHelp=_("Italic"))
        self.toolbar2.AddCheckTool(ID_UNDERLINE, icnUnderline, shortHelp=_("Underline"))
        #self.toolbar2.AddSimpleTool(ID_FONT_COLOR, icnColour, _("Font Color"), _("Select a font color"))
        self.toolbar2.AddSeparator()
        self.toolbar2.AddCheckTool(ID_ALIGN_LEFT, icnAlignLeft, shortHelp=_("Left Align"))
        self.toolbar2.AddCheckTool(ID_ALIGN_CENTER, icnAlignCenter, shortHelp=_("Center"))
        self.toolbar2.AddCheckTool(ID_ALIGN_RIGHT, icnAlignRight, shortHelp=_("Right Align"))
        self.toolbar2.AddSeparator()
        self.toolbar2.AddSimpleTool(ID_DEDENT, icnDedent, _("Decrease Indent"), _("Decrease Indent"))
        self.toolbar2.AddSimpleTool(ID_INDENT, icnIndent, _("Increase Indent"), _("Increase Indent"))
        self.toolbar2.AddCheckTool(ID_BULLETS, icnBullets, shortHelp=_("Bullets"))
        self.toolbar2.AddCheckTool(ID_NUMBERING, icnNumbering, shortHelp=_("Numbering"))
        self.toolbar2.AddSeparator()
        self.toolbar2.AddSimpleTool(ID_INSERT_IMAGE, icnImage, _("Insert Image"), _("Insert Image"))
        self.toolbar2.AddSimpleTool(ID_INSERT_LINK, icnLink, _("Insert Link"), _("Insert Link"))
        #self.toolbar.AddSimpleTool(ID_INSERT_HR, icnHR, _("Insert Horizontal Line"), _("Insert Horizontal Line"))
        self.toolbar2.Realize()

        self.notebook = fnb.FlatNotebook(self.panel, -1, style=fnb.FNB_NODRAG)
        self.notebook.SetSizerProps(expand=True,proportion=1)
        webpanel = sc.SizedPanel(self.notebook, -1)
        #webpanel.SetSizerProps(expand=True,proportion=1)
        self.notebook.AddPage(webpanel, "Edit")
        self.webview = wx.webview.WebView(webpanel, -1, size=(200, 200), style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self.webview.MakeEditable(True)
        self.webdelegate = HTMLEditorDelegate(source=self.webview)
        
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

        self.fontlist.Bind(wx.EVT_COMBOBOX, self.OnFontSelect)
        wx.EVT_TEXT_ENTER(self, self.fontlist.GetId(), self.OnFontSelect)
        wx.EVT_COMBOBOX(self, self.fontsizelist.GetId(), self.OnFontSizeSelect)
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
            self.webview.SetPageSource(htmlutils.getUnicodeHTMLForFile(filename), self.baseurl)
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
            self.webview.SetPageSource(pagetext)
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
            self.webview.SetPageSource(html)
        

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
    
class TagEditorDialog(sc.SizedDialog):
    def __init__(self, *a, **kw):
        sc.SizedDialog.__init__(self, *a, **kw)
        self.tagName = None
        # FIXME: Add a notebook with a "style" section here
    
    def setProps(self, props):
        assert self.tagName
        
        attrs = htmlattrs.tag_attrs[self.tagName]
        
        for prop in props:
            assert prop in attrs["required"] + attrs["optional"]
            control = self.FindWindowByName(prop)
            if control:
                value = props[prop]
                if isinstance(control, wx.TextCtrl):
                    control.SetValue(value)
                elif isinstance(control, wx.SpinCtrl):
                    if value.isdigit():
                        control.SetValue(int(value))
                elif isinstance(control, wx.Choice) or isinstance(control, wx.ComboBox):
                    tagattrs = htmlattrs.attr_values[self.tagName][prop]
                    in_list = False
                    for tagattr in tagattrs:
                        if tagattrs[tagattr] == value:
                            if isinstance(control, wx.Choice):
                                control.SetStringSelection(tagattr)
                            else:
                                control.SetValue(tagattr)
                            in_list = True
                    if not in_list and isinstance(control, wx.ComboBox):
                        control.SetValue(value)
                elif isinstance(control, wx.FilePickerCtrl):
                    control.GetTextCtrl().SetValue(value)
                    
    def getProps(self):
        assert self.tagName
        retattrs = {}
        attrs = htmlattrs.tag_attrs[self.tagName]
        all_attrs = attrs["required"] + attrs["optional"]
        for attr in all_attrs:
            control = self.FindWindowByName(attr)
            if control:
                if isinstance(control, wx.TextCtrl):
                    retattrs[attr] = control.GetValue()
                elif isinstance(control, wx.SpinCtrl):
                    retattrs[attr] = "%d" % control.GetValue()
                elif isinstance(control, wx.Choice) or isinstance(control, wx.ComboBox):
                    if isinstance(control, wx.Choice):
                        value = control.GetStringSelection()
                    else:
                        value = control.GetValue()
                    if value in htmlattrs.attr_values[self.tagName][attr]:
                        retattrs[attr] = htmlattrs.attr_values[self.tagName][attr][value]
                    elif isinstance(control, wx.ComboBox):
                        retattrs[attr] = value
                elif isinstance(control, wx.FilePickerCtrl):
                    retattrs[attr] = control.GetTextCtrl().GetValue()
        return retattrs

class LinkPropsDialog(TagEditorDialog):
    def __init__(self, parent, linkProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Link Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "A"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        wx.StaticText(pane, -1, _("Link"))
        self.fileURL = wx.FilePickerCtrl(pane, -1, style=wx.FLP_OPEN | wx.FLP_USE_TEXTCTRL, name="href")
        self.fileURL.SetSizerProps(expand=True)

        wx.StaticText(pane, -1, _("Open in"))
        target = wx.ComboBox(pane, -1, choices=htmlattrs.attr_values["A"]["target"].keys(), name="target")
        target.SetSizerProps(expand=True)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.fileURL.SetFocus()
        self.Fit()
        self.MinSize = self.Size
        self.MaxSize = (-1, self.Size.y)
        
        self.setProps(linkProps)

class BookmarkPropsDialog(TagEditorDialog):
    def __init__(self, parent, bookmarkProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Bookmark Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "A"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Name"))
        wx.TextCtrl(pane, -1, name="name")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(bookmarkProps)

class OLPropsDialog(TagEditorDialog):
    def __init__(self, parent, listProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Ordered List Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "OL"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        
        wx.StaticText(pane, -1, _("List Type"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["OL"]["type"].keys(), name="type")

        wx.StaticText(pane, -1, _("Start at"))
        self.spnStartNum = wx.SpinCtrl(pane, -1, "1", name="start")
        self.spnStartNum.SetRange(1, 100)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(listProps)

class ULPropsDialog(TagEditorDialog):
    def __init__(self, parent, listProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Unordered List Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "UL"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("List Type"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["UL"]["type"].keys(), name="type")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(listProps)

class ImagePropsDialog(TagEditorDialog):
    def __init__(self, parent, imageProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Image Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "IMG"
        
        pane = self.GetContentsPane()
 
        self.imageProps = imageProps

        pane.SetSizerType("form")
        
        wx.StaticText(pane, -1, _("Image Location"))
        self.txtImageSrc = wx.FilePickerCtrl(pane, -1, name="src")
        self.txtImageSrc.SetSizerProps(expand=True)
        wx.StaticText(pane, -1, _("Text Description"))
        self.txtDescription = wx.TextCtrl(pane, -1, name="alt")
        self.txtDescription.SetSizerProps(expand=True)
        wx.StaticText(pane, -1, _("Image Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['IMG']['align'].keys(), name="align")

        wx.StaticText(pane, -1, _("Width"))
        wx.TextCtrl(pane, -1, name="width")
        wx.StaticText(pane, -1, _("Height"))
        wx.TextCtrl(pane, -1, name="height")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(imageProps)

class RowPropsDialog(TagEditorDialog):
    def __init__(self, parent, props):
        TagEditorDialog.__init__ (self, parent, -1, _("Row Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TR"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Horizontal Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TR']['align'].keys(), name="align")
    
        wx.StaticText(pane, -1, _("Vertical Alignment:"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TR']['valign'].keys(), name="valign")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(props)

class CellPropsDialog(TagEditorDialog):
    def __init__(self, parent, props):
        TagEditorDialog.__init__ (self, parent, -1, _("Cell Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TD"

        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Horizontal Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TD']['align'].keys(), name="align")
    
        wx.StaticText(pane, -1, _("Vertical Alignment:"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values['TD']['valign'].keys(), name="valign")
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(props)

class TablePropsDialog(TagEditorDialog):
    def __init__(self, parent, tableProps):
        TagEditorDialog.__init__ (self, parent, -1, _("Table Properties"), wx.DefaultPosition,wx.DefaultSize,style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.tagName = "TABLE"
        
        pane = self.GetContentsPane()
        pane.SetSizerType("form")

        wx.StaticText(pane, -1, _("Width"))
        wx.TextCtrl(pane, -1, name="width")

        #alignment options
#
        wx.StaticText(pane, -1, _("Alignment"))
        wx.Choice(pane, -1, choices=htmlattrs.attr_values["TABLE"]["align"].keys(), name="align")

        wx.StaticText(pane, -1, _("Border"))
        wx.SpinCtrl(pane, -1, "0", name="border")
        
        wx.StaticText(pane, -1, _("Spacing"))
        wx.SpinCtrl(pane, -1, "0", name="cellspacing")
        
        wx.StaticText(pane, -1, _("Padding"))
        wx.SpinCtrl(pane, -1, "0", name="cellpadding")

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.MinSize = self.Size
        
        self.setProps(tableProps)

class CreateTableDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__ (self, *args, **kwargs)

        self.trows = "1"
        self.tcolumns = "1"
        self.twidth= "100"

        panel = self.GetContentsPane()

        rcpane = sc.SizedPanel(panel, -1)
        rcpane.SetSizerType("horizontal")
        self.lblRows = wx.StaticText(rcpane, -1, _("Rows:"))
        self.lblRows.SetSizerProps(valign="center")
        self.txtRows = wx.SpinCtrl(rcpane, -1, self.trows)
        self.lblColumns = wx.StaticText(rcpane, -1, _("Columns:"))
        self.lblColumns.SetSizerProps(valign="center")
        self.txtColumns = wx.SpinCtrl(rcpane, -1, self.tcolumns)

        widthPane = sc.SizedPanel(panel, -1)
        widthPane.SetSizerType("horizontal")
        self.lblWidth = wx.StaticText(widthPane, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(widthPane, -1, self.twidth)
        self.cmbWidthType = wx.Choice(widthPane, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbWidthType.SetStringSelection(_("Percent"))
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.SetMinSize(self.GetSize())

    def GetValues(self):
        trows = self.txtRows.GetValue()
        tcolumns = self.txtColumns.GetValue() 
        twidth = self.txtWidth.GetValue()
        if twidth.isdigit() and self.cmbWidthType.GetStringSelection() == _("Percent"):
            twidth += "%"

        return (trows, tcolumns, twidth)

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
