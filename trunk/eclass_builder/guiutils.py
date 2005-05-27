import sys, os, string
from wxPython.wx import *
try:
	import win32api
except:
	pass

def sendCommandToApplication(filename, action="open", application=""):
	command = ""
	ranCommand = False
	if not os.path.exists(filename):
		return ranCommand
	
	aFileType = wxTheMimeTypesManager.GetFileTypeFromExtension(os.path.splitext(filename)[1])
	filename = win32api.GetShortPathName(filename)
	if aFileType and action == "open" and application == "":
		command = aFileType.GetOpenCommand(filename)

	if aFileType and action == "print" and application == "":
		command = aFileType.GetPrintCommand(filename)

	if command == "":
		app = ""
		thisFile = ""
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
				command = "open -a " + app
			
			command = command + " " + thisFile
		
	if command != "":
		ranCommand = True
		print command
		wxExecute(command)
	
	return ranCommand