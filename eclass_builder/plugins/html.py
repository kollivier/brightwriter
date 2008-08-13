import wx
import wx.stc
import string
import os
#import conman.conman as conman
import locale
import re
import settings
import eclassutils
import ims
import ims.contentpackage
import appdata

import conman
from xmlutils import *
from htmlutils import *
from fileutils import *
import plugins
from mmedia import HTMLTemplates
    #from conman.colorbutton import *

mozilla_available = False

from StringIO import StringIO
from threading import *
import traceback
import sys
import utils, guiutils, settings

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

ID_INCREASE_FONT = wx.NewId()
ID_DECREASE_FONT = wx.NewId()

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
import errors
log = errors.appErrorLog

#-------------------------- PLUGIN REGISTRATION ---------------------
# This info is used so that EClass can be dynamically be added into
# EClass.Builder's plugin registry.

plugin_info = { "Name":"html", 
                "FullName":"Web Page", 
                "Directory": "Text", 
                "Extension": ["htm", "html"], 
                "Mime Type": "text/html",
                "IMS Type": "webcontent",
                "Requires":"", 
                "CanCreateNew":True}

#-------------------------- DATA CLASSES ----------------------------

htmlpage = """
    <html>
    <head>
    <title>New Page</title>
    </head>
    <body></body>
    </html>
"""

def CreateNewFile(filename, name="New Page"):
    try:
        if os.path.exists(filename):
            return False
        file = htmlpage
        file = file.replace("New Page", name)
        output = open(filename, "w")
        output.write(file)
        output.close()
        return True
    except:
        global log
        log.write(_("Could not create new HTML file."))
        return False

#------------------------ PUBLISHER CLASSES -------------------------------------------
#if this isn't the main script, then we're probably loading in EClass.Builder
#so load the plugin publisher class
if __name__ != "__main__":
    class HTMLPublisher(plugins.BaseHTMLPublisher):
        #init defined by parent class
        def GetFileLink(self, filename):
            return "pub/" + os.path.basename(self.GetFilename(filename))

        def GetData(self):
            if isinstance(self.node, conman.conman.ConNode):
                filename = self.node.content.filename
            
            elif isinstance(self.node, ims.contentpackage.Item):
                resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)
                filename = eclassutils.getEClassPageForIMSResource(resource)
                if not filename:
                    filename = resource.getFilename()
            
            filename = os.path.join(settings.ProjectDir, filename)
            
            if os.path.exists(filename):
                myfile = None
                myfile = utils.openFile(filename, 'r')
                
                #if myfile:
                myhtml = GetBody(myfile)
                myfile.close()
                #else:
                #   myhtml = ""
            else:
                myhtml = ""

            self.data['content'] = myhtml

#-------------------------- EDITOR INTERFACE ----------------------------------------

