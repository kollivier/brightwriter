import wx
import errors

class GUIErrorCallbacks:
    def displayError(self, message, title=_("EClass.Builder Error")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_ERROR)
        if errors.appErrorLog:
            errors.appErrorLog.write(message)
            
    def displayWarning(self, message, title=_("EClass.Builder Warning")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_EXCLAMATION)
        if errors.appErrorLog:
            errors.appErrorLog.write(message)
            
    def displayInformation(self, message, title=_("EClass.Builder Message")):
        wx.MessageBox(message, style=wx.OK|wx.ICON_INFORMATION)
        if errors.appErrorLog:
            errors.appErrorLog.write(message)            

errorPrompts = GUIErrorCallbacks()