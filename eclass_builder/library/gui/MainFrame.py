import sys, os, shutil

import wx
import wxaddons.sized_controls as sc
import wxaddons.persistence

import index, index_manager
import gui.autolist as autolist


# EClass.Library internal imports
import library.gui.constants as constants
import library.globals as globals
import New
import Settings
import Props
import errors

menuItems = {
        _("&File"):
        [
            (wx.ID_NEW, _("&New Library"), _("Create a new library")),
            (constants.ID_DEL_LIBRARY, _("&Delete Library"), _("Deletes a library from your collection.")),
        ],
        _("&Library"):
        [
            (constants.ID_ADD_FILES, _("Add File(s)"), 
                        _("Add file(s) to current library.")),
            (constants.ID_ADD_FILES, _("Add Folder(s)"), 
                        _("Add folder(s) to current library.")),
            (constants.ID_REINDEX, _("&Reindex\tCTRL+R"),
                        _("Reindex files in current library.")),
            (-1, "-", "-"),
            (constants.ID_LIB_SETTINGS, _("&Settings"),
                        _("View and set options for current library."))
        ],
        _("&Window"): 
        [
            (constants.ID_ERROR_LOG, _("Error Log"), _("View any program errors.")),
        ],
        _("&Help"): [],

}

errorLog = None

