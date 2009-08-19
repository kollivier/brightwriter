import os
import shutil
import urllib

import wx
import wx.stc
import wx.lib.sized_controls as sc

# eclass specific imports... we should remove these
import htmlutils
import settings
import utils
import errors
log = errors.appErrorLog

try:
    import wx.webview
    webkit_available = True
except:
    webkit_available = False

ID_NEW = wx.NewId()
ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
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
        if self.searchText and event.MetaDown() and event.KeyCode == 'G':
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
        
    def RegisterHandlers(self, event=None):
        self.source.Bind(wx.EVT_CHAR, self.OnKeyEvent)
        
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
        
    def OnDoSearch(self, event):
        text = event.GetValue()
        self.sourceFindHandler.DoInlineSearch(text)

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
        self.webview.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.webview.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        
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
        app.AddHandlerForID(ID_FIND, self.OnFind)

        app.AddHandlerForID(ID_INSERT_IMAGE, self.OnImageButton)
        app.AddHandlerForID(ID_INSERT_LINK, self.OnLinkButton)
        app.AddHandlerForID(ID_INSERT_HR, self.OnHRButton)
        app.AddHandlerForID(ID_INSERT_TABLE, self.OnTableButton)
        app.AddHandlerForID(ID_INSERT_BOOKMARK, self.OnBookmarkButton)
        app.AddHandlerForID(ID_INSERT_FLASH, self.OnFlashButton)

        app.AddHandlerForID(ID_EDITIMAGE, self.OnImageProps)
        app.AddHandlerForID(ID_EDITLINK, self.OnLinkProps)
        app.AddHandlerForID(ID_EDITOL, self.OnListProps)
        app.AddHandlerForID(ID_EDITTABLE, self.OnTableProps)
        app.AddHandlerForID(ID_EDITROW, self.OnRowProps)
        app.AddHandlerForID(ID_EDITCELL, self.OnCellProps)

        app.AddHandlerForID(ID_TEXT_SUP, self.OnSuperscript)
        app.AddHandlerForID(ID_TEXT_SUB, self.OnSubscript)
        #app.AddHandlerForID(ID_TEXT_CODE, self.OnCode)
        #app.AddHandlerForID(ID_TEXT_CITATION, self.OnCitation)
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
        app.RemoveHandlerForID(ID_FIND)
        #app.RemoveHandlerForID(ID_SELECTALL)
        #app.RemoveHandlerForID(ID_SELECTNONE)

        app.RemoveHandlerForID(ID_INSERT_IMAGE)
        app.RemoveHandlerForID(ID_INSERT_LINK)
        app.RemoveHandlerForID(ID_INSERT_HR)
        app.RemoveHandlerForID(ID_INSERT_TABLE)
        app.RemoveHandlerForID(ID_INSERT_BOOKMARK)
        app.RemoveHandlerForID(ID_INSERT_FLASH)

        app.RemoveHandlerForID(ID_EDITIMAGE)
        app.RemoveHandlerForID(ID_EDITLINK)
        app.RemoveHandlerForID(ID_EDITOL)
        app.RemoveHandlerForID(ID_EDITTABLE)
        app.RemoveHandlerForID(ID_EDITROW)
        app.RemoveHandlerForID(ID_EDITCELL)

        app.RemoveHandlerForID(ID_TEXT_SUP)
        app.RemoveHandlerForID(ID_TEXT_SUB)
        #app.RemoveHandlerForID(ID_TEXT_CODE)
        #app.RemoveHandlerForID(ID_TEXT_CITATION)
        app.RemoveHandlerForID(ID_TEXT_REMOVE_STYLES)
        
    def OnDoSearch(self, event):
        text = event.GetString()
        self.webview.FindString(text)

    def OnSelectAll(self, evt):
        self.webview.SelectAll()

    def OnSelectNone(self, evt):
        self.webview.SelectNone()

    def OnLoadComplete(self, evt):
        source = self.webview.GetPageSource()
        if source.find('<base href="about:blank">') != -1:
            pagetext = source.replace('<base href="about:blank">', '')
            self.webview.SetPageSource(pagetext)
            self.webview.Reload()

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
            trows, tcolumns, twidth, theight = mydialog.GetValues()
            tablehtml = """<table border="%s" width="%s" height="%s">""" % ("1", twidth, theight)
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
        tableProps = []
        tag = self.GetParent("table")
        if tag:
            attrs = ["width", "height", "align", "border", "cellspacing", "cellpadding"]
            for attr in attrs:
                tableProps.append(tag.GetAttribute(attr))

            mydialog = TablePropsDialog(self.webview, tableProps)
            if mydialog.ShowModal() == wx.ID_OK:
                tag.SetAttribute("width", mydialog.tableProps[0])
                tag.SetAttribute("height", mydialog.tableProps[1])
                tag.SetAttribute("align", mydialog.tableProps[2])
                tag.SetAttribute("border", mydialog.tableProps[3])
                tag.SetAttribute("cellspacing", mydialog.tableProps[4])
                tag.SetAttribute("cellpadding", mydialog.tableProps[5])
                self.dirty = True
            mydialog.Destroy()

    def OnRowProps(self, evt):
        rowProps = []
        row = self.GetParent("tr")
        if row:
            rowProps.append(row.GetAttribute("width"))
            rowProps.append(row.GetAttribute("height"))
            rowProps.append(row.GetAttribute("align"))
            rowProps.append(row.GetAttribute("valign"))
            mydialog = CellPropsDialog(self.webview, rowProps)
            mydialog.SetTitle("Row Properties")
            if mydialog.ShowModal() == wx.ID_OK:
                row.SetAttribute("width", mydialog.rowProps[0])
                row.SetAttribute("height", mydialog.rowProps[1])
                row.SetAttribute("align", mydialog.rowProps[2])
                row.SetAttribute("valign", mydialog.rowProps[3])
                self.dirty = True
            mydialog.Destroy()

    def OnCellProps(self, evt):
        rowProps = []
        tag = self.GetParent("td")
        if tag:
            rowProps.append(tag.GetAttribute("width"))
            rowProps.append(tag.GetAttribute("height"))
            rowProps.append(tag.GetAttribute("align"))
            rowProps.append(tag.GetAttribute("valign"))
            mydialog = CellPropsDialog(self.webview, rowProps)
            mydialog.SetTitle("Cell Properties")
            if mydialog.ShowModal() == wx.ID_OK:
                tag.SetAttribute("width", mydialog.rowProps[0])
                tag.SetAttribute("height", mydialog.rowProps[1])
                tag.SetAttribute("align", mydialog.rowProps[2])
                tag.SetAttribute("valign", mydialog.rowProps[3])
                self.dirty = True
            mydialog.Destroy()

    def OnImageProps(self, evt):
        imageProps = []
        tag = self.GetParent("img")
        if tag:
            imageProps.append(tag.GetAttribute("src"))
            imageProps.append(tag.GetAttribute("alt"))
            imageProps.append(tag.GetAttribute("width"))
            imageProps.append(tag.GetAttribute("height"))
            imageProps.append(tag.GetAttribute("align"))
        mydialog = ImagePropsDialog(self.webview, imageProps)
        if mydialog.ShowModal() == wx.ID_OK:
            tag.SetAttribute("src", mydialog.imageProps[0])
            tag.SetAttribute("alt", mydialog.imageProps[1])
            if not mydialog.imageProps[2] == "":
                tag.SetAttribute("width", mydialog.imageProps[2])
            if not mydialog.imageProps[3] == "":
                tag.SetAttribute("height", mydialog.imageProps[3])
            if not mydialog.imageProps[4] == "":
                tag.SetAttribute("align", mydialog.imageProps[4])
            self.dirty = True
        mydialog.Destroy()

    def OnLinkProps(self, evt):
        linkProps = []
        link = self.GetParent("A")
        url = link.GetAttribute("href")
        print "href = %s" % url
        if link:
            if url != "":
                linkProps.append(url)
                linkProps.append(link.GetAttribute("target"))
                mydialog = LinkPropsDialog(self.webview, linkProps)
                mydialog.CentreOnParent()
                if mydialog.ShowModal() == wx.ID_OK:
                    link.SetAttribute("href", mydialog.linkProps[0])
                    link.SetAttribute("target", mydialog.linkProps[1])
                    self.dirty = True
                mydialog.Destroy()
            elif link.GetAttribute("name") != "":
                linkProps.append(link.GetAttribute("name"))
                mydialog = BookmarkPropsDialog(self.webview, linkProps)
                if mydialog.ShowModal() == wx.ID_OK:
                    link.SetAttribute("href", mydialog.linkProps[0])
                    self.dirty = True
                mydialog.Destroy()

    def OnListProps(self, evt):
        listProps = []
        list = self.GetParent("ol")
        if list:
            listProps.append(list.GetAttribute("type"))
            listProps.append(list.GetAttribute("start"))
            mydialog = OLPropsDialog(self.webview, listProps)
            if mydialog.ShowModal() == wx.ID_OK:
                list.SetAttribute("type", mydialog.listProps[0])
                list.SetAttribute("start", mydialog.listProps[1])
                self.dirty = True
            mydialog.Destroy()
        
        else:
            list = self.GetParent("ul")
            if list:
                listProps.append(list.GetAttribute("type"))
                mydialog = ULPropsDialog(self.webview, listProps)
                if mydialog.ShowModal() == wx.ID_OK:
                    list.SetAttribute("type", mydialog.listProps[0])
                    self.dirty = True
                mydialog.Destroy()

    def GetParent(self, elementName):
        elementName = elementName.upper()
        selection = self.webview.GetSelection().GetAsRange()
        if selection:    
            root = selection.GetFirstNode()
            while root:
                #if isinstance(root, wx.webview.WebKitDOMElement):
                #    print "Parent tag is: %s" % root.GetTagName()
                if isinstance(root, wx.webview.WebKitDOMElement) and root.GetTagName() == elementName:
                    return root
                
                root = root.GetParentNode()
        return None

    def OnLinkButton(self, evt):    
        linkProps = []
        linkProps.append("")
        linkProps.append("")
        mydialog = LinkPropsDialog(self.webview, linkProps)
        mydialog.CentreOnParent()
        if mydialog.ShowModal() == wx.ID_OK:            
            self.webview.ExecuteEditCommand("CreateLink", mydialog.linkProps[0])
            url = self.GetParent("A")
            if url:
                print url.GetAttribute("href")
                url.SetAttribute("target", mydialog.linkProps[1])
        mydialog.Destroy()

    def OnBookmarkButton(self, evt):    
        dialog = BookmarkPropsDialog(self.webview, [""])
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            #html = "<a href='' name='" + dialog.bookmarkProps[0] + "'></a>"
            html = "<a name=\"" + dialog.bookmarkProps[0] + "\"></a>"
            #wx.MessageBox(html)
            self.webview.ExecuteEditCommand("InsertHTML", html)
            self.dirty = True
        dialog.Destroy()

    def OnFlashButton(self, evt):
        dialog = wx.FileDialog(self.webview, _("Choose a file"), "", "", _("Macromedia Flash Files") + " (*.swf)|*.swf", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            if os.path.exists(dialog.GetPath()):
                shutil.copy(dialog.GetPath(), os.path.join(settings.ProjectDir, "File"))
            code = HTMLTemplates.flashTemp
            code = code.replace("_filename_", "../File/" + dialog.GetFilename())
            code = code.replace("_autostart_", "True")
            self.webview.ExecuteEditCommand("InsertHTML", code)
        dialog.Destroy()

    def OnImageButton(self, evt):
        imageFormats = _("Image files") +"|*.gif;*.jpg;*.png;*.jpeg;*.bmp"
        dialog = wx.FileDialog(self.webview, _("Select an image"), "","", imageFormats, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            if os.path.exists(dialog.GetPath()):
                shutil.copy(dialog.GetPath(), os.path.join(settings.ProjectDir, "Graphics"))
            self.webview.ExecuteEditCommand("insertImage", "../Graphics/" + dialog.GetFilename())
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
        #elif link and link.GetAttribute('name') != '':
        #    popupmenu.Append(ID_EDITBOOKMARK, "Bookmark Properties")
        #    popupmenu.Append(ID_REMOVE_LINK, "Remove Bookmark")
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
        #evt.Skip()

    def OnUndo(self, evt):
        self.webview.ExecuteEditCommand("Undo")

    def OnKeyEvent(self, evt):
        #for now, we're just interested in knowing when to ask for save
        self.UpdateStatus(evt)

    def OnFind(self, evt):
        self.searchCtrl.SetFocus()
        self.searchCtrl.SetSelection(-1, -1)

    def RunCommand(self, command, evt):
        self.webview.ExecuteEditCommand(command)
        #self.UpdateStatus(evt)
        #self.dirty = True

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
        #self.UpdateStatus(evt)
        self.dirty = True

    def OnSuperscript(self, evt):
        self.RunCommand("superscript", evt)

    def OnSubscript(self, evt):
        self.RunCommand("subscript", evt)

    def OnCode(self, evt):
        self.RunCommand("code", evt)

    def OnCitation(self, evt):
        self.RunCommand("cite", evt)

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


class EditorFrame (wx.Frame):
    def __init__(self, parent, filename, pos=wx.DefaultPosition, size=(400,400)):
        
        wx.Frame.__init__(self, None, -1, "Document Editor", pos=pos)
        
        self.running = True
        self.filename = filename
        self.current = "about:blank"
        self.parent = parent
        self.currentItem = None #conman.ConNode("ID", conman.Content("ID2", "English"), None)
        self.findtext = ""
        
        
        #self.filename = self.currentItem.content.filename
        self.menu = wx.MenuBar()
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_NEW, _("New"))
        self.filemenu.Append(ID_OPEN, _("Open"))
        self.filemenu.Append(ID_SAVE, _("Save") +"\tCTRL+S")
        self.filemenu.Append(ID_QUIT, _("Exit") +"\tCTRL+Q")
        self.editmenu = wx.Menu()
        self.editmenu.Append(ID_UNDO, _("Undo") + "\tCTRL+Z")
        self.editmenu.Append(ID_REDO, _("Redo") + "\tCTRL+Y")
        self.editmenu.AppendSeparator()
        self.editmenu.Append(ID_CUT, _("Cut") + "\tCTRL+X")
        self.editmenu.Append(ID_COPY, _("Copy") + "\tCTRL+C")
        self.editmenu.Append(ID_PASTE, _("Paste") + "\tCTRL+V")
        self.editmenu.AppendSeparator()
        #self.editmenu.Append(ID_SELECTALL, _("Select All") + "\tCTRL+A")
        #self.editmenu.Append(ID_SELECTNONE, _("Select None"))
        #self.editmenu.AppendSeparator()
        self.editmenu.Append(ID_FIND, _("Find") + "\tCTRL+F")
        if wx.Platform == "__WXMAC__":
            self.editmenu.Append(ID_FIND_NEXT, _("Find Next") + "\tF3")
        else:
            self.editmenu.Append(ID_FIND_NEXT, _("Find Next") + "\tCTRL+G")
        self.editmenu.AppendSeparator()
        self.editmenu.Append(ID_REMOVE_LINK, _("Remove Link"))

        self.insertmenu = wx.Menu()
        self.insertmenu.Append(ID_INSERT_LINK, _("Hyperlink") + "\tCTRL+L")
        self.insertmenu.Append(ID_INSERT_BOOKMARK, _("Bookmark"))
        self.insertmenu.AppendSeparator()
        self.insertmenu.Append(ID_INSERT_IMAGE, _("Image..."))
        self.insertmenu.Append(ID_INSERT_FLASH, _("Flash Animation..."))

        self.formatmenu = wx.Menu()
        textstylemenu = wx.Menu()
        textstylemenu.Append(ID_BOLD, _("Bold") + "\tCTRL+B")
        textstylemenu.Append(ID_ITALIC, _("Italic") + "\tCTRL+I")
        textstylemenu.Append(ID_UNDERLINE, _("Underline") + "\tCTRL+U")
        textstylemenu.AppendSeparator()
        textstylemenu.Append(ID_TEXT_SUP, _("Superscript"))
        textstylemenu.Append(ID_TEXT_SUB, _("Subscript"))
        #textstylemenu.Append(ID_TEXT_CODE, _("Code"))
        #textstylemenu.Append(ID_TEXT_CITATION, _("Citation"))
        textstylemenu.AppendSeparator()
        textstylemenu.Append(ID_TEXT_REMOVE_STYLES, _("Remove Formatting"))

        self.formatmenu.AppendMenu(wx.NewId(), _("Text Style"), textstylemenu)
        
        self.tablemenu = wx.Menu()
        self.tablemenu.Append(ID_INSERT_TABLE, _("Insert Table"))

        #self.toolmenu = wx.Menu()
        #self.toolmenu.Append(ID_SPELLCHECK, _("Check Spelling"))

        self.menu.Append(self.filemenu, _("File"))
        self.menu.Append(self.editmenu, _("Edit"))
        self.menu.Append(self.insertmenu, _("Insert"))
        self.menu.Append(self.formatmenu, _("Format"))
        self.menu.Append(self.tablemenu, _("Table"))
        #self.menu.Append(self.toolmenu, _("Tools"))
        self.SetMenuBar(self.menu)
        sizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dirty = False

        #load icons
        icnSave = wx.Bitmap(os.path.join(settings.AppDir, "icons", "save16.gif"), wx.BITMAP_TYPE_GIF)
        icnBold = wx.Bitmap(os.path.join(settings.AppDir, "icons", "bold_blue16.gif"), wx.BITMAP_TYPE_GIF)
        icnItalic = wx.Bitmap(os.path.join(settings.AppDir, "icons", "italic_blue16.gif"), wx.BITMAP_TYPE_GIF)    
        icnUnderline = wx.Bitmap(os.path.join(settings.AppDir, "icons", "underline_blue16.gif"), wx.BITMAP_TYPE_GIF)

        icnCut = wx.Bitmap(os.path.join(settings.AppDir, "icons", "cut16.gif"), wx.BITMAP_TYPE_GIF)
        icnCopy = wx.Bitmap(os.path.join(settings.AppDir, "icons", "copy16.gif"), wx.BITMAP_TYPE_GIF)
        icnPaste = wx.Bitmap(os.path.join(settings.AppDir, "icons", "paste16.gif"), wx.BITMAP_TYPE_GIF)
        
        icnAlignLeft = wx.Bitmap(os.path.join(settings.AppDir, "icons", "align_left16.gif"), wx.BITMAP_TYPE_GIF) 
        icnAlignCenter = wx.Bitmap(os.path.join(settings.AppDir, "icons", "align_centre16.gif"), wx.BITMAP_TYPE_GIF)
        icnAlignRight = wx.Bitmap(os.path.join(settings.AppDir, "icons", "align_right16.gif"), wx.BITMAP_TYPE_GIF) 
        icnAlignJustify = wx.Bitmap(os.path.join(settings.AppDir, "icons", "align_justify16.gif"), wx.BITMAP_TYPE_GIF)

        icnIncreaseFont = wx.Bitmap(os.path.join(settings.AppDir, "icons", "arrowup_blue16.gif"), wx.BITMAP_TYPE_GIF)
        icnDecreaseFont = wx.Bitmap(os.path.join(settings.AppDir, "icons", "arrowdown_blue16.gif"), wx.BITMAP_TYPE_GIF)

        icnIndent = wx.Bitmap(os.path.join(settings.AppDir, "icons", "increase_indent16.gif"), wx.BITMAP_TYPE_GIF) 
        icnDedent = wx.Bitmap(os.path.join(settings.AppDir, "icons", "decrease_indent16.gif"), wx.BITMAP_TYPE_GIF)
        icnBullets = wx.Bitmap(os.path.join(settings.AppDir, "icons", "bullets16.gif"), wx.BITMAP_TYPE_GIF)
        icnNumbering = wx.Bitmap(os.path.join(settings.AppDir, "icons", "numbering16.gif"), wx.BITMAP_TYPE_GIF)

        icnColour = wx.Bitmap(os.path.join(settings.AppDir, "icons", "colour16.gif"), wx.BITMAP_TYPE_GIF)

        icnLink = wx.Bitmap(os.path.join(settings.AppDir, "icons", "insert_hyperlink16.gif"), wx.BITMAP_TYPE_GIF)
        icnImage = wx.Bitmap(os.path.join(settings.AppDir, "icons", "image16.gif"), wx.BITMAP_TYPE_GIF) 
        icnHR = wx.Bitmap(os.path.join(settings.AppDir, "icons", "horizontal_line16.gif"), wx.BITMAP_TYPE_GIF)
        #create toolbar

        self.fonts = ["Times New Roman, Times, serif", "Helvetica, Arial, sans-serif", "Courier New, Courier, monospace"]

        #self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar = wx.ToolBar(self, -1, size=(26,26))
        self.toolbar.AddSimpleTool(ID_SAVE, icnSave, _("Save"), _("Save File to Disk"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_CUT, icnCut, _("Cut"))
        self.toolbar.AddSimpleTool(ID_COPY, icnCopy, _("Copy"))
        self.toolbar.AddSimpleTool(ID_PASTE, icnPaste, _("Paste"))
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(ID_INSERT_IMAGE, icnImage, _("Insert Image"), _("Insert Image"))
        self.toolbar.AddSimpleTool(ID_INSERT_LINK, icnLink, _("Insert Link"), _("Insert Link"))
        self.toolbar.AddSimpleTool(ID_INSERT_HR, icnHR, _("Insert Horizontal Line"), _("Insert Horizontal Line"))
        self.toolbar.SetToolBitmapSize(wx.Size(16,16))
        self.toolbar.Realize()

        self.toolbar2 = wx.ToolBar(self, -1, size=(30,30))
        self.fontlist = wx.ComboBox(self.toolbar2, wx.NewId(), self.fonts[0], choices=self.fonts,style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
        #self.headings = ["None", "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"]
        #self.headinglist = wx.Choice(self.toolbar2, wx.NewId(), choices=self.headings)
        #if self.headinglist.GetCount() > 0:
        #   self.headinglist.SetSelection(0)

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
        self.toolbar2.AddSimpleTool(ID_FONT_COLOR, icnColour, _("Font Color"), _("Select a font color"))
        self.toolbar2.AddSeparator()
        self.toolbar2.AddCheckTool(ID_ALIGN_LEFT, icnAlignLeft, shortHelp=_("Left Align"))
        self.toolbar2.AddCheckTool(ID_ALIGN_CENTER, icnAlignCenter, shortHelp=_("Center"))
        self.toolbar2.AddCheckTool(ID_ALIGN_RIGHT, icnAlignRight, shortHelp=_("Right Align"))
        #self.toolbar2.AddCheckTool(ID_ALIGN_JUSTIFY, icnAlignJustify, shortHelp=_("Justify"))
        self.toolbar2.AddSeparator()
        self.toolbar2.AddSimpleTool(ID_DEDENT, icnDedent, _("Decrease Indent"), _("Decrease Indent"))
        self.toolbar2.AddSimpleTool(ID_INDENT, icnIndent, _("Increase Indent"), _("Increase Indent"))
        self.toolbar2.AddCheckTool(ID_BULLETS, icnBullets, shortHelp=_("Bullets"))
        self.toolbar2.AddCheckTool(ID_NUMBERING, icnNumbering, shortHelp=_("Numbering"))
        self.toolbar2.AddSeparator()
        self.searchCtrl = wx.SearchCtrl(self.toolbar2, -1, size=(200,-1))
        self.toolbar2.AddControl(self.searchCtrl)
        self.toolbar2.SetToolBitmapSize(wx.Size(16,16))
        self.toolbar2.Realize()

        #wx.MessageBox("Loading wx.Mozilla...")
        self.notebook = wx.Notebook(self, -1)
        notebooksizer = wx.BoxSizer(wx.VERTICAL)
        notebooksizer.Add(self.notebook, 1, wx.EXPAND, wx.ALL, 4)
        webpanel = wx.Panel(self.notebook, -1)
        self.notebook.AddPage(webpanel, "Edit")
        self.webview = wx.webview.WebView(webpanel, -1, size=(200, 200), style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self.webdelegate = HTMLEditorDelegate(source=self.webview)
        
        webpanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        webpanelsizer.Add(self.webview, 1, wx.EXPAND)
        webpanel.SetAutoLayout(True)
        webpanel.SetSizerAndFit(webpanelsizer)

        self.webview.MakeEditable(True)
        sourcepanel = wx.Panel(self.notebook, -1)
        self.notebook.AddPage(sourcepanel, "HTML")

        self.source = wx.stc.StyledTextCtrl(sourcepanel, -1)
        sourcepanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        sourcepanelsizer.Add(self.source, 1, wx.EXPAND)
        sourcepanel.SetAutoLayout(True)
        sourcepanel.SetSizerAndFit(sourcepanelsizer)

        self.source.SetLexer(wx.stc.STC_LEX_HTML)
        #self.source.SetCodePage(wx.stc.STC_CP_DBCS)
        #self.source.StyleClearAll()
        self.source.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "fore:#000000,size:12,face:Arial")
        self.source.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, "fore:#000000")
        self.source.StyleSetSpec(wx.stc.STC_H_TAG, "fore:#000099")
        self.source.StyleSetSpec(wx.stc.STC_H_ATTRIBUTE, "fore:#009900")
        self.source.StyleSetSpec(wx.stc.STC_H_VALUE, "fore:#009900")
        self.source.SetProperty("fold.html", "1")

        self.sourceDelegate = HTMLSourceEditorDelegate(self.source)

        self.SetAutoLayout(True)
        self.SetSizer(notebooksizer)

        accelerators = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('B'), ID_BOLD),(wx.ACCEL_CTRL, ord('I'), ID_ITALIC), (wx.ACCEL_CTRL, ord('U'), ID_UNDERLINE), (wx.ACCEL_CTRL, ord('S'), ID_SAVE)]) 
        self.SetAcceleratorTable(accelerators)

        wx.EVT_COMBOBOX(self, self.fontlist.GetId(), self.OnFontSelect)
        wx.EVT_TEXT_ENTER(self, self.fontlist.GetId(), self.OnFontSelect)
        wx.EVT_COMBOBOX(self, self.fontsizelist.GetId(), self.OnFontSizeSelect)
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_QUIT, self.OnQuit)
        wx.EVT_CLOSE(self, self.OnQuit)

        self.Bind(wx.EVT_TEXT, self.OnDoSearch, self.searchCtrl)

        #btnSizer.Add(self.location, 1, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        sizer.Add(self.toolbar2, 0, wx.EXPAND)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        #self.webview.ExecuteEditCommand("fontFace", self.fonts[0])
        #self.location.Append(self.current)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        
        self.notebook.SetSelection(0)
        self.LoadPage(self.filename)
        
        width, height = self.webview.GetVirtualSize()
        ssize = wx.Display().GetClientArea()
        
        if width > ssize.GetWidth():
            width = ssize.GetWidth() - 40
        
        if height > ssize.GetHeight():
            height = ssize.GetHeight() - 40
            
        self.SetSize((width, height))
        
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

    def OnDoSearch(self, event):
        text = event.GetString()
        self.webview.FindString(text)

    def OnFontSelect(self, evt):
        self.webview.ExecuteEditCommand("FontName", self.fontlist.GetStringSelection())
        self.dirty = True

    def OnFontSizeSelect(self, evt):
        self.webview.ExecuteEditCommand("FontSize", self.fontsizelist.GetStringSelection())
        self.dirty = True

    def LoadPage(self, filename):
        if os.path.exists(filename):
            fileurl = urllib.quote(os.path.dirname(filename)) + "/"
            print "File URL is: %s" % fileurl
            self.baseurl = 'file://' + fileurl
            print "base url is %s" % self.baseurl
            self.webview.SetPageSource(htmlutils.getUnicodeHTMLForFile(filename), self.baseurl)
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
            #self.webview.UpdateBaseURI()
            self.webview.Reload()

    def OnPageChanging(self, evt):
        if evt.GetOldSelection() == 1:
            self.webview.SetPageSource(self.source.GetText(), self.baseurl)
            #self.webview.UpdateBaseURI()
            self.webview.Reload()
        else:
            pagetext = self.webview.GetPageSource()
            self.source.SetText(pagetext)
            seltext = self.webview.GetSelectionAsHTML()
            if seltext != "":
                index = pagetext.find(seltext)
                self.source.SetSelection(index, index+len(seltext))
        evt.Skip()

    def OnQuit(self, evt):
        self.running = False
        if self.dirty == True:
            dlg = wx.MessageDialog(self, _("Your file contains unsaved changes. Would you like to save now?"), _("Save File?"), wx.YES_NO)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                self.OnSave(evt)
            elif result == wx.ID_CANCEL:
                return
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
        evt.Skip()

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
        self.webview.LoadURL("about:blank")

    def OnOpen(self, event):
        global webPageWildcard
        dlg = wx.FileDialog(self, _("Select a file"), "", "", webPageWildcard, wx.OPEN)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.current = dlg.GetPath()
            self.webview.LoadURL(self.current)
        dlg.Destroy()

    def OnSaveAs(self, event):
        dlg = wx.FileDialog(self, _("Save File As"), "", "", webPageWildcard, wx.SAVE)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.current = dlg.GetPath()
            self.SaveToDisk(self.current)
        dlg.Destroy()

    def OnSave(self, event):
        filename = os.path.join(settings.ProjectDir, self.filename)
        if not os.path.exists(filename):
            self.OnSaveAs(event)
        else:
            self.SaveToDisk(filename)
        
    def SaveToDisk(self, filename):
        source = self.webview.GetPageSource()
        if self.notebook.GetSelection() == 1:
            source = self.source.GetText()
            
        encoding = htmlutils.GetEncoding(source)
        try:
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

