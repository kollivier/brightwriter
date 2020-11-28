from builtins import range
import wx
import wx.lib.sized_controls as sc
import string, sys, os
    
class ConvertMediaDialog(sc.SizedDialog):
    def __init__(self, parent, files=[]):
        self.files = files
        
        sc.SizedDialog.__init__(self, parent, -1, _("Convert Media Files?"), 
                            wx.DefaultPosition, wx.DefaultSize,
                            wx.DEFAULT_DIALOG_STYLE)
        
        # we do things this way so that the dialog automatically is able to
        # calculate the correct amount of padding around the dialog.
        # This helps make the dialog HIG compliant.
        dlgPanel = self.GetContentsPane()
        
        label = wx.StaticText(dlgPanel, -1, _("Converting the following files to streaming format will provide improved performance\n over the Internet. Please select which files (if any) you'd like to convert."))
        self.fileList = wx.CheckListBox(dlgPanel, -1, choices=files)
        self.fileList.SetSizerProp("expand", "true")
        
        # you could also put the buttons in their own pane and add it to the contents pane, 
        # but I added this method so that we can take advantage of CreateStdDialogButtonSizer.
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL))
        
        # This is how you can change the sizer dynamically until we can hook into
        # wx.Window.SetSizer(). Note that the sizer properties are retained.
        
        # dlgPanel.SetNewSizer(wx.BoxSizer(wx.HORIZONTAL))
        
        self.Fit()

    def GetSelectedFiles(self):
        files = []
        for item in range(0, self.fileList.GetCount()):
            if self.fileList.IsChecked(item):
                files.append(self.fileList.GetString(item))
                
        return files