##########################################
# utils.py
# Common utilities used among EClass modules
# Author: Kevin Ollivier
##########################################

import sys, os, string
import settings

class LogFile:
	def __init__(self, filename="log.txt"):
		self.filename = filename

	def write(self, message):
		if message == None:
			return
		print message
		myfile = open(self.filename, "a")
		myfile.write(message + "\n")
		myfile.close()

def getStdErrorMessage(type = "IOError", args={}):
	if type == "IOError":
		if args.has_key("type") and args["type"] == "write":
			return _("There was an error writing the file '%(filename)s' to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file.") % {"filename":args["filename"]}
		elif args.has_key("type") and args["type"] == "read":
			return _("Could not read file '%(filename)s from disk. Please check that the file exists in the location specified and that you have permission to open/view the file.") % {"filename":args["filename"]}
		elif args.has_key("filename"):
			return _("There was a problem reading or writing the file %(filename)s. Please check that the file exists and that you have correct permissions to the file.") % {"filename":args["filename"]} 
	elif type == "UnknownError":
		return _("An unknown error has occurred. A traceback has been written to the 'errlog.txt' file within your program directory.")

def makeModuleName(text):
	result = string.replace(text, "-", "_")
	result = string.replace(result, "*", "")
	result = string.replace(result, "/", "")
	result = string.replace(result, "\\", "")

def createHTMLPageWithBody(text):
	retval = """
<html>
<head>
</head>
<body>
%s
</body>
</html>""" % text

	return retval