class EditorFrame (wx.Frame):
    def __init__(self, parent):
        self.running = true
        wx.Frame.__init__(self,NULL, -1, "Document Editor")
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
        self.editmenu.Append(ID_SELECTALL, _("Select All") + "\tCTRL+A")
        self.editmenu.Append(ID_SELECTNONE, _("Select None"))
        self.editmenu.AppendSeparator()
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
        textstylemenu.Append(ID_TEXT_CODE, _("Code"))
        textstylemenu.Append(ID_TEXT_CITATION, _("Citation"))
        textstylemenu.AppendSeparator()
        textstylemenu.Append(ID_TEXT_REMOVE_STYLES, _("Clear Text Styles"))

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
        self.dirty = false

        #load icons
        icnSave = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "save16.gif"), wx.BITMAP_TYPE_GIF)
        icnBold = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "bold_blue16.gif"), wx.BITMAP_TYPE_GIF)
        icnItalic = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "italic_blue16.gif"), wx.BITMAP_TYPE_GIF)    
        icnUnderline = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "underline_blue16.gif"), wx.BITMAP_TYPE_GIF)

        icnCut = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "cut16.gif"), wx.BITMAP_TYPE_GIF)
        icnCopy = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "copy16.gif"), wx.BITMAP_TYPE_GIF)
        icnPaste = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "paste16.gif"), wx.BITMAP_TYPE_GIF)
        
        icnAlignLeft = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "align_left16.gif"), wx.BITMAP_TYPE_GIF) 
        icnAlignCenter = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "align_centre16.gif"), wx.BITMAP_TYPE_GIF)
        icnAlignRight = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "align_right16.gif"), wx.BITMAP_TYPE_GIF) 
        icnAlignJustify = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "align_justify16.gif"), wx.BITMAP_TYPE_GIF)

        icnIncreaseFont = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "arrowup_blue16.gif"), wx.BITMAP_TYPE_GIF)
        icnDecreaseFont = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "arrowdown_blue16.gif"), wx.BITMAP_TYPE_GIF)

        icnIndent = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "increase_indent16.gif"), wx.BITMAP_TYPE_GIF) 
        icnDedent = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "decrease_indent16.gif"), wx.BITMAP_TYPE_GIF)
        icnBullets = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "bullets16.gif"), wx.BITMAP_TYPE_GIF)
        icnNumbering = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "numbering16.gif"), wx.BITMAP_TYPE_GIF)

        icnColour = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "colour16.gif"), wx.BITMAP_TYPE_GIF)

        icnLink = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "insert_hyperlink16.gif"), wx.BITMAP_TYPE_GIF)
        icnImage = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "image16.gif"), wx.BITMAP_TYPE_GIF) 
        icnHR = wx.Bitmap(os.path.join(self.parent.AppDir, "icons", "horizontal_line16.gif"), wx.BITMAP_TYPE_GIF)
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
        #self.toolbar.AddSimpleTool(ID_INCREASE_FONT, icnIncreaseFont, _("Increase Font Size"), _("Increase Font Size"))
        #self.toolbar.AddSimpleTool(ID_DECREASE_FONT, icnDecreaseFont, _("Decrease Font Size"), _("Decrease Font Size"))
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
        self.fontsizelist = wx.Choice(self.toolbar2, wx.NewId(), choices=self.fontsizes)
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
        self.toolbar2.SetToolBitmapSize(wx.Size(16,16))
        self.toolbar2.Realize()

        #wx.MessageBox("Loading wx.Mozilla...")
        self.notebook = wx.Notebook(self, -1)
        notebooksizer = wx.BoxSizer(wx.VERTICAL)
        notebooksizer.Add(self.notebook, 1, wx.EXPAND, wx.ALL, 4)
        mozillapanel = wx.Panel(self.notebook, -1)
        self.notebook.AddPage(mozillapanel, "Edit")
        self.mozilla = wx.MozillaBrowser(mozillapanel, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
        mozpanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        mozpanelsizer.Add(self.mozilla, 1, wx.EXPAND)
        mozillapanel.SetAutoLayout(True)
        mozillapanel.SetSizerAndFit(mozpanelsizer)

        self.mozilla.MakeEditable()
        sourcepanel = wx.Panel(self.notebook, -1)
        self.notebook.AddPage(sourcepanel, "HTML")

        self.source = wx.stc.StyledTextCtrl(sourcepanel, -1)
        sourcepanelsizer = wx.BoxSizer(wx.HORIZONTAL)
        sourcepanelsizer.Add(self.source, 1, wx.EXPAND)
        sourcepanel.SetAutoLayout(True)
        sourcepanel.SetSizerAndFit(sourcepanelsizer)

        self.source.SetLexer(wx.STC_LEX_HTML)
        #self.source.SetCodePage(wx.STC_CP_DBCS)
        #self.source.StyleClearAll()
        self.source.StyleSetSpec(wx.STC_STYLE_DEFAULT, "fore:#000000,size:12,face:Arial")
        self.source.StyleSetSpec(wx.STC_STYLE_LINENUMBER, "fore:#000000")
        self.source.StyleSetSpec(wx.STC_H_TAG, "fore:#000099")
        self.source.StyleSetSpec(wx.STC_H_ATTRIBUTE, "fore:#009900")
        self.source.StyleSetSpec(wx.STC_H_VALUE, "fore:#009900")
        self.source.SetProperty("fold.html", "1")

        self.SetAutoLayout(True)
        self.SetSizer(notebooksizer)

        accelerators = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('B'), ID_BOLD),(wx.ACCEL_CTRL, ord('I'), ID_ITALIC), (wx.ACCEL_CTRL, ord('U'), ID_UNDERLINE), (wx.ACCEL_CTRL, ord('S'), ID_SAVE)]) 
        self.SetAcceleratorTable(accelerators)

        EVT_COMBOBOX(self, self.fontlist.GetId(), self.OnFontSelect)
        EVT_TEXT_ENTER(self, self.fontlist.GetId(), self.OnFontSelect)
        EVT_CHOICE(self, self.fontsizelist.GetId(), self.OnFontSizeSelect)
        #EVT_KEY_UP(self.location, self.OnLocationKey)
        #EVT_CHAR(self.location, self.IgnoreReturn)
        #EVT_MENU(self, ID_NEW, self.OnNew)
        EVT_MENU(self, ID_OPEN, self.OnOpen)
        EVT_MENU(self, ID_SAVE, self.OnSave)
        EVT_MENU(self, ID_QUIT, self.OnQuit)
        EVT_CLOSE(self, self.OnQuit)
        EVT_MENU(self, ID_UNDO, self.OnUndo)
        EVT_MENU(self, ID_REDO, self.OnRedo)
        EVT_MENU(self, ID_CUT, self.OnCut)
        EVT_MENU(self, ID_COPY, self.OnCopy)
        EVT_MENU(self, ID_PASTE, self.OnPaste)
        EVT_MENU(self, ID_REMOVE_LINK, self.OnRemoveLink)
        EVT_MENU(self, ID_BOLD, self.OnBoldButton)
        EVT_MENU(self, ID_ITALIC, self.OnItalicButton)
        EVT_MENU(self, ID_UNDERLINE, self.OnUnderlineButton)
        EVT_MENU(self, ID_FONT_COLOR, self.OnFontColorButton)
        EVT_MENU(self, ID_ALIGN_LEFT, self.OnLeftAlignButton)
        EVT_MENU(self, ID_ALIGN_CENTER, self.OnCenterAlignButton)
        EVT_MENU(self, ID_ALIGN_RIGHT, self.OnRightAlignButton)
        EVT_MENU(self, ID_INDENT, self.OnIndentButton)
        EVT_MENU(self, ID_DEDENT, self.OnOutdentButton)
        EVT_MENU(self, ID_INCREASE_FONT, self.OnFontIncreaseButton)
        EVT_MENU(self, ID_DECREASE_FONT, self.OnFontDecreaseButton)
        EVT_MENU(self, ID_BULLETS, self.OnBullet)
        EVT_MENU(self, ID_NUMBERING, self.OnNumbering)
        EVT_MENU(self, ID_FIND, self.OnFind)
        EVT_MENU(self, ID_FIND_NEXT, self.OnFindNext)
        EVT_MENU(self, ID_SELECTALL, self.OnSelectAll)
        EVT_MENU(self, ID_SELECTNONE, self.OnSelectNone)

        EVT_MENU(self, ID_INSERT_IMAGE, self.OnImageButton)
        EVT_MENU(self, ID_INSERT_LINK, self.OnLinkButton)
        EVT_MENU(self, ID_INSERT_HR, self.OnHRButton)
        EVT_MENU(self, ID_INSERT_TABLE, self.OnTableButton)
        EVT_MENU(self, ID_INSERT_BOOKMARK, self.OnBookmarkButton)
        EVT_MENU(self, ID_INSERT_FLASH, self.OnFlashButton)

        EVT_MENU(self, ID_EDITIMAGE, self.OnImageProps)
        EVT_MENU(self, ID_EDITLINK, self.OnLinkProps)
        EVT_MENU(self, ID_EDITOL, self.OnListProps)
        EVT_MENU(self, ID_EDITTABLE, self.OnTableProps)
        EVT_MENU(self, ID_EDITROW, self.OnRowProps)
        EVT_MENU(self, ID_EDITCELL, self.OnCellProps)

        EVT_MENU(self, ID_TEXT_SUP, self.OnSuperscript)
        EVT_MENU(self, ID_TEXT_SUB, self.OnSubscript)
        EVT_MENU(self, ID_TEXT_CODE, self.OnCode)
        EVT_MENU(self, ID_TEXT_CITATION, self.OnCitation)
        EVT_MENU(self, ID_TEXT_REMOVE_STYLES, self.OnRemoveStyle)

        #EVT_MENU(self, ID_SPELLCHECK, self.OnSpellCheck)
        #EVT_UPDATE_UI(self, -1, self.UpdateStatus)
        EVT_COMMAND_FIND(self, -1, self.OnFindClicked)
        EVT_COMMAND_FIND_NEXT(self, -1, self.OnFindNext)
        EVT_COMMAND_FIND_CLOSE(self, -1, self.OnFindClose)
        EVT_CHAR(self.mozilla, self.OnKeyEvent)
        #EVT_IDLE(self, self.UpdateStatus)
        EVT_CHAR(self.source, self.OnKeyEvent)
        EVT_KEY_DOWN(self.mozilla, self.OnCharEvent)
        EVT_KEY_UP(self.mozilla, self.OnKeyEvent)
        EVT_MOZILLA_RIGHT_CLICK(self.mozilla, self.mozilla.GetId(), self.OnRightClick)
        #EVT_MOZILLA_LOAD_COMPLETE(self.mozilla, self.mozilla.GetId(), self.OnLoadComplete)
        EVT_MOUSE_EVENTS(self.mozilla, self.UpdateStatus)

        #btnSizer.Add(self.location, 1, wx.EXPAND|wx.ALL, 2)
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        sizer.Add(self.toolbar2, 0, wx.EXPAND)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        #self.mozilla.EditCommand("cmd_fontFace", self.fonts[0])
        #self.location.Append(self.current)

        self.SetSizer(sizer)
        self.SetAutoLayout(true)
        self.filename = ""
        self.notebook.SetSelection(0)
        #self.mozilla.LoadPage("about:blank")
        EVT_SIZE(self, self.OnSize)
        EVT_CLOSE(self, self.OnQuit)

        EVT_NOTEBOOK_PAGE_CHANGING(self.notebook, self.notebook.GetId(), self.OnPageChanging)
        if wx.Platform == '__WXMSW__':
            EVT_CHAR(self.notebook, self.SkipNotebookEvent)

    def SkipNotebookEvent(self, evt):
        evt.Skip()

    def SkipEvent(self, evt):
        pass

    def OnSelectAll(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.SelectAll()
        else:
            self.source.SelectAll()

    def OnSelectNone(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.SelectNone()
        else:
            self.source.SetSelection(-1, self.source.GetCurrentPos())

    def OnSpellCheck(self, evt):
        self.mozilla.StartSpellCheck()
        #wx.MessageBox(self.mozilla.GetNextMisspelledWord())
        self.mozilla.StopSpellChecker()

    def OnLoadComplete(self, evt):
        if string.find(self.mozilla.GetPage(), '<base href="about:blank">') != -1:
            pagetext = string.replace(self.mozilla.GetPage(), '<base href="about:blank">', '')
            self.mozilla.SetPage(pagetext)
            self.mozilla.UpdateBaseURI()
            self.mozilla.Reload()

    def OnPageChanging(self, evt):
        if evt.GetOldSelection() == 1:
            self.mozilla.SetPage(self.source.GetText())
            self.mozilla.UpdateBaseURI()
            self.mozilla.Reload()
        else:
            pagetext = self.mozilla.GetPage()
            self.source.SetText(pagetext)
            seltext = self.mozilla.GetSelection()
            if seltext != "":
                index = string.find(pagetext, seltext)
                self.source.SetSelection(index, index+len(seltext))
        evt.Skip()

    def OnTableButton(self, evt):
        tableProps = []
        mydialog = CreateTableDialog(self)
        if mydialog.ShowModal() == wx.ID_OK:
            tablehtml = """<table border="%s" width="%s" height="%s">""" % ("1", mydialog.twidth, mydialog.theight)
            for counter in range(0, int(mydialog.trows)):
                tablehtml = tablehtml + "<tr>"
                for counter in range(0, int(mydialog.tcolumns)):
                    tablehtml = tablehtml + "<td>&nbsp</td>"
                tablehtml = tablehtml + "</tr>"
            tablehtml = tablehtml + "</table>"
            self.mozilla.InsertHTML(tablehtml)
            self.dirty = true
        mydialog.Destroy()
        
    def OnTableProps(self, evt):
        tableProps = []
        if self.mozilla.IsElementInSelection("table"):
            tableProps.append(self.mozilla.GetElementAttribute("table", "width"))
            tableProps.append(self.mozilla.GetElementAttribute("table", "height"))
            tableProps.append(self.mozilla.GetElementAttribute("table", "align"))
            tableProps.append(self.mozilla.GetElementAttribute("table", "border"))
            tableProps.append(self.mozilla.GetElementAttribute("table", "cellspacing"))
            tableProps.append(self.mozilla.GetElementAttribute("table", "cellpadding"))
            mydialog = TablePropsDialog(self, tableProps)
            if mydialog.ShowModal() == wx.ID_OK:
                self.mozilla.SetElementAttribute("width", mydialog.tableProps[0])
                self.mozilla.SetElementAttribute("height", mydialog.tableProps[1])
                self.mozilla.SetElementAttribute("align", mydialog.tableProps[2])
                self.mozilla.SetElementAttribute("border", mydialog.tableProps[3])
                self.mozilla.SetElementAttribute("cellspacing", mydialog.tableProps[4])
                self.mozilla.SetElementAttribute("cellpadding", mydialog.tableProps[5])
                self.dirty = true
            mydialog.Destroy()

    def OnRowProps(self, evt):
        rowProps = []
        if self.mozilla.IsElementInSelection("tr"):
            rowProps.append(self.mozilla.GetElementAttribute("tr", "width"))
            rowProps.append(self.mozilla.GetElementAttribute("tr", "height"))
            rowProps.append(self.mozilla.GetElementAttribute("tr", "align"))
            rowProps.append(self.mozilla.GetElementAttribute("tr", "valign"))
            mydialog = CellPropsDialog(self, rowProps)
            mydialog.SetTitle("Row Properties")
            if mydialog.ShowModal() == wx.ID_OK:
                self.mozilla.SetElementAttribute("width", mydialog.rowProps[0])
                self.mozilla.SetElementAttribute("height", mydialog.rowProps[1])
                self.mozilla.SetElementAttribute("align", mydialog.rowProps[2])
                self.mozilla.SetElementAttribute("valign", mydialog.rowProps[3])
                self.dirty = true
            mydialog.Destroy()

    def OnCellProps(self, evt):
        rowProps = []
        if self.mozilla.IsElementInSelection("td"):
            rowProps.append(self.mozilla.GetElementAttribute("td", "width"))
            rowProps.append(self.mozilla.GetElementAttribute("td", "height"))
            rowProps.append(self.mozilla.GetElementAttribute("td", "align"))
            rowProps.append(self.mozilla.GetElementAttribute("td", "valign"))
            mydialog = CellPropsDialog(self, rowProps)
            mydialog.SetTitle("Cell Properties")
            if mydialog.ShowModal() == wx.ID_OK:
                self.mozilla.SetElementAttribute("width", mydialog.rowProps[0])
                self.mozilla.SetElementAttribute("height", mydialog.rowProps[1])
                self.mozilla.SetElementAttribute("align", mydialog.rowProps[2])
                self.mozilla.SetElementAttribute("valign", mydialog.rowProps[3])
                self.dirty = true
            mydialog.Destroy()

    def OnImageProps(self, evt):
        imageProps = []
        if self.mozilla.IsElementInSelection("img"):
            imageProps.append(self.mozilla.GetElementAttribute("img", "src"))
            imageProps.append(self.mozilla.GetElementAttribute("img", "alt"))
            imageProps.append(self.mozilla.GetElementAttribute("img", "width"))
            imageProps.append(self.mozilla.GetElementAttribute("img", "height"))
            imageProps.append(self.mozilla.GetElementAttribute("img", "align"))
        mydialog = ImagePropsDialog(self, imageProps)
        if mydialog.ShowModal() == wx.ID_OK:
            self.mozilla.SetElementAttribute("src", mydialog.imageProps[0])
            self.mozilla.SetElementAttribute("alt", mydialog.imageProps[1])
            if not mydialog.imageProps[2] == "":
                self.mozilla.SetElementAttribute("width", mydialog.imageProps[2])
            if not mydialog.imageProps[3] == "":
                self.mozilla.SetElementAttribute("height", mydialog.imageProps[3])
            if not mydialog.imageProps[4] == "":
                self.mozilla.SetElementAttribute("align", mydialog.imageProps[4])
            self.dirty = true
        mydialog.Destroy()

    def OnLinkProps(self, evt):
        linkProps = []
        if self.mozilla.IsElementInSelection("a"):
            if self.mozilla.GetElementAttribute("a", "href") != "":
                linkProps.append(self.mozilla.GetElementAttribute("a", "href"))
                linkProps.append(self.mozilla.GetElementAttribute("a", "target"))
                mydialog = LinkPropsDialog(self, linkProps)
                if mydialog.ShowModal() == wx.ID_OK:
                    self.mozilla.SetElementAttribute("href", mydialog.linkProps[0])
                    self.mozilla.SetElementAttribute("target", mydialog.linkProps[1])
                    self.dirty = true
                mydialog.Destroy()
            elif self.mozilla.GetElementAttribute("a", "name") != "":
                linkProps.append(self.mozilla.GetElementAttribute("a", "name"))
                mydialog = BookmarkPropsDialog(self, linkProps)
                if mydialog.ShowModal() == wx.ID_OK:
                    self.mozilla.SetElementAttribute("href", mydialog.linkProps[0])
                    self.dirty = true
                mydialog.Destroy()

    def OnListProps(self, evt):
        listProps = []
        if self.mozilla.IsElementInSelection("ol"):
            listProps.append(self.mozilla.GetElementAttribute("ol", "type"))
            listProps.append(self.mozilla.GetElementAttribute("ol", "start"))
            mydialog = OLPropsDialog(self, listProps)
            if mydialog.ShowModal() == wx.ID_OK:
                self.mozilla.SetElementAttribute("type", mydialog.listProps[0])
                self.mozilla.SetElementAttribute("start", mydialog.listProps[1])
                self.dirty = true
            mydialog.Destroy()
        if self.mozilla.IsElementInSelection("ul"):
            listProps.append(self.mozilla.GetElementAttribute("ul", "type"))
            mydialog = ULPropsDialog(self, listProps)
            if mydialog.ShowModal() == wx.ID_OK:
                self.mozilla.SetElementAttribute("type", mydialog.listProps[0])
                self.dirty = true
            mydialog.Destroy()

    def OnQuit(self, evt):
        try:
            self.running = false
            if self.dirty == true:
                dlg = wx.MessageDialog(self, _("Your file contains unsaved changes. Would you like to save now?"), _("Save File?"), wx.YES_NO)
                result = dlg.ShowModal()
                if result == wx.ID_YES:
                    self.OnSave(evt)
                elif result == wx.ID_CANCEL:
                    return
            self.MakeModal(False)
            self.Show(False)
            self.parent.Update()
            self.Destroy()
        except Exception, ex:
            global log
            message = utils.getStdErrorMessage("UnknownError")
            log.write(message)
            wx.MessageBox(message, _("Unknown Error Occurred"), wx.ICON_ERROR)
            
    def OnRightClick(self, evt):
        popupmenu = wx.Menu()
        if evt.GetImageSrc() != "" and self.mozilla.IsElementInSelection("img"):
            popupmenu.Append(ID_EDITIMAGE, "Image Properties")
        if evt.GetLink() != "" and self.mozilla.IsElementInSelection("href"):
            popupmenu.Append(ID_EDITLINK, "Link Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Link")
        elif evt.GetLink() != "" and self.mozilla.IsElementInSelection("a"):
            popupmenu.Append(ID_EDITBOOKMARK, "Bookmark Properties")
            popupmenu.Append(ID_REMOVE_LINK, "Remove Bookmark")
        if self.mozilla.IsElementInSelection("ol") or self.mozilla.IsElementInSelection("ul"):
            popupmenu.Append(ID_EDITOL, "Bullets and Numbering")
        if self.mozilla.IsElementInSelection("table"):
            popupmenu.Append(ID_EDITTABLE, "Table Properties")
        if self.mozilla.IsElementInSelection("tr"):
            popupmenu.Append(ID_EDITROW, "Row Properties")
        if self.mozilla.IsElementInSelection("td"):
            popupmenu.Append(ID_EDITCELL, "Cell Properties")
        position = evt.GetPosition()
        position[0] = position[0] + self.notebook.GetPosition()[0]
        position[1] = position[1] + self.notebook.GetPosition()[1]
        self.PopupMenu(popupmenu, position)
        evt.Skip()

    def OnSize(self, evt):
        self.Layout()

    def OnCharEvent(self, evt):
        self.dirty = true
        self.OnKeyEvent(evt)

    def OnKeyEvent(self, evt):
        #for now, we're just interested in knowing when to ask for save
        self.UpdateStatus(evt)

    def OnFind(self, evt):
        data = wx.FindReplaceData()
        dlg = wx.FindReplaceDialog(self, data, "Find")
        dlg.Show()

    def OnFindClicked(self, evt):
        type = evt.GetEventType()
        matchCase = false
        matchWholeWord = false
        searchBackwards = false

        flags = evt.GetFlags()
        if flags and wx.FR_MATCHCASE:
            matchCase = true
        if flags and wx.FR_WHOLEWORD:
            matchWholeWord = true
        if flags and wx.FR_DOWN:
            searchBackwards = false
        else:
            searchBackwards = true
        self.mozilla.Find(evt.GetFindString(), matchCase, matchWholeWord, true, searchBackwards)

    def OnFindNext(self, evt):
        self.mozilla.FindNext()

    def OnFindClose(self, evt):
        evt.GetDialog().Destroy()       

    def OnSuperscript(self, evt):
        self.mozilla.EditCommand("cmd_superscript")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnSubscript(self, evt):
        self.mozilla.EditCommand("cmd_subscript")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnCode(self, evt):
        self.mozilla.EditCommand("cmd_code")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnCitation(self, evt):
        self.mozilla.EditCommand("cmd_cite")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnRemoveStyle(self, evt):
        self.mozilla.EditCommand("cmd_removeStyles")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnRemoveLink(self, evt):
        self.mozilla.EditCommand("cmd_removeLinks")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnBullet(self, evt):
        self.mozilla.EditCommand("cmd_ul")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnNumbering(self, evt):
        self.mozilla.EditCommand("cmd_ol")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnBoldButton(self, evt):
        self.mozilla.EditCommand("cmd_bold")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnItalicButton(self, evt):
        self.mozilla.EditCommand("cmd_italic")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnUnderlineButton(self, evt):
        self.mozilla.EditCommand("cmd_underline")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnLeftAlignButton(self, evt):
        self.mozilla.EditCommand("cmd_align", "left")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnCenterAlignButton(self, evt):
        self.mozilla.EditCommand("cmd_align", "center")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnRightAlignButton(self, evt):
        self.mozilla.EditCommand("cmd_align", "right")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnOutdentButton(self, evt):
        self.mozilla.EditCommand("cmd_outdent")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnIndentButton(self, evt):
        self.mozilla.EditCommand("cmd_indent")
        self.UpdateStatus(evt)
        self.dirty = true

    def OnUndo(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.EditCommand("cmd_undo")
        else:
            self.source.Undo()
        self.UpdateStatus(evt)
        self.dirty = true

    def OnFontSelect(self, evt):
        self.mozilla.EditCommand("cmd_fontFace", self.fontlist.GetStringSelection())
        self.dirty = true

    def OnFontSizeSelect(self, evt):
        self.mozilla.EditCommand("cmd_fontSize", self.fontsizelist.GetStringSelection())
        self.dirty = true

    def OnRedo(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.EditCommand("cmd_redo")
        else:
            self.source.Redo()
        self.dirty = true

    def OnCut(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.EditCommand("cmd_cut")
        else:
            self.source.Cut()
        self.dirty = true

    def OnCopy(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.EditCommand("cmd_copy")
        else:
            self.source.Copy()
        self.dirty = true

    def OnPaste(self, evt):
        if self.notebook.GetSelection() == 0:
            self.mozilla.EditCommand("cmd_paste")
        else:
            self.source.Paste()
        self.dirty = true

    def OnLinkButton(self, evt):    
        linkProps = []
        linkProps.append("")
        linkProps.append("")
        mydialog = LinkPropsDialog(self, linkProps)
        if mydialog.ShowModal() == wx.ID_OK:
            self.mozilla.EditCommand("cmd_insertLinkNoUI", mydialog.linkProps[0])
            if self.mozilla.IsElementInSelection("a"):
                #self.mozilla.SelectElement("a")
                self.mozilla.SetElementAttribute("target", mydialog.linkProps[1])
        mydialog.Destroy()

    def OnBookmarkButton(self, evt):    
        dialog = BookmarkPropsDialog(self, [""])
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            #html = "<a href='' name='" + dialog.bookmarkProps[0] + "'></a>"
            html = "<a name=\"" + dialog.bookmarkProps[0] + "\"></a>"
            #wx.MessageBox(html)
            self.mozilla.InsertHTML(html)
            self.dirty = true
        dialog.Destroy()

    def OnFlashButton(self, evt):
        dialog = wx.FileDialog(self, _("Choose a file"), "", "", _("Macromedia Flash Files") + " (*.swf)|*.swf", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            if os.path.exists(dialog.GetPath()):
                CopyFile(dialog.GetFilename(), dialog.GetDirectory(), os.path.join(self.parent.pub.directory, "File"))
            code = HTMLTemplates.flashTemp
            code = string.replace(code, "_filename_", "../File/" + dialog.GetFilename())
            code = string.replace(code, "_autostart_", "True")
            self.mozilla.InsertHTML(code)
        dialog.Destroy()

    def OnImageButton(self, evt):
        imageFormats = _("Image files") +"|*.gif;*.jpg;*.png;*.jpeg;*.bmp"
        dialog = wx.FileDialog(self, _("Select an image"), "","", imageFormats, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            if os.path.exists(dialog.GetPath()):
                CopyFile(dialog.GetFilename(), dialog.GetDirectory(), os.path.join(self.parent.pub.directory, "Graphics"))
            self.mozilla.EditCommand("cmd_insertImageNoUI", "../Graphics/" + dialog.GetFilename())
        self.dirty = true

    def OnHRButton(self, evt):  
        self.mozilla.EditCommand("cmd_insertHR")
        self.dirty = true

    def OnFontIncreaseButton(self, evt):    
        self.mozilla.EditCommand("cmd_increaseFont")
        self.dirty = true

    def OnFontDecreaseButton(self, evt):    
        self.mozilla.EditCommand("cmd_decreaseFont")
        self.dirty = true

    def OnFontColorButton(self, evt):
        dlg = wx.ColourDialog(self)
        dlg.GetColourData().SetChooseFull(true)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData().GetColour().Get() #RGB tuple
            red = string.replace(str(hex(data[0])), "0x", "")
            if len(red) == 1:
                red = "0" + red
            green = string.replace(str(hex(data[1])), "0x", "")
            if len(green) == 1:
                green = "0" + green
            blue = string.replace(str(hex(data[2])), "0x", "")
            if len(blue) == 1:
                blue = "0" + blue
            value = "#" + red + green + blue
            #print value
            self.mozilla.EditCommand("cmd_fontColor", value)
        dlg.Destroy()
        self.dirty = true

    def OnLocationSelect(self, evt):
        #url = self.location.GetStringSelection()
        self.log.write('OnLocationSelect: %s\n' % url)
        self.mozilla.LoadURL(url)

    def OnLocationKey(self, evt):
        if evt.KeyCode() == WXK_RETURN:
            #URL = self.location.GetValue()
            #self.location.Append(URL)
            self.mozilla.LoadURL(URL)
        else:
            evt.Skip()

    def UpdateStatus(self, evt):
        self.toolbar2.ToggleTool(ID_BOLD, self.mozilla.GetCommandState("cmd_bold", "state_all"))
        self.toolbar2.ToggleTool(ID_ITALIC, self.mozilla.GetCommandState("cmd_italic", "state_all"))
        self.toolbar2.ToggleTool(ID_UNDERLINE, self.mozilla.GetCommandState("cmd_underline", "state_all"))
        self.toolbar2.ToggleTool(ID_BULLETS, self.mozilla.GetCommandState("cmd_ul", "state_all"))
        self.toolbar2.ToggleTool(ID_NUMBERING, self.mozilla.GetCommandState("cmd_ol", "state_all"))
        alignment = self.mozilla.GetStateAttribute("cmd_align")
        if alignment == "left":
            self.toolbar2.ToggleTool(ID_ALIGN_LEFT, true)
        else:
            self.toolbar2.ToggleTool(ID_ALIGN_LEFT, false)

        if alignment == "center":
            self.toolbar2.ToggleTool(ID_ALIGN_CENTER, true)
        else:
            self.toolbar2.ToggleTool(ID_ALIGN_CENTER, false)

        if alignment == "right":
            self.toolbar2.ToggleTool(ID_ALIGN_RIGHT, true)
        else:
            self.toolbar2.ToggleTool(ID_ALIGN_RIGHT, false)

        fontsize = self.mozilla.GetStateAttribute("cmd_fontSize")
        print "Fontsize is: " + fontsize
        if fontsize == "":
            self.fontsizelist.SetStringSelection("3")
        else:
            self.fontsizelist.SetStringSelection(fontsize)
        
        fontname = self.mozilla.GetStateAttribute("cmd_fontFace")
        if fontname == "":
            self.fontlist.SetValue(self.fonts[0]) #just show the default
        else:   
            self.fontlist.SetValue(fontname)
        evt.Skip()

    def IgnoreReturn(self, evt):
        if evt.GetKeyCode() != WXK_RETURN:
            evt.Skip()

    def OnNew(self, event):
        self.mozilla.LoadURL("about:blank")

    def OnOpen(self, event):
        dlg = wx.FileDialog(self, _("Select a file"), "", "", _("Web Pages") + "(*.htm,*.html)|*.html;*.htm", wx.OPEN)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.current = dlg.GetPath()
            if (self.current != self.filename):
                wx.MessageBox(self.current + "\n" + self.filename)
            self.mozilla.LoadURL(self.current)
        dlg.Destroy()

    def OnSave(self, event):
        if self.notebook.GetSelection() == 1:
            self.mozilla.SetPage(self.source.GetText())
        filename = os.path.join(self.parent.pub.directory, self.currentItem.content.filename)
        try:
            result = self.mozilla.SavePage(filename, False)
            if result:
                print "Hello!"
                self.mozilla.UpdateBaseURI()
                self.mozilla.Reload()
                self.dirty = False
            else:
                message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":filename})
                wx.MessageBox(message, _("Unable to Save File"), wx.ICON_ERROR)
        except IOError:
            message = utils.getStdErrorMessage("IOError", {"type":"write", "filename":filename})
            global log
            log.write(message)
            wx.MessageBox(message, _("Unable to Save File"), wx.ICON_ERROR)

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

class LinkPropsDialog(wx.Dialog):
    def __init__(self, parent, linkProps):
        wx.Dialog.__init__ (self, parent, -1, _("Link Properties"), wx.DefaultPosition,wx.Size(400,200))
        self.parent = parent
        self.linkProps = linkProps

        self.lblURL = wx.StaticText(self, -1, _("Location:"))
        self.cmbURL = wx.ComboBox(self, -1, linkProps[0], style=wx.CB_DROPDOWN)
        self.btnURL = wx.Button(self, -1, _("Select File..."))
        #self.lblPage = wx.StaticText(self, -1, _("Link to Page"))
        #self.cmbPage = wx.Choice(self, -1)
        self.LoadPages(self.parent.parent.pub.nodes)
        self.chkNewWindow = wx.CheckBox(self, -1, _("Open in new window"))
        if linkProps[1] == "_blank":
            self.chkNewWindow.SetValue(1)
        else:
            self.chkNewWindow.SetValue(0)
        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnOK.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblURL, 0, wx.ALL, 4)
        urlsizer = wx.BoxSizer(wx.HORIZONTAL)
        urlsizer.Add(self.cmbURL, 0, wx.EXPAND | wx.RIGHT | wx.TOP | wx.BOTTOM, 4)
        urlsizer.Add(self.btnURL, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        self.sizer.Add(urlsizer, 0, wx.ALL, 4)
        #self.sizer.Add(self.lblPage, 0)
        #self.sizer.Add(self.cmbPage, 0, wx.EXPAND)
        self.sizer.Add(self.chkNewWindow)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((100, 25), 1, wx.EXPAND)
        btnsizer.Add(self.btnOK)
        btnsizer.Add(self.btnCancel)

        self.sizer.Add(btnsizer, 0, wx.EXPAND)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOKClicked)
        EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)
        EVT_COMBOBOX(self.cmbURL, self.cmbURL.GetId(), self.OnSelectPage)

    def LoadPages(self, nodes, indent=0):
        if len(nodes) > 0:
            for node in nodes:
                text = ""
                if indent > 0:
                    text = text + " " * indent
                text = text + node.content.metadata.name

                self.cmbURL.Append(text, node)
                if len(node.children) > 0:
                    self.LoadPages(node.children, indent + 2)

    def OnOKClicked(self, evt):
        self.linkProps[0] = self.cmbURL.GetValue()
        if self.chkNewWindow.IsChecked():
            self.linkProps[1] = "_blank"
        else:
            self.linkProps[1] = ""
        self.EndModal(wx.ID_OK)

    def OnSelectPage(self, evt):
        page = self.cmbURL.GetClientData(evt.GetSelection())
        if publisher:
            self.cmbURL.SetStringSelection(publisher.GetFilename(page.content.filename))
        else:
            self.cmbURL.SetValue("../File/" + page.content.filename)

    def OnSelectFile(self, evt):
        dialog = wx.FileDialog(self, _("Select a file"), "","", _("All files") + "|*.*", wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filedir = os.path.join(self.parent.parent.pub.directory, "File")
            if os.path.exists(dialog.GetPath()):
                if dialog.GetDirectory() != filedir:
                    CopyFile(dialog.GetFilename(), dialog.GetDirectory(), filedir)
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

        EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOK)

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

        EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOKClicked)
        EVT_SPIN(self, self.spnStartNum.GetId(), self.OnSpin)
        #EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)

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

        EVT_BUTTON(self.btnOK, self.btnOK.GetId(), self.OnOKClicked)
        #EVT_SPIN(self, self.spnStartNum.GetId(), self.OnSpin)
        #EVT_BUTTON(self.btnURL, self.btnURL.GetId(), self.OnSelectFile)

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

        EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)
        EVT_BUTTON(self, self.btnImageSrc.GetId(), self.OnSelectImage)

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
                    CopyFile(dialog.GetFilename(), dialog.GetDirectory(), graphicsdir)
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
            self.cmbAlign.SetStringSelection(string.lower(rowProps[2]))
        else:
            self.cmbAlign.SetSelection(0)
    
        self.lblVAlign = wx.StaticText(self, -1, _("Vertical Alignment:"))
        self.cmbVAlign = wx.Choice(self, -1, choices=["top", "middle", "bottom"])
        if rowProps[3] != "":
            self.cmbVAlign.SetStringSelection(string.lower(rowProps[3]))
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

        EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)

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

        EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)

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

class CreateTableDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__ (self, parent, -1, _("Table Properties"))
        height = 20
        if wx.Platform == "__WXMAC__":
            height = 25
        self.parent = parent
        self.trows = "1"
        self.tcolumns = "1"
        self.twidth= "100"
        self.theight = "100"

        self.lblRows = wx.StaticText(self, -1, _("Rows:"))
        self.txtRows = wx.TextCtrl(self, -1, "1")
        self.lblColumns = wx.StaticText(self, -1, _("Columns:"))
        self.txtColumns = wx.TextCtrl(self, -1, "1")

        self.sizebox = wx.StaticBox(self, -1, "Size")
        #self.radOriginalSize = wx.RadioBox(self, -1, _("Actual size"))
        #self.radResizeImage = wx.RadioBox(self, -1, _("Custom size"))
        self.lblWidth = wx.StaticText(self, -1, _("Width:"))
        self.txtWidth = wx.TextCtrl(self, -1, "100")
        self.cmbWidthType = wx.Choice(self, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbWidthType.SetStringSelection(_("Percent"))
        self.lblHeight = wx.StaticText(self, -1, _("Height:"))
        self.txtHeight = wx.TextCtrl(self, -1, "100")
        self.cmbHeightType = wx.Choice(self, -1, choices=[_("Percent"), _("Pixels")])
        self.cmbHeightType.SetStringSelection(_("Percent"))

        self.btnOK = wx.Button(self, wx.ID_OK, _("OK"))
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.lblRows, 0, wx.ALL, 4)
        self.sizer.Add(self.txtRows, 0, wx.ALL, 4)
        self.sizer.Add(self.lblColumns, 0, wx.ALL, 4)
        self.sizer.Add(self.txtColumns, 0, wx.ALL, 4)
        boxsizer = wx.StaticBoxSizer(self.sizebox, wx.VERTICAL)
        #boxsizer.Add(self.radOriginalSize, 0)
        #boxsizer.Add(self.radResizeImage, 0)
        size_sizer = wx.GridSizer(2, 3, 3, 3)
        size_sizer.Add(self.lblWidth, 0)
        size_sizer.Add(self.txtWidth, 0)
        size_sizer.Add(self.cmbWidthType, 0)
        size_sizer.Add(self.lblHeight, 0)
        size_sizer.Add(self.txtHeight, 0)
        size_sizer.Add(self.cmbHeightType, 0)
        boxsizer.Add(size_sizer)
        self.sizer.Add(boxsizer, 0)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add((100, 25), 1, wx.EXPAND | wx.ALL, 4)
        btnsizer.Add(self.btnOK, 0, wx.ALL, 4)
        btnsizer.Add(self.btnCancel, 0, wx.ALL, 4)
        self.sizer.Add(btnsizer, 0, wx.ALL, 4)
        self.SetSizerAndFit(self.sizer)
        self.Layout()

        EVT_BUTTON(self, self.btnOK.GetId(), self.OnOKClicked)

    def OnOKClicked(self, evt):
        self.trows = self.txtRows.GetValue()
        self.tcolumns = self.txtColumns.GetValue() 
        self.twidth = self.txtWidth.GetValue()
        if self.cmbWidthType.GetStringSelection() == _("Percent"):
            self.twidth = self.twidth + "%"
        
        self.theight = self.txtHeight.GetValue()
        if self.cmbHeightType.GetStringSelection() == _("Percent"):
            self.theight = self.theight + "%"
        self.EndModal(wx.ID_OK)

if __name__ != "__main__":
    class EditorDialog:
        def __init__(self, parent, node):
            self.parent = parent
            self.node = node
    
        def ShowModal(self):
            if isinstance(self.node, conman.conman.ConNode):
                filename = self.node.content.filename
            
            elif isinstance(self.node, ims.contentpackage.Item):
                resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, self.node)
                filename = eclassutils.getEClassPageForIMSResource(resource)
                if not filename:
                    filename = resource.getFilename()

            self.filename = os.path.join(settings.ProjectDir, filename)
            if not os.path.exists(self.filename):
                global htmlpage
                file = utils.openFile(self.filename, "w")
                file.write(htmlpage)
                file.close()

            #until we get editing fixed...
            use_builtin = False
            if settings.AppSettings["HTMLEditor"] != "":
                guiutils.openInHTMLEditor(os.path.join(settings.ProjectDir, "Text", self.selectText.GetValue()))
                use_builtin = True
            else:
                use_builtin = True

            if use_builtin:
                global mozilla_available
                if mozilla_available:
                    self.frame = EditorFrame(self.parent)
                    #self.frame.mozilla.LoadURL("about:blank")
                    self.frame.currentItem = self.currentItem
                    self.frame.mozilla.LoadURL(self.filename)
                    self.frame.MakeModal(True)
                    self.frame.Show()
            return wx.ID_OK

class MyApp(wx.App):
    def OnInit(self):
        self.frame = EditorFrame(None)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
