import sys, string, os
import utils
import guiutils
import time

import wx
import persistence
import wx.lib.sized_controls as sc
import settings
import autolist

import index

class ProjectFindDialog(sc.SizedDialog):
    def __init__(self, parent=None):
        sc.SizedDialog.__init__(self, parent, -1, _("Find In Project"), wx.DefaultPosition, wx.Size(420, 340), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pane = self.GetContentsPane()
        self.itemCount = 0
        
        self.searchBox = wx.SearchCtrl(pane, -1, style=wx.TE_PROCESS_ENTER)
        self.searchBox.SetSizerProp("expand", "true") #, proportion=0)
        self.searchBox.SetFocus()
        
        #wx.StaticText(searchpane, -1, _("in") + " ")
        #self.searchContext = wx.Choice(searchpane, -1, choices=["contents"])
        #self.searchContext.SetSelection(0)
        
        #self.searchBtn = wx.Button(searchpane, -1, _("Search"))
        #self.searchBtn.SetDefault()
        
        # list containing search results
        self.listCtrl = autolist.AutoSizeListCtrl(pane, -1, style=wx.LC_REPORT)
        self.listCtrl.SetSizerProp("expand", "true")
        self.listCtrl.SetSizerProp("proportion", 2)
        
        self.itemCount = 0
        self.selItem = None
        self.listCtrl.InsertColumn(0, _("Page"))
        self.listCtrl.InsertColumn(1, _("Filename"))
        self.listCtrl.SetColumnWidth(0, 100)
        self.listCtrl.SetColumnWidth(1, 280)

        #EVT_LEFT_DCLICK(self, self.listCtrl.GetId(), self.OnDblClick)
        wx.EVT_LIST_ITEM_SELECTED(self, self.listCtrl.GetId(), self.OnSelection)
        wx.EVT_TEXT(self.searchBox, self.searchBox.GetId(), self.OnSearch)

        #wx.EVT_ACTIVATE(self, self.OnActivate)
        
    def MakeSearchMenu(self):
        menuItems = ["contents"]
        

    def OnSearch(self, evt):
        searcher = index.Index(os.path.join(settings.ProjectDir, "index.lucene"), settings.ProjectDir)
        results = searcher.search("contents", self.searchBox.GetValue())
        self.itemCount = 0
        
        self.listCtrl.DeleteAllItems()
        for result in results:
            self.listCtrl.InsertStringItem(self.itemCount, result['title'])
            self.listCtrl.SetStringItem(self.itemCount, 1, result['url'][0])
            self.itemCount += 1
            
        
            

    def OnSelection(self, evt):
        pass
        
