import sys, os, string
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