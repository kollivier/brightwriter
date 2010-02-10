import wx

import logging
log = logging.getLogger('EClass')

class GUIErrorCallbacks:
    def displayError(self, message, title=_("EClass.Builder Error")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_ERROR)
        if log:
            log.error(message)
            
    def displayWarning(self, message, title=_("EClass.Builder Warning")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_EXCLAMATION)
        if log:
            log.warning(message)
            
    def displayInformation(self, message, title=_("EClass.Builder Message")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_INFORMATION)
        if log:
            log.info(message)            

errorPrompts = GUIErrorCallbacks()
