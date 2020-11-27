from __future__ import absolute_import
import wx
import wx.lib.pydocview
from . import menus
from . import events

class UtilityManagerMixin:
    """
    IDEs often have a mixture of views, which represent documents, and what I call
    'utilities', which are helper views that might visualize a document in another way,
    provide services and logging, etc. The key is that these utilities may react to
    an open document, but are not document-specific, thus they don't appear and disappear
    along with the document itself.
    """
    
    def __init__(self):
        self.utilityViews = {}
    
    def AddUtilityView(self, view, direction):
        if direction not in self.utilityViews:
            self.utilityViews[direction] = []
            
        if not window in self.utilityViews[direction]:
            self.utilityViews[direction].append(view)
           
    def RemoveUtilityView(self, view):
        for direction in self.utilityViews:
            for utility in self.utilityViews[direction]:
                if utility == view:
                    self.utilityViews[direction].remove(utility) 

    # subclasses implement these interfaces 
    def LoadUtilityViews(self):
        pass
        
    def SaveUtilityViews(self):
        pass

class AppFrameManagerMixin:
    """
    This class allows the application to switch UIs between MDI/AUI/MFI as desired by
    the app developer or user. 
    """
    
    def __init__(self, redirect):
        # ALERT!! pydocview bugs that need fixing (accessing undefined vars)
        self._defaultIcon = None
        self._services = []
        self._useTabbedMDI = True
        self._registeredCloseEvent = False
        
        self.auiManager = None
        self.mdiParentFrame = None
        self.interfaceStyle = "Tabbed"
        if wx.Platform == "__WXMAC__":
            self.interfaceStyle = "MFI"
            
        config = wx.Config.Get()
        config.SetPath("AppFrameManagerProperties")
        style = config.Read("InterfaceStyle", "")
        if style != "":
            self.interfaceStyle = style
            
        self.RegisterEvents()
        
    def ProcessEvent(self, event):
        id = event.GetId()
        if id == wx.ID_NEW:
            self.CreateNewWindow()
        elif id == wx.ID_EXIT:
            self.ExitMainLoop()
            
        return True
            
    def ProcessUpdateUIEvent(self, event):
        if event.GetId() in [wx.ID_NEW, wx.ID_OPEN, wx.ID_EXIT]:
            event.Enable(True)
        else:
            event.Enable(False)
            
        return True