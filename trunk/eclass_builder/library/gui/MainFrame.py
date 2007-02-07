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
import settings
import LibSettings
import Props
import Metadata
import errors
import PyLucene

# because a dict randomly re-orders the keys so menus are not sequential
menus = [
        _("&File"),
        _("&Edit"),
        _("&Library"),
        _("&Window"),
        _("&Help"),
        ]
        
menuItems = {
        _("&File"):
        [
            (wx.ID_NEW, _("&New Library"), _("Create a new library")),
            (constants.ID_DEL_LIBRARY, _("&Delete Library"), _("Deletes a library from your collection.")),
        ],
        _("&Edit"):
        [
            (wx.ID_CUT, _("Cut\tCTRL+X"), _("Cut items")),
            (wx.ID_COPY, _("Copy\tCTRL+C"), _("Copy items")),
            (wx.ID_PASTE, _("Paste\tCTRL+V"), _("Paste Items")),
            (-1, "-", "-"),
            (wx.ID_SELECTALL, _("Select All\tCTRL+A"), _("Select all items")),
        ],
        _("&Library"):
        [
            (constants.ID_ADD_FILES, _("Add File(s)"), 
                        _("Add file(s) to current library.")),
            (constants.ID_ADD_FOLDERS, _("Add Folder(s)"), 
                        _("Add folder(s) to current library.")),
            (constants.ID_INDEX, _("&Index\tCTRL+R"),
                        _("Index files in contents folder.")),
            (constants.ID_UPDATE_INDEX, _("&Update Index\tCTRL+U"),
                        _("Update index for files in current library.")),
            (-1, "-", "-"),
            (constants.ID_LIB_SETTINGS, _("&Settings"),
                        _("View and set options for current library."))
        ],
        _("&Window"):
        [
            (constants.ID_PROPS, _("Property Editor"), _("Edit item properties")),
            (constants.ID_METADATA_EDITOR, _("Field Editor"), _("Edit fields in property list.")),
            (constants.ID_ERROR_LOG, _("Error Log"), _("View any program errors")),
        ],
        _("&Help"):
        [],

}

errorLog = None

class FrameStatusBarIndexingCallback(index.IndexingCallback):
    def __init__(self, index, parent=None):
        self.index = index
        self.parent = parent
        
        self.numFiles = 0
        
    def indexingStarted(self, numFiles):
        wx.CallAfter(self.parent.updateLibraryStatus, self.index, enabled=False)
    
        self.numFiles = numFiles
        message = _("Indexing files in %s") % (self.index)
        if self.parent:
            wx.CallAfter(self.parent.GetStatusBar().SetStatusText, message)
        print message
        
    def fileIndexingStarted(self, filename):
        message = _("%(index)s: Indexing %(file)s") % {"index":self.index, "file":filename}
        if self.parent:
            wx.CallAfter(self.parent.GetStatusBar().SetStatusText, message)
        print message
        
    def indexingComplete(self):
        message = _("Finished indexing %s") % (self.index)
        if self.parent:
            wx.CallAfter(self.parent.GetStatusBar().SetStatusText, message)
        print message
        
        wx.CallAfter(self.parent.updateLibraryStatus, self.index, enabled=True)
            

class ContentsList(autolist.AutoSizeListCtrl):
    def __init__(self, *args, **kwargs):
        autolist.AutoSizeListCtrl.__init__(self, *args, **kwargs)
        self.files = []
        
    def OnGetItemText(self, itemNum, col):
        if len(self.files) >= itemNum:
            return self.files[itemNum]
        

