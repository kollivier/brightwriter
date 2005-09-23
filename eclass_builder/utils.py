##########################################
# utils.py
# Common utilities used among EClass modules
# Author: Kevin Ollivier
##########################################

import sys, os, string
import settings
import plugins

class LogFile:
	def __init__(self, filename="log.txt"):
		self.filename = filename
		
	def read(self):
		if os.path.exists(self.filename):
			return unicode(open(self.filename, "rb").read(), "utf-8")
		else:
			return ""

	def write(self, message):
		if message == None:
			return
		myfile = open(self.filename, "ab")
		myfile.write(message.encode("utf-8") + "\n")
		myfile.close()

	def clear(self):
		os.remove(self.filename)

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

def isReadOnly(filename):
    if sys.platform == 'win32':
        import win32file
        fileattr = win32file.GetFileAttributes(filename)
        return (fileattr & win32file.FILE_ATTRIBUTE_READONLY)
    else:
        return not (os.stat(filename)[stat.ST_MODE] & stat.S_IWUSR)

def CreateJoustJavascript(pub):
	try:
		filename = _GetFilename(pub.nodes[0].content.filename)
		text = """
function addJoustItems(theMenu){
	var level1ID = -1;
	var level2ID = -1;
	var level3ID = -1;
"""
		text = text + """level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(pub.nodes[0].content.metadata.name, "\"", "\\\""), filename, string.replace(pub.nodes[0].content.metadata.name, "\"", "\\\""))
		text = text + AddJoustItems(pub.nodes[0], 1)
		text = text + "return theMenu; \n}"

		afile = open(os.path.join(settings.CurrentDir, "joustitems.js"), "w")
		afile.write(text)
		afile.close()
	except:
		import traceback
		print `traceback.print_exc()`
	

def AddJoustItems(nodes, level):
	text = ""
	for root in nodes.children:
		filename = ""
		if string.find(root.content.filename, "imsmanifest.xml") != -1:
				root = root.pub.nodes[0]

		filename = _GetFilename(root.content.filename) 

		if not root.content.public == "false":
			if len(root.children) > 0:
				nodeType = "Book"
			else:
				nodeType = "Document"
			text = text + """level%sID = theMenu.addChild(level%sID,"%s", "%s", "%s", "%s");\n""" % (level + 1, level, nodeType, string.replace(root.content.metadata.name, "\"", "\\\""), filename, string.replace(root.content.metadata.name, "\"", "\\\""))

			if len(root.children) > 0:
				text = text + AddJoustItems(root, level + 1)
		else:
			print "Item " + root.content.metadata.name + " is marked private and was not published."
	return text	

def _GetFilename(filename):
	extension = string.split(filename, ".")[-1]
	publisher = plugins.GetPluginForExtension(extension).HTMLPublisher()
	if publisher: 
		try:
			filename = "pub/" + publisher.GetFilename(filename)
		except: 
			import traceback
			print `traceback.print_exc()`
	else:
		filename = string.replace(filename, "\\", "/")
	return filename

def getCurrentEncoding():
	import locale
	encoding = locale.getdefaultlocale()[1]
	if not encoding or encoding == 'ascii':
		encoding = "iso-8859-1" 
	
	return encoding
	
def makeUnicode(text, encoding):
	if isinstance(text, str):
		return text.decode(encoding, 'replace')
	else:
		return text

def openFile(filename, mode="r"):
    """We need this special function because there are hardcoded restriction on the size of the pathname. 
       We used to use GetShortPathName, but that  only works with ANSI mode, not with Unicode.
       Tried ctypes, but that seems like too thin a wrapper for my comfort."""
    myfilename = filename
    olddir = os.getcwd()
    if len(filename) > 240: #the exact number of chars varies by OS, but it's in the 240-250 char range on all the tested OSes.
        mydir = os.path.dirname(filename)
        myfilename = os.path.basename(filename)
        if len(mydir) > 240:
            # fun, now we have to break up the directory into a two parts that are both less than 240 chars
            sepmarker = mydir.rfind(os.sep)
            while (sepmarker > 0 and sepmarker > 240):
                sepmarker = mydir.rfind(os.sep)
            mydir = mydir[0:sepmarker-1]
            myfilename = os.path.join(mydir[sepmarker+1:], myfilename)
            os.chdir(mydir)
    myfile = open(myfilename, mode)
    os.chdir(olddir)
    return myfile
            