class LinkPropsDialog(sc.SizedDialog):
    def __init__(self, parent, linkProps):
        sc.SizedDialog.__init__ (self, parent, -1, _("Link Properties"), size=wx.Size(400,200), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.linkProps = linkProps
        
        pane = self.GetContentsPane()
        self.lblURL = wx.StaticText(pane, -1, _("URL"))
        linkpane = sc.SizedPanel(pane, -1)
        linkpane.SetSizerType("horizontal")
        self.cmbURL = wx.TextCtrl(linkpane, -1, linkProps[0])
        self.btnURL = wx.Button(linkpane, -1, _("Select File..."))

        self.chkNewWindow = wx.CheckBox(pane, -1, _("Open in new window"))
        if linkProps[1] == "_blank":
            self.chkNewWindow.SetValue(1)
        else:
            self.chkNewWindow.SetValue(0)

        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.cmbURL.SetFocus()
        self.Fit()

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOKClicked)
        wx.EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)

    def OnOKClicked(self, evt):
        self.linkProps[0] = self.cmbURL.GetValue()
        if self.chkNewWindow.IsChecked():
            self.linkProps[1] = "_blank"
        else:
            self.linkProps[1] = ""
        self.EndModal(wx.ID_OK)

    def OnSelectFile(self, evt):
        dialog = wx.FileDialog(self, _("Select a file"), "","", _("All files") + "|*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filedir = os.path.join(settings.ProjectDir, "File")
            if os.path.exists(dialog.GetPath()):
                if dialog.GetDirectory() != filedir:
                    shutil.copy(dialog.GetPath(), filedir)
                self.cmbURL.SetValue("../File/" + dialog.GetFilename())
        dialog.Destroy()

class BookmarkPropsDialog(wx.Dialog):
    def __init__(self, parent, bookmarkProps):
        wx.Dialog.__init__ (self, parent, -1, _("Bookmark Properties"), wx.DefaultPosition,wx.Size(300,200))
        self.parent = parent
        self.bookmarkProps = bookmarkProps

        self.lblName = wx.StaticText(self, -1, _("Name"))
        self.txtName = wx.TextCtrl(self, -1, bookmarkProps[0])

        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnOK.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblName)
        self.sizer.Add(self.txtName, 1, wx.EXPAND)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((1, 1), 1, wx.EXPAND)
        btnsizer.Add(self.btnOK)
        btnsizer.Add(self.btnCancel)

        self.sizer.Add(btnsizer)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOK)

    def OnOK(self, event):
        self.bookmarkProps[0] = self.txtName.GetValue()
        self.EndModal(wx.ID_OK)

