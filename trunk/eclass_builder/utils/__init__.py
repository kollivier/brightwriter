##########################################
# utils.py
# Common utilities used among EClass modules
# Author: Kevin Ollivier
##########################################

import sys, os, string
import settings
import plugins
import constants
import ims
import ims.contentpackage
import ims.utils
import conman
import appdata
import eclassutils
import uuid

filenameRestrictedChars = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]

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
        return _("An unknown error has occurred.") + constants.errorInfoMsg

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
    if isinstance(pub, conman.conman.ConNode):
        name = pub.nodes[0].content.metadata.name
        filename = GetFileLink(pub.content.filename)
    elif isinstance(pub, ims.contentpackage.Item):
        name = pub.title.text
        resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, pub)
        filename = eclassutils.getEClassPageForIMSResource(resource)
        if not filename:
            filename = resource.getFilename()
        filename = GetFileLink(filename)
    text = u"""
function addJoustItems(theMenu){
var level1ID = -1;
var level2ID = -1;
var level3ID = -1;
"""
    text = text + """level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(name, "\"", "\\\""), filename, string.replace(name, "\"", "\\\""))
    text = text + AddJoustItems(pub, 1)
    text = text + "return theMenu; \n}"

    afile = open(os.path.join(settings.ProjectDir, "joustitems.js"), "w")
    afile.write(text.encode("utf-8"))
    afile.close()
    

def AddJoustItems(nodes, level):
    text = u""
    if isinstance(nodes, conman.conman.ConNode):
        children = nodes.children
    else:
        children = nodes.items
        
    for root in children:
        filename = ""

        if isinstance(root, conman.conman.ConNode):
            filename = GetFileLink(root.content.filename)
            name = root.content.metadata.name
        elif isinstance(root, ims.contentpackage.Item):
            name = root.title.text
            resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, root)
            filename = eclassutils.getEClassPageForIMSResource(resource)
            if not filename:
                filename = resource.getFilename()
            filename = GetFileLink(filename)

        if isinstance(root, conman.conman.ConNode) and len(root.children) > 0 \
            or isinstance(root, ims.contentpackage.Item) and len(root.items) > 0:
            nodeType = "Book"
        else:
            nodeType = "Document"
        text = text + u"""level%sID = theMenu.addChild(level%sID,"%s", "%s", "%s", "%s");\n""" % (level + 1, level, nodeType, string.replace(name, '"', '\\"'), filename, string.replace(name, '"', '\\"'))

        if len(root.children) > 0:
            text = text + AddJoustItems(root, level + 1)

    return text 

def GetFileLink(filename):
    try:
        publisher = plugins.GetPluginForFilename(filename).HTMLPublisher()
        filename = publisher.GetFileLink(filename)
    except: 
        filename = string.replace(filename, "\\", "/")

    return filename

def getCurrentEncoding():
    import locale
    encoding = locale.getdefaultlocale()[1]
    if not encoding or encoding == 'ascii':
        if sys.platform == "darwin":
            encoding = "utf-8"
        else:
            encoding = "iso-8859-1" 
    
    return encoding
    
def makeUnicode(text, encoding=""):
    if encoding == "":
        encoding = getCurrentEncoding()

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
 
def createSafeFilename(filename):
    finalname = filename
    global filenameRestrictedChars
    for char in filenameRestrictedChars:
        finalname = finalname.replace(char, "")

    return finalname
    
def createWebFriendlyFilename(filename):
    finalname = createSafeFilename(filename)
    finalname = finalname.replace(" ", "_")
    return finalname
    
def checkNameExists(filename):
    # due to file conversion, we have to check for files with other extensions
    # that have the same name.
    basename = os.path.splitext(os.path.basename(filename))[0]
    for dir in ["EClass", "Text", "pub"]:
        for ext in [".htm", ".html", ".quiz", ".ecp"]:
            if os.path.exists(os.path.join(settings.ProjectDir, dir, basename + ext)):
                return True
                
    return False

def suggestFilename(filename):
    counter = 2
    finalname = filename
    
    # check for any files that would end up being named pub/whatever.html
    while checkNameExists(finalname):
        basename, ext = os.path.splitext(os.path.basename(finalname))
        finalname = basename + `counter` + ext
        counter = counter + 1
    return finalname
    
def escapeFilename(filename):
    # escape any special characters for terminal commands
    if not sys.platform.startswith("win"):
        result = filename.replace(" ", "\\ ")
        result = result.replace("(", "\\(")
        result = result.replace(")", "\\)")
        result = result.replace("[", "\\[")
        result = result.replace("]", "\\]")
    return result
    
def getPlatformName():
    if sys.platform.startswith("win"):
        return "win32"
    elif sys.platform.startswith("darwin"):
        return "mac"
    else:
        return "linux"
        
def getUUID():
    """
    Generates and returns a random UUID as a unicode text object.
    """
    return unicode(uuid.uuid4())
