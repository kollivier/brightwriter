import sys, os, string
import settings
from wxPython.wx import *
try:
	import win32api
except:
	pass

def getOpenCommandForFilename(filename):
	aFileType = wxTheMimeTypesManager.GetFileTypeFromExtension(os.path.splitext(filename)[1])
	if aFileType:
		return aFileType.GetOpenCommand(filename)

	return ""
	
def openInHTMLEditor(filename):
    htmleditor = settings.AppSettings["HTMLEditor"]
    if htmleditor == "":
        wxMessageDialog(self, _("To edit the page, EClass needs to know what HTML Editor you would like to use. To specify a HTML Editor, select 'Preferences' from the 'Options' menu."), _("Cannot Edit Page"), wxOK).ShowModal()
    else:
        if not os.path.exists(filename):
            return 
            
        if wxPlatform == "__WXMSW__":
            import win32api
            editor = "\"" + htmleditor + "\""
            if not string.find(string.lower(editor), "mozilla") == -1:
                editor = editor + " -edit" 
            win32api.WinExec(editor + " \"" + filename + "\"")
                
        else:
            editor = htmleditor 
            if wxPlatform == "__WXMAC__":
                editor = "open -a '" + editor + "'"
            path = editor + " '" + filename + "'"
            os.system(path)

def sendCommandToApplication(filename, action="open", application=""):
	command = ""
	ranCommand = False
	if not os.path.exists(filename):
		return ranCommand
	
	aFileType = wxTheMimeTypesManager.GetFileTypeFromExtension(os.path.splitext(filename)[1])
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
		wxExecute(command.encode("utf-8"))
	
	return ranCommand

def getAppDataDir():
	dir = ""
	if wxGetApp():
		dir = wxStandardPaths.Get().GetUserDataDir()
		if not os.path.exists(dir):
			os.mkdir(dir)
	
	return dir

def getOldAppDataDir():
	"""
	This function contains the old logic for finding the preferences directory. It is still 
	in place so that any old preferences can be moved to the data dir returned by StandardPaths.
	"""
	prefdir = ""
	if wxPlatform == '__WXMSW__':
		import _winreg as wreg
		key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") 
		prefdir = ""
		#Win98 doesn't have a Local AppData folder
		#TODO: replace all this code with wxStandardPaths!
		try:
			prefdir = wreg.QueryValueEx(key,'Local AppData')[0]
		except:
			try:
				prefdir = wreg.QueryValueEx(key,'AppData')[0]
			except:
				pass
		if not os.path.exists(prefdir):
			prefdir = self.AppDir
		else:
			if not os.path.exists(os.path.join(prefdir, "EClass")):
				os.mkdir(os.path.join(prefdir, "EClass"))
			prefdir = os.path.join(prefdir, "EClass")

	elif wxPlatform == '__WXMAC__':
		prefdir = os.path.join(os.path.expanduser("~"), "Library", "Preferences", "EClass")

	else: #Assume we're UNIX-based
		prefdir = os.path.join(os.path.expanduser("~"), ".eclass")

	return prefdir

def getDocumentsDir():
	docsfolder = ""
	if wxPlatform == '__WXMSW__':
		try:
			import _winreg as wreg
			key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") 
			my_documents_dir = wreg.QueryValueEx(key,'Personal')[0] 
			key.Close() 
			docsfolder = os.path.join(my_documents_dir)
		except:
			key.Close()
				
	elif wxPlatform == '__WXMAC__':
		docsfolder = os.path.join(os.path.expanduser("~"),"Documents")
	else:
		docsfolder = os.path.expanduser("~")

	if not os.path.exists(docsfolder):
		os.mkdir(docsfolder)

	return docsfolder

def getEClassProjectsDir():
	if wxPlatform in ['__WXMAC__', '__WXMSW__']:
		return os.path.join(getDocumentsDir(), "EClass Projects")
	else:
		return os.path.join(getDocumentsDir(), "eclass_projects")

def openFolderInGUI(folder):
	if wxPlatform == "__WXMSW__":
		win32api.ShellExecute(0, "open", folder, "", folder, 1)
	elif wxPlatform == "__WXMAC__":
		result = os.popen("open " + string.replace(folder, " ", "\ "))
		result.close()
		
def getOSProgramExt():
	ext = "*"
	if wxPlatform == "__WXMSW__":
		ext = "exe"
	elif wxPlatform == "__WXMAC__":
		ext = "app"
	return ext 
	
def getOSApplicationsDir():
	appdir = ""
	if wxPlatform == "__WXMSW__":
		appdir = "C:\Program Files"
	elif wxPlatform == "__WXMAC__":
		appdir = "/Applications"
	elif wxPlatform == "__WXGTK__":
		appdir = "/usr/bin"
	   
	return appdir