class OLPropsDialog(wx.Dialog):
    def __init__(self, parent, listProps):
        wx.Dialog.__init__ (self, parent, -1, _("Bullets and Numbering"), wx.DefaultPosition,wx.Size(300,200))
        self.parent = parent
        self.listProps = listProps

        self.lblListType = wx.StaticText(self, -1, _("List Type:"))
        self.lstListType = wx.ListBox(self, -1)

        listTypes = ["1", "i", "I", "a", "A"]
        for type in listTypes:
            self.lstListType.Append(type)
            if type == listProps[0]:
                self.lstListType.SetStringSelection(type)
        self.lblStartNum = wx.StaticText(self, -1, _("Start at: "))
        self.txtStartNum = wx.TextCtrl(self, -1, "")
        h = self.txtStartNum.GetSize().height
        self.spnStartNum = wx.SpinButton(self, -1,size=(h,h), style=wx.SP_VERTICAL)
        self.spnStartNum.SetRange(1, 100)
        startnum = listProps[1]
        if startnum != "":
            self.spnStartNum.SetValue(int(startnum))
        else:
            self.spnStartNum.SetValue(1)

        self.txtStartNum.SetValue(str(self.spnStartNum.GetValue()))
        
        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblListType, 0, wx.LEFT, 4)
        self.sizer.Add(self.lstListType, 1, wx.EXPAND | wx.ALL, 4)
        self.sizer.Add(self.lblStartNum, 0, wx.LEFT, 4)
        spinsizer = wx.BoxSizer(wx.HORIZONTAL)
        spinsizer.Add(self.txtStartNum, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        spinsizer.Add(self.spnStartNum, 0, wx.ALL, 4)
        self.sizer.Add(spinsizer)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((1, 1), 1, wx.EXPAND)
        btnsizer.Add(self.btnOK)
        btnsizer.Add(self.btnCancel)

        self.sizer.Add(btnsizer)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOKClicked)
        wx.EVT_SPIN(self, self.spnStartNum.GetId(), self.OnSpin)
        #wx.EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)

    def OnOKClicked(self, evt):
        self.listProps[0] = self.lstListType.GetStringSelection()
        self.listProps[1] = `self.txtStartNum.GetValue()`
        self.EndModal(wx.ID_OK)

    def OnSpin(self, evt):
        self.txtStartNum.SetValue(str(evt.GetPosition()))