class MainFrame(sc.SizedFrame):
    def __init__(self, *args, **kwargs):
        sc.SizedFrame.__init__(self, *args, **kwargs)
        self.indexManager = index_manager.IndexManager()
        self.files = {}
        self.createMenu()
        
        pane = self.GetContentsPane()
        
        searchPane = sc.SizedPanel(pane, -1)
        searchPane.SetSizerProps(expand=True)
        
        self.srchCtrl = wx.SearchCtrl(searchPane, -1, size=(200, -1))
        self.srchCtrl.SetSizerProps(halign="right")
        self.srchCtrl.Bind(wx.EVT_TEXT, self.OnSearchText)
        
        self.splitter = wx.SplitterWindow(pane, -1, style=wx.NO_BORDER)
        self.splitter.SetSizerProps(expand=True, proportion=1)
        
        self.indexPane = sc.SizedPanel(self.splitter, -1)
        
        self.indexList = wx.ListBox(self.indexPane, -1, wx.DefaultPosition, wx.DefaultSize,
                            self.indexManager.getIndexes())
        self.indexList.SetSizerProps(expand=True, proportion=1, border=(["all"], 0))
        
        self.Bind(wx.EVT_LISTBOX, self.OnIndexSelected, self.indexList)
        
        self.contentsList = autolist.AutoSizeListCtrl(self.splitter, -1, style = wx.LC_REPORT)
        self.contentsList.InsertColumn(0, _("Filename"))
        
        self.splitter.SplitVertically(self.indexPane, self.contentsList, 150)
        
        self.CreateStatusBar()
        
        globals.errorLog = errors.AppErrorLog()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.LoadState("LibraryMainFrame")
        
        #self.props = PropsMiniFrame(self, -1, _("Properties"), wx.Point(self.GetPosition().x, 0), style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
        #self.props.Show()
    
    def SaveState(self, id):
        sc.SizedFrame.SaveState(self, id)
        config = wx.Config()
        if config:
            config.SetPath(id)
            libName = self.indexList.GetStringSelection()
            if libName != "":
                config.Write("LastLibrary", libName)
    
    def LoadState(self, id):
        sc.SizedFrame.LoadState(self, id)
        config = wx.Config()
        if config:
            config.SetPath(id)
            libName = config.Read("LastLibrary")
            if libName != "":
                self.indexList.SetStringSelection(libName)
                self.loadLibraryFiles(libName)
    
    def menuEventHandler(self, event):
        id = event.GetId()
        libName = self.indexList.GetStringSelection()
        
        if id == wx.ID_NEW:
            self.createNewLibrary()
        
        if id == constants.ID_DEL_LIBRARY:
            self.removeIndex(libName)
        
        if id == constants.ID_REINDEX:
            if not libName == "":
                self.reindexLibrary(libName)
        
        if id == constants.ID_LIB_SETTINGS:
            if not libName == "":
                self.showSettingsDialog(libName)
                
        if id == constants.ID_ADD_FILES:
            if not libName == "":
                self.addFiles(libName)
    
    def createNewLibrary(self):
        dialog = New.NewLibraryDialog(self, -1, _("New Library"),
                    style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetName()
            contentDir = dialog.GetContentsDir()
            self.indexManager.addIndex(name, contentDir)
            self.indexList.Append(name)
            
    def addFiles(self, libName):
        dialog = wx.FileDialog(self, _("Choose files to add"), 
                                style=wx.FD_MULTIPLE|wx.FD_FILE_MUST_EXIST|wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            dirname = dialog.GetDirectory()
            contentdir = self.indexManager.getIndexProp(libName, index_manager.CONTENT_DIR)
            if not dirname.find(contentdir):
                result = wx.MessageBox(_("The files you selected are located outside of your contents folder. If you want to add these files, they must be copied to your contents folder. Would you like to do this now?"),
                            _("Copy files to contents dir?"), wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                if result == wx.ID_YES:
                    try:
                        for afile in dialog.GetFilenames():
                            destfile = os.path.join(contentdir, afile)
                            copy = True
                            # TODO: make an "apply to all" dialog here
                            if os.path.exists(destfile):
                                result = wx.MessageBox(_("The file %(filename)s already exists. Do you want to overwrite it?") % destfile,
                                    _("Overwrite file?"), wx.YES_NO | wx.ICON_WARNING)
                                if result != wx.ID_YES:
                                    copy = False
                                    
                            if copy:
                                shutil.copyfile(os.path.join(dirname, afile), destfile)
                                
                        dirname = contentdir
                    except:
                        globals.errorLog.write("MainFrame.addFiles: Unable to copy files")
                        wx.MessageBox(_("Unable to copy files."), _("Unable to copy files"))
                
                index = self.indexManager.getIndex(libName)
                for afile in dialog.GetFilenames():
                    self.GetStatusBar().SetStatusText(_("Adding %(filename)s to index.") % afile)
                    index.addFile(afile)
        
        dialog.Destroy()
    
    def removeIndex(self, libName):
        result = wx.MessageBox(_("This will delete this library from your collection, along with its index files. Are you sure you want to do this? (Your imported files and folders will not be deleted.)"),
                            _("Confirm Library Delete"), wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        if result == wx.ID_YES:
            self.indexManager.removeIndex(libName, deleteIndexFiles=True)
            self.indexManager.saveChanges()
            index = self.indexList.FindString(libName)
            if index > -1:
                self.indexList.Delete(index)
                self.indexList.SetSelection(0)
                self.loadLibraryFiles(self.indexList.GetStringSelection())
    
    def showSettingsDialog(self, libName):
        indexDir = self.indexManager.getIndexProp(libName, index_manager.INDEX_DIR)
        contentsDir = self.indexManager.getIndexProp(libName, index_manager.CONTENT_DIR)
        dialog = Settings.LibSettingsDialog(self, -1,
                    _("%(libname)s Library Settings") % {"libname": libName},
                    style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_MODAL | wx.RESIZE_BORDER,
                    indexDir=indexDir, contentsDir=contentsDir)
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            self.indexManager.setIndexProp(libName, index_manager.INDEX_DIR, dialog.GetIndexDir())
            self.indexManager.setIndexProp(libName, index_manager.CONTENT_DIR, dialog.GetContentsDir())
            self.indexManager.saveChanges()
        dialog.Destroy()
    
    def reindexLibrary(self, libName):
        
        class MainFrameIndexingCallback(index.IndexingCallback):
            def __init__(self, thisindex, parent):
                index.IndexingCallback.__init__(self, thisindex)
                self.parent = parent
            
            def indexingStarted(self, numFiles):
                self.numFiles = numFiles
                self.parent.GetStatusBar().SetStatusText(_("Started indexing..."))
            
            def fileIndexingStarted(self, filename):
                self.numFiles = self.numFiles - 1
                self.parent.GetStatusBar().SetStatusText(_("Indexing %(filename)s...") % {"filename": filename})
            
            def indexingComplete(self):
                self.parent.GetStatusBar().SetStatusText(_("Indexing complete."))
        
        thisindex = self.indexManager.getIndex(libName)
        callback = MainFrameIndexingCallback(thisindex, self)
        
        thisindex.reindexLibrary(callback)
    
    def OnIndexSelected(self, evt):
        self.loadLibraryFiles(evt.GetString())
    
    def OnSearchText(self, evt):
        self.queryLibrary(evt.GetString())
    
    def OnClose(self, evt):
        self.SaveState("LibraryMainFrame")
        evt.Skip()
    
    def queryLibrary(self, query):
        libName = self.indexList.GetStringSelection()
        if query.strip() == "":
            self.loadLibraryFiles(libName)
            return
        
        query = query
        index = self.indexManager.getIndex(libName)
        hits = index.search("url", query)
        self.contentsList.DeleteAllItems()
        for hit in hits:
            listIndex = self.contentsList.InsertStringItem(sys.maxint, hit["url"][0])
    
    def loadLibraryFiles(self, libName):
        self.contentsList.DeleteAllItems()
        index = self.indexManager.getIndex(libName)
        files = index.getFilesInIndex()
        for afile in files:
            listIndex = self.contentsList.InsertStringItem(sys.maxint, afile)
            #self.contentsList.SetStringItem(listIndex, 1, files[afile])
    
    def createMenu(self):
        global menuItems
        
        menubar = wx.MenuBar()
        
        for menu in menuItems:
            newMenu = wx.Menu()
            
            for item in menuItems[menu]:
                itemType = wx.ITEM_NORMAL
                if len(item) == 4:
                    itemType = item[3]
                
                if item[1] != "-":
                    newMenu.Append(item[0], item[1], item[2], itemType)
                else:
                    newMenu.AppendSeparator()
                
                self.Bind(wx.EVT_MENU, self.menuEventHandler, id=item[0])
            
            menubar.Append(newMenu, menu)
        
        self.SetMenuBar(menubar)
        