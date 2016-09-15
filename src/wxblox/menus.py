#----------------------------------------------------------------------
# Name:        wxblox/menus.py
# Purpose:     A simple mixin to allow apps to store their menubars as a series of
#              tuples, and then use the CreateMenuBar() function to realize it as 
#              a wx.MenuBar.
#
# Author:      Kevin Ollivier
#
# Created:     10-Mar-2007
# Copyright:   (c) 2007 Kevin Ollivier
# Licence:     wxWindows license
#----------------------------------------------------------------------

import wx

# TODO: Find a better place for these...        
SAVEALL_ID = wx.NewId()
VIEW_TOOLBAR_ID = wx.NewId()
VIEW_STATUSBAR_ID = wx.NewId()

class Menu:
    def __init__(self, name, items=[]):
        self.name = name
        # we don't use a dict because a dict's keys are sorted by their hash values
        # which is often not the same as the actual order the items were defined in.
        self.items = items
        
class MenuItem:
    def __init__(self, name, id=wx.NewId(), description="", hotkey="", type=wx.ITEM_NORMAL,
                    image=None, handlerFunc=None):
        self.id = id
        self.name = name
        self.description = description
        self.hotkey = hotkey
        self.type = type
        self.image = image
        self.handlerFunc=handlerFunc

class MenuManager:
    def CreateMenuBar(self):
        global menus
        global menuItems
        
        menubar = wx.MenuBar()
        
        for menu in self.menus:
            newMenu = wx.Menu()
            
            for item in self.menuItems[menu]:
                itemType = wx.ITEM_NORMAL
                if len(item) == 4:
                    itemType = item[3]
                
                if item[0] != "-":
                    newMenu.Append(item[1], item[0], item[2], itemType)
                else:
                    newMenu.AppendSeparator()
                
                self.Bind(wx.EVT_MENU, self.HandleEvent, id=item[0])
            
            menubar.Append(newMenu, menu)
        
        return menubar