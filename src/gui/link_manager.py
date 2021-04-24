from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import os, sys, re
import wx
import wx.lib.sized_controls as sc
import persistence
from . import autolist
import utils
import guiutils
import settings

class LinkChecker(sc.SizedDialog):
    def __init__(self, parent):
        sc.SizedDialog.__init__ (self, parent, -1, _("Link Checker"), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.parent = parent
        
        pane = self.GetContentsPane()
        self.linkList = autolist.AutoSizeListCtrl(pane, -1, size=(600,200), style=wx.LC_REPORT)
        self.linkList.InsertColumn(0, _("Link"), width=300)
        self.linkList.InsertColumn(1, _("Status"))
        self.linkList.SetSizerProps({"expand": True, "proportion":1})
        
        btnPane = sc.SizedPanel(pane, -1)
        btnPane.SetSizerProps({"expand": True, "halign":"right"})

        self.links = []
        self.itemCount = 0
        self.currentFile = ""

        self.Fit()
        self.SetMinSize(self.GetSize())

    def CheckLinks(self, myhtml):
        imagelinks = re.compile("src\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
        imagelinks.sub(self.CheckLink,myhtml)
        weblinks = re.compile("href\\s*=\\s*\"([^\"]*)\"", re.IGNORECASE|re.DOTALL)
        weblinks.sub(self.CheckLink, myhtml)

    def CheckLink(self, match):
        link = match.group(1)
        if link.lower().find("http://") == 0 or link.lower().find("ftp://") == 0:
            if link in self.links:
                return
            else:
                self.links.append(link)
            #add the link to the list and check the status
            if self.linkList:
                self.linkList.InsertStringItem(self.itemCount, link)
                self.linkList.SetStringItem(self.itemCount, 1, _("Connecting..."))
                import threading
                self.mythread = threading.Thread(None, self.ConnectToLink, args=(self.itemCount, link))
                self.mythread.start()
                self.itemCount = self.itemCount + 1

    def ConnectToLink(self, item, link):
            import urllib.request, urllib.error, urllib.parse
            try:
                request = urllib.request.Request(link)
                opener = urllib.request.build_opener()
                # some providers, such as Wikipedia, will block requests
                # when a user agent isn't specified, or if it's a defualt
                # user agent for automated bots. So we need to specify our
                # own user agent to keep from being blocked.
                request.add_header('User-Agent','EClass Link Checker/1.0 +http://www.eclass.net/') 
                opener.open(request)
                wx.CallAfter(self.linkList.SetStringItem, item, 1, _("OK"))
            except urllib.error.URLError as e:
                print("link is: " + link)
                if hasattr(e, 'reason'):
                    print('We failed to reach a server.')
                    print('Reason: ', e.reason)
                elif hasattr(e, 'code'):
                    print('The server couldn\'t fulfill the request.')
                    print('Error code: ', e.code)
                wx.CallAfter(self.linkList.SetStringItem, item, 1, _("Broken"))