class ULPropsDialog(wx.Dialog):
    def __init__(self, parent, listProps):
        wx.Dialog.__init__ (self, parent, -1, _("Bullets and Numbering"), wx.DefaultPosition,wx.Size(300,200))
        self.parent = parent
        self.listProps = listProps

        self.lblListType = wx.StaticText(self, -1, _("List Type:"))
        self.lstListType = wx.ListBox(self, -1)

        listTypes = ["circle", "diamond", "square"]
        for type in listTypes:
            self.lstListType.Append(type)
            if type == listProps[0]:
                self.lstListType.SetStringSelection(type)
        
        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblListType, 0, wx.LEFT, 4)
        self.sizer.Add(self.lstListType, 1, wx.EXPAND | wx.ALL, 4)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((1, 1), 1, wx.EXPAND)
        btnsizer.Add(self.btnOK)
        btnsizer.Add(self.btnCancel)

        self.sizer.Add(btnsizer)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOKClicked)
        #wx.EVT_SPIN(self, self.spnStartNum.GetId(), self.OnSpin)
        #wx.EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)

    def OnOKClicked(self, evt):
        self.listProps[0] = self.lstListType.GetStringSelection()
        if self.listProps[0] == "diamond":
            self.listProps[0] = "disc"
        self.EndModal(wx.ID_OK)

    def OnSpin(self, evt):
        self.txtStartNum.SetValue(str(evt.GetPosition()))

