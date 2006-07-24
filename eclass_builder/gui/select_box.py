# NOTE: To be replaced by wxFilePicker once it's ready.
import os
import wx
import wx.lib.newevent as newevent
import wxaddons.sized_controls as sc
import settings

# common file filters for supported multimedia formats
image_exts = ["jpg", "jpeg", "gif", "bmp", "png"]
video_exts = ["avi", "mov" , "mpg", "asf", "wmv", "rm", "ram", "swf"]
audio_exts = ["wav", "aif", "mp3", "asf", "wma", "rm" , "ram"]
doc_exts   = ["htm", "html", "doc", "rtf"]
pres_exts  = ["ppt", "htm", "html", "swf", "pdf"]


filters =   {
            "Graphics"  : ( _("Image Files"), image_exts ),
            "Video"     : ( _("Video Files"), video_exts ),
            "Audio"     : ( _("Audio Files"), audio_exts ),
            "Text"      : ( _("Document Files"), doc_exts ),
            "Present"   : ( _("Presentation Files"), pres_exts ),
            "File"      : ( _("All Files"), ["*"] ),
            }
            
(FileSelectedEvent, EVT_FILE_SELECTED) = newevent.NewEvent()

class SelectBox(sc.SizedPanel):
    """
    Class: eclass.SelectBox
    Last Updated: 9/24/02
    Description: A customized text box class to integrate file selection capabilities.

    Attributes:
    - parent: the parent window hosting the control
    - filename: points to the file selected by the user
    - type: file types the user is allowed to select (i.e. "Graphics", "Audio")
    - title: label text
    - label: textbox label
    - textbox: the textbox to store the file selected by the user
    - selectbtn: button the user clicks to select a file

    Methods:
    - selectbtnClicked: brings up the file selection dialog when the user clicks the selectbtn
    - textboxChanged: updates the textbox attribute whenever the textbox changes
    """

    def __init__(self, parent, filename, type="File", startdir="", exts=[]):
        self.parent = parent
        self.type = type
        self.exts = exts
        self.selecteddir = ""
        self.startdir = startdir
        global filters
        if self.startdir == "":
            self.startdir = settings.ProjectDir
            if self.type in filters:
                self.startdir = os.path.join(self.startdir, self.type)
    
        sc.SizedPanel.__init__(self, parent, -1)
        self.SetSizerType("horizontal")
        self.SetSizerProp("expand", True)
        self.SetSizerProp("proportion", 1)
        self.SetSizerProp("border", (["all"], 0))
        
        icnFolder = wx.Bitmap(os.path.join(settings.AppDir, "icons", "Open.gif"), wx.BITMAP_TYPE_GIF)
        self.textbox = wx.TextCtrl(self, -1, filename)
        self.textbox.SetSizerProp("expand", True)
        self.textbox.SetSizerProp("proportion", 1)
        self.selectbtn = wx.BitmapButton(self, -1, icnFolder)

        wx.EVT_BUTTON(self.selectbtn, self.selectbtn.GetId(), self.selectbtnClicked)
        
    def createFilter(self):
        global filters
        
        if self.type in filters: 
            filter = filters[self.type][0]
            exts = filters[self.type][1]
        else:
            filter = self.type
            exts = self.exts
            
        extlist = ""
        for ext in exts:
            extlist += "*." + ext + ","
        extlist = extlist[:-1] # remove the trailing comma
        filter = filter + " (" + extlist + ")|" + extlist.replace(",", ";")
        return filter
        
    def SetValue(self, text):
        self.textbox.SetValue(text)
        
    def GetValue(self):
        return self.textbox.GetValue()
        
    def selectbtnClicked(self, event):
        f = None
        if self.type == "Directory":
            f = wx.DirDialog(self.parent, _("Select a directory"), self.directory)
        else:
            f = wx.FileDialog(self.parent, _("Select a file"), self.startdir, "", self.createFilter(), wx.OPEN)
        if f and f.ShowModal() == wx.ID_OK:
            self.textbox.SetValue(f.GetPath())
            evt = FileSelectedEvent(sender = self, filename = f.GetPath())
            wx.PostEvent(self, evt)
        f.Destroy()