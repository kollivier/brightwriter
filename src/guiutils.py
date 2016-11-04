import sys, os, string
import settings
import utils
import fileutils
import htmlutils
import wx
import plugins

try:
    import win32api
except:
    pass


def getOpenCommandForFilename(filename):
    aFileType = wx.TheMimeTypesManager.GetFileTypeFromExtension(os.path.splitext(filename)[1])
    if aFileType:
        return aFileType.GetOpenCommand(filename)

    return ""


def importFile(filename):
    dir = os.path.dirname(filename)
    basename = os.path.basename(filename)
    
    if filename.find(settings.ProjectDir) != -1:
        return filename.replace(settings.ProjectDir + os.sep, "")
    
    copyfile = False
    destdir = os.path.join(settings.ProjectDir, "Content")
    # Don't do anything if the user selected the same file
    destfile = os.path.join(destdir, basename) 
    if destfile == filename:
        pass
    elif os.path.exists(destfile):
        # TODO: Check if files are identical before prompting to overwrite.
        msg = wx.MessageDialog(None, _("The file %(filename)s already exists. Do you want to overwrite this file?") % {"filename": destfile},
                                   _("Overwrite File?"), wx.YES_NO)
        answer = msg.ShowModal()
        msg.Destroy()
        if answer == wx.ID_YES:
            copyfile = True
    else:
        copyfile = True
        
    if copyfile:
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        fileutils.CopyFile(basename, dir, destdir)
        if os.path.splitext(basename)[1].find("htm") != -1:
            htmlutils.copyDependentFilesAndUpdateLinks(filename, os.path.join(destdir, basename))

    return os.path.join(destdir, basename)


def openInHTMLEditor(filename):
    htmleditor = settings.AppSettings["HTMLEditor"]
    if htmleditor == "":
        wx.MessageBox(_("To edit the page, EClass needs to know what HTML Editor you would like to use. To specify a HTML Editor, select 'Preferences' from the 'Options' menu."), _("Cannot Edit Page"), wx.OK)
    else:
        if not os.path.exists(filename):
            return 
            
        success = True
        try:
            if wx.Platform == "__WXMSW__":
                import win32api
                editor = "\"" + htmleditor + "\""
                if not string.find(string.lower(editor), "mozilla") == -1:
                    editor = editor + " -edit" 
                win32api.WinExec(editor + " \"" + filename + "\"")
                    
            else:
                editor = htmleditor 
                if wx.Platform == "__WXMAC__":
                    editor = "open -a '" + editor + "'"
                path = editor + " \"" + filename + "\""
                success = not os.system(path)
        except:
            success = False
            
        if not success:
            wx.MessageBox(_("The HTML Editor '%s' cannot be started. Make sure the program exists and can be accessed, or choose another HTML Editor.") % htmleditor, _("Cannot Start Editor"), wx.OK)

def sendCommandToApplication(filename, action="open", application=""):
    command = ""
    ranCommand = False
    if not os.path.exists(filename):
        return ranCommand
    
    aFileType = wx.TheMimeTypesManager.GetFileTypeFromExtension(os.path.splitext(filename)[1])
    if sys.platform == "win32":
        filename = win32api.GetShortPathName(filename)
    
    if aFileType and action == "open" and application == "":
        command = aFileType.GetOpenCommand(filename)

    if aFileType and action == "print" and application == "":
        command = aFileType.GetPrintCommand(filename)

    if command == "":
        app = u""
        thisFile = u""
        if os.path.exists(application):
            if sys.platform == "win32":
                app = win32api.GetShortPathName(application)
                thisFile = win32api.GetShortPathName(filename)
            else:
                app = string.replace(application, " ", "\\ ")
                thisFile = string.replace(filename, " ", "\\ ")
        
        if app != "":
            command = app
            if sys.platform == "darwin":
                command = u"open -a " + app
            
            command = command + " " + thisFile
        
    if command != "":
        #command = unicode(command, "utf-8")
        ranCommand = True
        print `command`
        wx.Execute(command.encode("utf-8"))
    
    return ranCommand


def getEClass3Dir():
    return os.path.join(getDocumentsDir(), "%s Projects" % app_name)


def openFolderInGUI(folder):
    if wx.Platform == "__WXMSW__":
        win32api.ShellExecute(0, "open", folder, "", folder, 1)
    elif wx.Platform == "__WXMAC__":
        result = os.popen("open " + string.replace(folder, " ", "\ "))
        result.close()


def getOSProgramExt():
    ext = "*"
    if wx.Platform == "__WXMSW__":
        ext = "exe"
    elif wx.Platform == "__WXMAC__":
        ext = "app"
    return ext


def getOSApplicationsDir():
    appdir = ""
    if wx.Platform == "__WXMSW__":
        appdir = "C:\Program Files"
    elif wx.Platform == "__WXMAC__":
        appdir = "/Applications"
    elif wx.Platform == "__WXGTK__":
        appdir = "/usr/bin"
       
    return appdir