class ImagePropsDialog(wx.Dialog):
    def __init__(self, parent, imageProps):
        wx.Dialog.__init__ (self, parent, -1, _("Image Properties"), wx.DefaultPosition,wx.Size(300,300))
        height = 20
        if wx.Platform == "__WXMAC__":
            height = 25
        self.parent = parent
        self.imageProps = imageProps
        self.alignments = {"": _("Default"), "left": _("Left"), "right": _("Right"), "top": _("Top"), "middle": _("Middle"), "bottom": _("Bottom")}

        self.lblImageSrc = wx.StaticText(self, -1, _("Image Location:"))
        self.txtImageSrc = wx.TextCtrl(self, -1, imageProps[0])
        self.btnImageSrc = wx.Button(self, -1, _("Select Image..."))
        self.lblDescription = wx.StaticText(self, -1, _("Text Description:"))
        self.txtDescription = wx.TextCtrl(self, -1, imageProps[1])
        self.lblAlign = wx.StaticText(self, -1, _("Image Alignment..."))
        self.chAlign = wx.Choice(self, -1, choices=self.alignments.values())
        if imageProps[4] in self.alignments.keys():
            self.chAlign.SetStringSelection(self.alignments[imageProps[4]])

        self.sizebox = wx.StaticBox(self, -1, _("Size"))
        #self.radOriginalSize = wx.RadioBox(self, -1, _("Actual size"))
        #self.radResizeImage = wx.RadioBox(self, -1, _("Custom size"))
        self.lblWidth = wx.StaticText(self, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(self, -1, imageProps[2])
        self.lblHeight = wx.StaticText(self, -1, _("Height:"))
        self.txtHeight = wx.TextCtrl(self, -1, imageProps[3])

        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnOK.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblImageSrc, 0, wx.ALL, 4)
        self.sizer.Add(self.txtImageSrc, 0, wx.ALL | wx.EXPAND, 4)
        self.sizer.Add(self.btnImageSrc, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        self.sizer.Add(self.lblDescription, 0, wx.ALL, 4)
        self.sizer.Add(self.txtDescription, 0, wx.ALL | wx.EXPAND, 4)
        boxsizer = wx.StaticBoxSizer(self.sizebox, wx.VERTICAL)
        #boxsizer.Add(self.radOriginalSize, 0)
        #boxsizer.Add(self.radResizeImage, 0)
        boxsizer.Add(self.lblWidth, 0)
        boxsizer.Add(self.txtWidth, 0)
        boxsizer.Add(self.lblHeight, 0)
        boxsizer.Add(self.txtHeight, 0)
        self.sizer.Add(boxsizer)
        self.sizer.Add(self.lblAlign)
        self.sizer.Add(self.chAlign)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((100, 25), 1, wx.EXPAND | wx.ALL, 4)
        btnsizer.Add(self.btnOK, 0, wx.ALL, 4)
        btnsizer.Add(self.btnCancel, 0, wx.ALL, 4)
        self.sizer.Add(btnsizer, 0, wx.EXPAND, 4)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)
        wx.EVT_BUTTON(self, self.btnImageSrc.GetId(), self.OnSelectImage)

    def OnOKClicked(self, evt):
        self.imageProps[0] = self.txtImageSrc.GetValue()
        self.imageProps[1] = self.txtDescription.GetValue() 
        self.imageProps[2] = self.txtWidth.GetValue()
        self.imageProps[3] = self.txtHeight.GetValue()
        align = self.chAlign.GetStringSelection()
        for item in self.alignments.keys():
            if align == self.alignments[item]:
                self.imageProps[4] = item

        self.EndModal(wx.ID_OK)
 
    def OnSelectImage(self, evt):
        imageFormats = _("Image files") + "|*.gif;*.jpg;*.png;*.jpeg;*.bmp"
        dialog = wx.FileDialog(self, _("Select an image"), "","", imageFormats, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            graphicsdir = os.path.join(self.parent.parent.pub.directory, "Graphics")
            if os.path.exists(dialog.GetPath()):
                if dialog.GetDirectory() != graphicsdir:
                    shutil.copy(dialog.GetPath(), graphicsdir)
                self.txtImageSrc.SetValue("../Graphics/" + dialog.GetFilename())
        dialog.Destroy()

class CellPropsDialog(wx.Dialog):
    def __init__(self, parent, rowProps):
        wx.Dialog.__init__ (self, parent, -1, _("Cell Properties"), wx.DefaultPosition,wx.Size(300,300))
        height = 20
        if wx.Platform == "__WXMAC__":
            height = 25
        self.parent = parent
        self.rowProps = rowProps

        self.sizebox = wx.StaticBox(self, -1, _("Size"))
        #self.radOriginalSize = wx.RadioBox(self, -1, _("Actual size"))
        #self.radResizeImage = wx.RadioBox(self, -1, _("Custom size"))
        self.lblWidth = wx.StaticText(self, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(self, -1, rowProps[0])
        self.lblHeight = wx.StaticText(self, -1, _("Height:"))
        self.txtHeight = wx.TextCtrl(self, -1, rowProps[1])

        self.alignbox = wx.StaticBox(self, -1, _("Layout and Borders"))
        self.lblAlign = wx.StaticText(self, -1, _("Horizontal Alignment:"))
        self.cmbAlign = wx.Choice(self, -1, choices=["left", "center", "right", "justify"])
        if rowProps[2] != "":
            self.cmbAlign.SetStringSelection(rowProps[2].lower())
        else:
            self.cmbAlign.SetSelection(0)
    
        self.lblVAlign = wx.StaticText(self, -1, _("Vertical Alignment:"))
        self.cmbVAlign = wx.Choice(self, -1, choices=["top", "middle", "bottom"])
        if rowProps[3] != "":
            self.cmbVAlign.SetStringSelection(rowProps[3].lower())
        else:
            self.cmbVAlign.SetSelection(0)

        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnOK.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        boxsizer = wx.StaticBoxSizer(self.sizebox, wx.VERTICAL)
        sizegridsizer = wx.FlexGridSizer(2, 2, 4, 4)
        sizegridsizer.AddMany([(self.lblWidth, 0), (self.txtWidth, 0), (self.lblHeight, 0), (self.txtHeight, 0)])
        boxsizer.Add(sizegridsizer, 1, wx.EXPAND)

        alignsizer = wx.StaticBoxSizer(self.alignbox, wx.VERTICAL)
        aligngridsizer = wx.FlexGridSizer(2, 2, 4, 4)
        aligngridsizer.AddMany([(self.lblAlign, 0), (self.cmbAlign, 0), (self.lblVAlign,0), (self.cmbVAlign, 0)])
        alignsizer.Add(aligngridsizer, 1, wx.EXPAND)
        self.sizer.Add(boxsizer, 0, wx.EXPAND | wx.ALL, 4)
        self.sizer.Add(alignsizer, 0, wx.EXPAND | wx.ALL, 4)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((100, 25), 1, wx.EXPAND | wx.ALL, 4)
        btnsizer.Add(self.btnOK, 0, wx.ALL, 4)
        btnsizer.Add(self.btnCancel, 0, wx.ALL, 4)
        self.sizer.Add(btnsizer, 0, wx.EXPAND, 4)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)

    def OnOKClicked(self, evt):
        self.rowProps[0] = self.txtWidth.GetValue()
        self.rowProps[1] = self.txtHeight.GetValue()
        self.rowProps[2] = self.cmbAlign.GetStringSelection()
        self.rowProps[3] = self.cmbVAlign.GetStringSelection()
        self.EndModal(wx.ID_OK)

class TablePropsDialog(wx.Dialog):
    def __init__(self, parent, tableProps):
        wx.Dialog.__init__ (self, parent, -1, _("Table Properties"), wx.DefaultPosition,wx.Size(300,300))
        height = 20
        if wx.Platform == "__WXMAC__":
            height = 25
        self.parent = parent
        self.tableProps = tableProps

        #sizing options
        self.sizebox = wx.StaticBox(self, -1, _("Size"))
        #self.radOriginalSize = wx.RadioBox(self, -1, _("Actual size"))
        #self.radResizeImage = wx.RadioBox(self, -1, _("Custom size"))
        self.lblWidth = wx.StaticText(self, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(self, -1, tableProps[0])
        self.lblHeight = wx.StaticText(self, -1, _("Height:"))
        self.txtHeight = wx.TextCtrl(self, -1, tableProps[1])

        #alignment options
        self.alignbox = wx.StaticBox(self, -1, _("Layout and Borders"))
        self.lblAlign = wx.StaticText(self, -1, _("Table Alignment:"))
        self.cmbAlign = wx.Choice(self, -1, choices=["Default", "Left", "Center", "Right", "Justify"])
        if tableProps[2] != "":
            self.cmbAlign.SetStringSelection(tableProps[2])
        else:
            self.cmbAlign.SetSelection(0)

        self.lblBorder = wx.StaticText(self, -1, _("Border:"))
        value = "0"
        if tableProps[3] != "":
            value = tableProps[3]
        self.spnBorder = wx.SpinCtrl(self, -1, value)
        self.lblSpacing = wx.StaticText(self, -1, _("Spacing:"))
        value = "0"
        if tableProps[4] != "":
            value = tableProps[4]
        self.spnSpacing = wx.SpinCtrl(self, -1, value)
        self.lblPadding = wx.StaticText(self, -1, _("Padding:"))
        value = "0"
        if tableProps[5] != "":
            value = tableProps[5]
        self.spnPadding = wx.SpinCtrl(self, -1, value)

        #background color 
        #self.lblBackColor = wx.StaticText(self, -1, _("Background Color:"))
        #self.btnBackColor = wx.ColorButton(self, -1)

        self.btnOK = wx.Button(self, wx.ID_OK, "OK")
        self.btnOK.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        boxsizer = wx.StaticBoxSizer(self.sizebox, wx.VERTICAL)
        sizegridsizer = wx.FlexGridSizer(2, 2, 4, 4)
        sizegridsizer.AddMany([(self.lblWidth, 0), (self.txtWidth, 0), (self.lblHeight, 0), (self.txtHeight, 0)])
        boxsizer.Add(sizegridsizer, 1, wx.EXPAND)
        alignsizer = wx.StaticBoxSizer(self.alignbox, wx.VERTICAL)
        aligngridsizer = wx.FlexGridSizer(2, 2, 4, 4)
        aligngridsizer.AddMany([(self.lblAlign, 0), (self.cmbAlign, 0), (self.lblBorder,0), (self.spnBorder, 0), 
                        (self.lblSpacing,0), (self.spnSpacing, 0), (self.lblPadding,0), (self.spnPadding, 0)])
        alignsizer.Add(aligngridsizer, 1, wx.EXPAND)
        topsizer = wx.BoxSizer(wx.HORIZONTAL)       
        self.sizer.Add(boxsizer, 0, wx.EXPAND | wx.ALL, 4)
        self.sizer.Add(alignsizer, 0, wx.EXPAND | wx.ALL, 4)
        #colorsizer = wx.BoxSizer(wx.HORIZONTAL)
        #colorsizer.AddMany([(self.lblBackColor),(self.btnBackColor)])
        #self.sizer.Add(colorsizer, 0, wx.ALL, 4)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((100, 25), 1, wx.EXPAND | wx.ALL, 4)
        btnsizer.Add(self.btnOK, 0, wx.ALL, 4)
        btnsizer.Add(self.btnCancel, 0, wx.ALL, 4)
        self.sizer.Add(btnsizer, 0, wx.EXPAND, 4)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        wx.EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)

    def OnOKClicked(self, evt):
        self.tableProps[0] = self.txtWidth.GetValue()
        self.tableProps[1] = self.txtHeight.GetValue()
        if self.cmbAlign.GetStringSelection() != "Default":
            self.tableProps[2] = self.cmbAlign.GetStringSelection()
        else:
            self.tableProps[2] = ""
        self.tableProps[3] = `self.spnBorder.GetValue()`
        self.tableProps[4] = `self.spnSpacing.GetValue()`
        self.tableProps[5] = `self.spnPadding.GetValue()`
        self.EndModal(wx.ID_OK)

class CreateTableDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        sc.SizedDialog.__init__ (self, *args, **kwargs)

        self.trows = "1"
        self.tcolumns = "1"
        self.twidth= "100"
        self.theight = "100"

        panel = self.GetContentsPane()

        rcpane = sc.SizedPanel(panel, -1)
        rcpane.SetSizerType("horizontal")
        self.lblRows = wx.StaticText(rcpane, -1, _("Rows:"))
        self.lblRows.SetSizerProps(valign="center")
        self.txtRows = wx.SpinCtrl(rcpane, -1, "1")
        self.lblColumns = wx.StaticText(rcpane, -1, _("Columns:"))
        self.lblColumns.SetSizerProps(valign="center")
        self.txtColumns = wx.SpinCtrl(rcpane, -1, "1")

        widthPane = sc.SizedPanel(panel, -1)
        widthPane.SetSizerType("horizontal")
        self.lblWidth = wx.StaticText(widthPane, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(widthPane, -1, "")
        self.cmbWidthType = wx.Choice(widthPane, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbWidthType.SetStringSelection(_("Percent"))
        
        heightPane = sc.SizedPanel(panel, -1)
        heightPane.SetSizerType("horizontal")
        self.lblHeight = wx.StaticText(heightPane, -1, _("Height:"))
        self.txtHeight = wx.TextCtrl(heightPane, -1, "")
        self.cmbHeightType = wx.Choice(heightPane, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbHeightType.SetStringSelection(_("Percent"))
        
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        self.Fit()
        self.SetMinSize(self.GetSize())

    def GetValues(self):
        trows = self.txtRows.GetValue()
        tcolumns = self.txtColumns.GetValue() 
        twidth = self.txtWidth.GetValue()
        if self.cmbWidthType.GetStringSelection() == _("Percent"):
            twidth += "%"
        
        theight = self.txtHeight.GetValue()
        if self.cmbHeightType.GetStringSelection() == _("Percent"):
            theight += "%"

        return (trows, tcolumns, twidth, theight)

class MyApp(wx.App):
    def OnInit(self):
        self.frame = EditorFrame(None, "about:blank")
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
