import wx

import logging
log = logging.getLogger('EClass')

class GUIErrorCallbacks:
    def displayError(self, message, title=_("BrightWriter Error")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_ERROR)
        if log:
            log.error(message)
            
    def displayWarning(self, message, title=_("BrightWriter Warning")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_EXCLAMATION)
        if log:
            log.warn(message)
            
    def displayInformation(self, message, title=_("BrightWriter Message")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_INFORMATION)
        if log:
            log.info(message)            

errorPrompts = GUIErrorCallbacks()
