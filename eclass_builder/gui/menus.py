import wx
from gui.ids import *

def getFileMenu():
    # File menu
    FileMenu = wx.Menu()
    FileMenu.Append(ID_NEW, "&" + _("New"), _("Create a New Project"))
    FileMenu.Append(ID_OPEN, "&" +_("Open"), _("Open an Existing Project"))
    FileMenu.Append(ID_SAVE, "&" + _("Save") + "\tCTRL+S", _("Save the Current Project"))
    FileMenu.Append(ID_CLOSE, "&" + _("Close"), _("Close the Current Project"))
    FileMenu.AppendSeparator()
    
    PrevMenu = wx.Menu()
    PrevMenu.Append(ID_PREVIEW, _("Web Browser"),  _("Preview EClass in web browser"))
    FileMenu.AppendMenu(wx.NewId(), _("Preview"), PrevMenu)
    
    FileMenu.Append(ID_REFRESH_THEME, _("Refresh Theme"), "Reapply current theme to pages.")
    FileMenu.AppendSeparator()
    
    FileMenu.Append(ID_IMPORT_PACKAGE, _("Import Package"))
    
    PubMenu = wx.Menu()
    PubMenu.Append(ID_PUBLISH, _("To web site"), _("Publish EClass to a web server"))
    PubMenu.Append(ID_PUBLISH_CD, _("To CD-ROM"), _("Publish EClass to a CD-ROM"))
    #PubMenu.Append(ID_PUBLISH_PDF, _("To PDF"))
    PubMenu.Append(ID_PUBLISH_IMS, _("IMS Content Package"))
    PubMenu.Append(ID_PUBLISH_EPUB, _("ePub Package"))
    FileMenu.AppendMenu(ID_PUBLISH_MENU, "&" + _("Publish"), PubMenu, "")
    
    FileMenu.AppendSeparator()
    FileMenu.Append(ID_PROPS, _("Project Settings"), _("View and edit project settings"))
    FileMenu.AppendSeparator()
    FileMenu.Append(ID_EXIT, "&" + _("Exit"), _("Exit this Application"))
    
    return FileMenu
    
def getEditMenu():
    EditMenu = wx.Menu()
    EditMenu.Append(ID_CUT, _("Cut")+"\tCTRL+X")
    EditMenu.Append(ID_COPY, _("Copy")+"\tCTRL+C")

    PasteMenu = wx.Menu()
    PasteMenu.Append(ID_PASTE_BELOW, _("Paste After")+"\tCTRL+V")
    PasteMenu.Append(ID_PASTE_CHILD, _("Paste As Child"))
    EditMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu)
    
    #EditMenu.AppendSeparator()
    #EditMenu.Append(ID_FIND_IN_PROJECT, _("Find in Project"))
    
    return EditMenu
    
def getInsertMenu():
    InsertMenu = wx.Menu()
    InsertMenu.Append(ID_INSERT_LINK, _("Hyperlink") + "\tCTRL+L")
    InsertMenu.Append(ID_INSERT_BOOKMARK, _("Bookmark") + "\tCTRL+SHIFT+B")
    InsertMenu.AppendSeparator()
    InsertMenu.Append(ID_INSERT_IMAGE, _("Image..."))
    InsertMenu.Append(ID_INSERT_TABLE, _("Insert Table"))
    return InsertMenu    

def getFormatMenu():
    FormatMenu = wx.Menu()
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
    FormatMenu.AppendMenu(wx.NewId(), _("Text Style"), textstylemenu)
    FormatMenu.AppendSeparator()
    FormatMenu.Append(ID_CLEANUP_HTML, _("Clean Up HTML"))
    return FormatMenu
    
def getPageMenu(openWithMenu=None):
    PageMenu = wx.Menu()
    PageMenu.Append(ID_ADD_MENU, _("Add New"))
    PageMenu.Append(ID_TREE_REMOVE, _("Remove Page"), _("Remove the current page"))     
    PageMenu.AppendSeparator()
    PageMenu.Append(ID_IMPORT_FILE, _("Import file..."))
    PageMenu.AppendSeparator()
    PageMenu.Append(ID_CUT, _("Cut")+"\tCTRL+X")
    PageMenu.Append(ID_COPY, _("Copy")+"\tCTRL+C")
    
    PasteMenu2 = wx.Menu()
    PasteMenu2.Append(ID_PASTE_BELOW, _("Paste After")+"\tCTRL+V")
    PasteMenu2.Append(ID_PASTE_CHILD, _("Paste As Child"))
    PageMenu.AppendMenu(ID_PASTE, _("Paste"), PasteMenu2)
    
    PageMenu.AppendSeparator()
    PageMenu.Append(ID_EDIT_ITEM, _("Edit Page"), _("Edit the currently selected page"))
    
    if openWithMenu:
        PageMenu.AppendMenu(ID_OPEN_ITEM, _("Open With"), openWithMenu)
    
    PageMenu.Append(ID_TREE_MOVEUP, _("Move Page Up"), _("Move the selected page higher in the tree"))
    PageMenu.Append(ID_TREE_MOVEDOWN, _("Move Page Down"), _("Move the selected page lower in the tree"))   
    PageMenu.AppendSeparator()
    PageMenu.Append(ID_UPLOAD_PAGE, _("Upload Page"), _("Upload Page to FTP Server"))
    PageMenu.AppendSeparator()
    PageMenu.Append(ID_TREE_EDIT, _("Page Properties"), _("Edit Page Properties"))
    
    return PageMenu
    
def getToolsMenu():
    ToolsMenu = wx.Menu()
    #ToolsMenu.Append(ID_THEME, _("Change Theme"))
    ToolsMenu.Append(ID_LINKCHECK, _("Check Links"))
    ToolsMenu.AppendSeparator()
    ToolsMenu.Append(ID_SETTINGS, _("Options"), _("Modify Program Options"))
    
    return ToolsMenu

def getHelpMenu():
    HelpMenu = wx.Menu()
    HelpMenu.Append(wx.ID_ABOUT, _("About Eclass"), _("About Eclass.Builder"))
    HelpMenu.Append(ID_HELP, _("Help"), _("EClass.Builder Help"))
    HelpMenu.Append(ID_BUG, _("Provide Feedback"), _("Submit feature requests or bugs"))
    
    return HelpMenu
    
def getWindowMenu():
    WindowMenu = wx.Menu()
    WindowMenu.Append(ID_CONTACTS, _("Contact Manager"))
    WindowMenu.Append(ID_ERRORLOG, _("Error Viewer"))
    WindowMenu.Append(ID_ACTIVITY, _("Activity Monitor"), _("View status of background activties."))
    
    return WindowMenu
    
def getMenuBar():
    menuBar = wx.MenuBar()
    menuBar.Append(getFileMenu(), "&"+ _("File"))
    menuBar.Append(getEditMenu(), _("Edit"))
    menuBar.Append(getPageMenu(), "&" + _("Page"))
    menuBar.Append(getInsertMenu(), _("Insert"))
    menuBar.Append(getFormatMenu(), _("Format"))
    menuBar.Append(getToolsMenu(), "&" + _("Tools"))
    menuBar.Append(getWindowMenu(), _("Window"))
    menuBar.Append(getHelpMenu(), "&" + _("Help"))
    
    return menuBar
