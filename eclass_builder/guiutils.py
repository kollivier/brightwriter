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
