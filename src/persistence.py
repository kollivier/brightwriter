#----------------------------------------------------------------------
# Name:        persistence.py
# Purpose:     This module provides basic state saving/persistence functions,
#              allowing developers to save and load a window or frame's 
#              position, size, and visibility information.
#
# Author:      Kevin Ollivier
#
# Created:     2-June-2006
# Copyright:   (c) 2006 Kevin Ollivier
# Licence:     wxWindows license
#----------------------------------------------------------------------

import wx

def LoadState(self, id, dialogIsModal=True):
    config = wx.Config()
    if config:
        config.SetPath(id)
        size = (config.ReadInt("Width", -1), config.ReadInt("Height", -1))
        pos = (config.ReadInt("PosX", -1), config.ReadInt("PosY", -1))
        self.SetPosition(pos)
        self.SetSize(size)
        # don't handle visibility for modal dialogs, since they steal focus
        if not isinstance(self, wx.Dialog) or not dialogIsModal:
            self.Show(config.ReadInt("Visible", 0))
        
def SaveState(self, id):
    config = wx.Config()
    if config:
        size = self.GetSize()
        pos = self.GetPosition()
        
        config.SetPath(id)
        config.WriteInt("Width", size[0])
        config.WriteInt("Height", size[1])
        config.WriteInt("PosX", pos[0])
        config.WriteInt("PosY", pos[1])
        config.WriteInt("Visible", int(self.IsShown())) 
        
wx.Dialog.LoadState = LoadState
wx.Dialog.SaveState = SaveState

wx.Frame.LoadState = LoadState
wx.Frame.SaveState = SaveState