class MainFrame(sc.SizedFrame):
    def __init__(self, *args, **kwargs):
        sc.SizedFrame.__init__(self, *args, **kwargs)
        self.indexManager = index_manager.IndexManager(os.path.join(settings.PrefDir, "indexes.cfg"))
        self.files = []
        self.busyLibraries = []
        self.createMenu()
        self.sortAscending = False
        
        self.threads = []
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
        
        self.listPane = sc.SizedPanel(self.splitter, -1)
        self.statusPane = sc.SizedPanel(self.listPane, -1)
        self.statusText = wx.StaticText(self.statusPane, -1)
        self.statusPane.Hide()
        self.contentsList = ContentsList(self.listPane, -1, style = wx.LC_REPORT | wx.LC_VIRTUAL )
        self.contentsList.SetSizerProps(expand=True, proportion=1)
        self.contentsList.InsertColumn(0, _("Filename"))
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.contentsList)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.contentsList)
        
        self.splitter.SplitVertically(self.indexPane, self.listPane, 150)
        
        self.CreateStatusBar()
        
        globals.errorLog = errors.AppErrorLog()
        
        self.propsFrame = Props.PropsMiniFrame(self, -1, _("Properties"), style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX)
        self.propsFrame.LoadState("LibraryPropsFrame")
        #self.propsFrame.Show()
        
        self.metadataFrame = Metadata.MetadataMiniFrame(self, -1, _("Field Editor"), style=wx.CAPTION | wx.RESIZE_BORDER | wx.CLOSE_BOX)
        self.metadataFrame.LoadState("LibraryMetadataFrame")
        #self.metadataFrame.Show()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.LoadState("LibraryMainFrame")
        
    def OnColClick(self, event):
        self.sortAscending = not self.sortAscending
        self.contentsList.SortItems(self.itemSorter)

    def itemSorter(self, key1, key2):
        cmpVal = cmp(key1,key2)
        print "cmpVal = %d" % cmpVal
        if cmpVal == 0:
            cmpVal = 1
            
        if not self.sortAscending:
            cmpVal = -cmpVal
        
        return cmpVal
    
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
            if libName != "" and libName in self.indexManager.getIndexes():
                self.indexList.SetStringSelection(libName)
                self.loadLibraryFiles(libName)
    
    def menuEventHandler(self, event):
        id = event.GetId()
        
        if id == wx.ID_NEW:
            self.createNewLibrary()
        
        elif id == constants.ID_DEL_LIBRARY:
            self.removeIndex(libName)
        
        elif id == constants.ID_INDEX:
            if not libName == "":
                self.indexLibrary(libName)
                
        elif id == constants.ID_UPDATE_INDEX:
            if not libName == "":
                self.updateLibrary(libName)
        
        elif id == constants.ID_LIB_SETTINGS:
            if not libName == "":
                self.showSettingsDialog(libName)
                
        elif id == constants.ID_ADD_FILES:
            if not libName == "":
                self.addFiles(libName)
                
        elif id == constants.ID_PROPS:
            self.propsFrame.Show()
            
        elif id == constants.ID_METADATA_EDITOR:
            self.metadataFrame.Show()
                
        else:
            event.Skip()
    
    def createNewLibrary(self):
        dialog = New.NewLibraryDialog(self, -1, _("New Library"),
                    style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetName()
            contentDir = dialog.GetContentsDir()
            self.indexManager.addIndex(name, contentDir)
            newItem = self.indexList.Append(name)
            self.indexList.SetSelection(newItem)
            self.selectLibrary(name)
            
    def updateLibraryStatus(self, index, enabled=True):
        if enabled:
            if index in self.busyLibraries:
                self.busyLibraries.remove(index)
            if self.indexList.GetStringSelection() == index:
                self.contentsList.Enable()
                self.loadLibraryFiles(index)
                
        else:
            if index not in self.busyLibraries:
                self.busyLibraries.append(index)
            if self.indexList.GetStringSelection() == index:
                self.contentsList.Enable(False)
                self.statusPane.SetBackgroundColour(wx.RED)
                self.statusText.SetLabel(_("Library %(library)s is currently being indexed..."))                

    def refreshMetadataPropsForSelectedFiles(self):
        indexName = self.indexList.GetStringSelection()
        metadata = {}
        if indexName != "":
            thisindex = self.indexManager.getIndex(indexName)
            selItem = self.contentsList.GetFirstSelected()
            counter = 0
            while selItem != -1:
                filename = self.contentsList.GetItemText(selItem)
                props = self.getFileProps(filename)

                for prop in props:
                    if counter == 0 and not metadata.has_key(prop):
                        metadata[prop] = props[prop]
                    elif counter > 0:
                        if metadata.has_key(prop) and not props[prop] == metadata[prop]:
                            del metadata[prop]
                counter += 1
        
                selItem = self.contentsList.GetNextItem(selItem, wx.LIST_NEXT_BELOW, wx.LIST_STATE_SELECTED)
            
            fields = self.getIndexInfo()["MetadataFields"]
            self.propsFrame.props.loadProps(metadata, fields)


    def updateMetadataForSelectedFiles(self, field, value):
        indexName = self.indexList.GetStringSelection()
        if indexName != "":
            thisindex = self.indexManager.getIndex(indexName)
            selItem = self.contentsList.GetFirstSelected()
            while selItem != -1:
                filename = self.contentsList.GetItemText(selItem)
                thisindex.updateFileMetadata(filename, {field:value})
                selItem = self.contentsList.GetNextItem(selItem, wx.LIST_NEXT_BELOW, wx.LIST_STATE_SELECTED)

    def addFiles(self, libName):
        dialog = wx.FileDialog(self, _("Choose files to add"), 
                                style=wx.FD_MULTIPLE|wx.FD_FILE_MUST_EXIST|wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            dirname = dialog.GetDirectory()
            contentdir = self.indexManager.getIndexProp(libName, index_manager.CONTENT_DIR)
            if dirname.find(contentdir) != -1:
                result = wx.MessageBox(_("The files you selected are located outside of your contents folder. If you want to add these files, they must be copied to your contents folder. Would you like to do this now?"),
                            _("Copy files to contents dir?"), wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                if not result == wx.YES:
                    return
                    
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
        if result == wx.YES:
            self.indexManager.removeIndex(libName, deleteIndexFiles=True)
            self.indexManager.saveChanges()
            index = self.indexList.FindString(libName)
            if index > -1:
                self.indexList.Delete(index)
                if self.indexList.GetCount() > 0:
                    self.indexList.SetSelection(0)
                    self.loadLibraryFiles(self.indexList.GetStringSelection())
                else:
                    self.contentsList.DeleteAllItems()
                    
    
    def showSettingsDialog(self, libName):
        indexDir = self.indexManager.getIndexProp(libName, index_manager.INDEX_DIR)
        contentsDir = self.indexManager.getIndexProp(libName, index_manager.CONTENT_DIR)
        dialog = LibSettings.LibSettingsDialog(self, -1,
                    _("%(libname)s Library Settings") % {"libname": libName},
                    style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_MODAL | wx.RESIZE_BORDER,
                    indexDir=indexDir, contentsDir=contentsDir)
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            self.indexManager.setIndexProp(libName, index_manager.INDEX_DIR, dialog.GetIndexDir())
            self.indexManager.setIndexProp(libName, index_manager.CONTENT_DIR, dialog.GetContentsDir())
            self.indexManager.saveChanges()
        dialog.Destroy()
    
    def indexLibrary(self, libName):
        thisindex = self.indexManager.getIndex(libName)
        #self.indexManager.removeIndex(libName, deleteIndexFiles=True)
        #callback = index.IndexingCallback(libName) #FrameStatusBarIndexingCallback(thisindex, self)

        class IndexThread(PyLucene.PythonThread):
            def __init__(self, index, libName, frame):
                PyLucene.PythonThread.__init__(self)
                self.index = index
                self.libName = libName
                self.frame = frame
                self.callback = None
                
            def run(self):
                self.callback = FrameStatusBarIndexingCallback(self.libName, self.frame)
                self.index.indexLibrary(self.callback)
                
        self.indexthread = IndexThread(thisindex, libName, self)
        self.indexthread.start()
        
    def updateLibrary(self, libName):
        thisindex = self.indexManager.getIndex(libName)
        #callback = index.IndexingCallback(libName) #FrameStatusBarIndexingCallback(thisindex, self)

        class IndexThread(PyLucene.PythonThread):
            def __init__(self, index, libName, frame):
                PyLucene.PythonThread.__init__(self)
                self.index = index
                self.libName = libName
                self.frame = frame
                self.callback = None
                
            def run(self):
                self.callback = FrameStatusBarIndexingCallback(self.libName, self.frame)
                self.index.updateLibrary(self.callback)
                
        self.indexthread = IndexThread(thisindex, libName, self)
        self.indexthread.start()
        
    def selectLibrary(self, libName):
        if libName not in self.busyLibraries:
            self.statusPane.Hide()
            self.contentsList.Enable(True)
            self.loadLibraryFiles(libName)
        else:
            self.contentsList.Enable(False)
            self.statusText.SetLabel(_("Library %(library)s is currently being indexed...") % libname) 
            self.statusPane.Show()   
    
    def OnIndexSelected(self, evt):
        self.selectLibrary(evt.GetString())
            
    def OnItemSelected(self, evt):
        self.refreshMetadataPropsForSelectedFiles()     
    
    def OnSearchText(self, evt):
        self.queryLibrary(evt.GetString())
    
    def OnClose(self, evt):
        self.propsFrame.SaveState("LibraryPropsFrame")
        self.metadataFrame.SaveState("LibraryMetadataFrame")
        self.SaveState("LibraryMainFrame")
        evt.Skip()
        
    def getIndexInfo(self):
        libName = self.indexList.GetStringSelection()
        index = self.indexManager.getIndex(libName)
        if index:
            return index.getIndexInfo()

    def getFileProps(self, filename):
        libName = self.indexList.GetStringSelection()
        index = self.indexManager.getIndex(libName)
        if index:
            return index.getFileInfo(filename)[1]
    
    def queryLibrary(self, query):
        libName = self.indexList.GetStringSelection()
        if query.strip() == "":
            self.loadLibraryFiles(libName)
            return
        
        query = query
        index = self.indexManager.getIndex(libName)
        files = index.getFilesInIndex()
        #hits = index.search("url", query)
        self.contentsList.DeleteAllItems()
        self.contentsList.files = []
        self.contentsList.SetScrollPos(wx.VERTICAL, 0)
        
        for afile in files:
            if afile.find(query) != -1:
                self.contentsList.files.append(afile)
        
        self.contentsList.files.sort()
        numFiles = len(self.contentsList.files)
        self.contentsList.SetItemCount(numFiles)
        self.SetStatusText(_("%(results)d results for query '%(query)s'" % {"results":numFiles, "query":query}))
    
    def loadLibraryFiles(self, libName):
        self.contentsList.DeleteAllItems()
        self.contentsList.files = []
        self.contentsList.SetScrollPos(wx.VERTICAL, 0)
        index = self.indexManager.getIndex(libName)
        try:
            files = index.getFilesInIndex()
            self.contentsList.Freeze()
            for afile in files:
                self.contentsList.files.append(afile)
                #listIndex = self.contentsList.InsertStringItem(sys.maxint, afile)
                #self.contentsList.SetItemData(listIndex, afile)
                #self.contentsList.SetStringItem(listIndex, 1, files[afile])
            self.contentsList.files.sort()
            numFiles = len(self.contentsList.files)
            self.contentsList.SetItemCount(numFiles)
            self.SetStatusText(_("%(numberFiles)d files in library." % {"numberFiles":numFiles}))
            self.contentsList.Thaw()
            
            
            #self.contentsList.SortItems(self.itemSorter)
        except PyLucene.JavaError:
            self.fixCorruptIndex(libName)
        
    def fixCorruptIndex(self, libName):
        message = _("The \"%(library)s\" library index appears to be corrupted and cannot be opened. Would you like to try re-creating the index?") % {"library": libName}
        result = wx.MessageBox(message, _("Fix corrupted index?"), wx.YES_NO | wx.ICON_ERROR)
        
        if result == wx.YES:
            index_dir = self.indexManager.getIndexProp(libName, index_manager.INDEX_DIR)
            shutil.rmtree(index_dir)
            if not os.path.exists(index_dir):
                os.makedirs(index_dir)
            self.indexLibrary(libName)
    
    def createMenu(self):
        global menuItems
        
        menubar = wx.MenuBar()
        
        for menu in menus:
            #if menu == _("&Window") and wx.Platform == "__WXMAC__":
            #    break 
            
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
        