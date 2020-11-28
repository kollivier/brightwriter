##########################################
# utils.py
# Common utilities used among EClass modules
# Author: Kevin Ollivier
##########################################

from builtins import str
import sys, os, string
import settings
import shutil
import chardet
import constants
import ims
import ims.contentpackage
import ims.utils
import appdata
import eclassutils
import uuid

filenameRestrictedChars = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "'", "\""]

def getStdErrorMessage(type = "IOError", args={}):
    if type == "IOError":
        if "type" in args and args["type"] == "write":
            return _("There was an error writing the file '%(filename)s' to disk. Please check that you have enough hard disk space to write this file and that you have permission to write to the file.") % {"filename":args["filename"]}
        elif "type" in args and args["type"] == "read":
            return _("Could not read file '%(filename)s from disk. Please check that the file exists in the location specified and that you have permission to open/view the file.") % {"filename":args["filename"]}
        elif "filename" in args:
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

def AddiPhoneItems(node, isroot=False):
    links = ""
    pages = ""
    children = node.items
    
    childLinks = ""
    for root in children:
        filename = ""

        name = root.title.text
        if not name:
            name = ""
        childLinks += "<li><a href=\"#%s\">%s</a></li>\n" % (name.replace(" ", ""), name)
        if len(root.children) > 0:
            newlinks, newpages = AddiPhoneItems(root)
            links += newlinks
            pages += newpages

    name = nodename = node.title.text
    if not name:
        name = nodename = ""

    selectedText = ""
    
    if isroot:
        selectedText = """ selected="true" """
    
    if len(node.items) > 0:
        name = name + "_content"
        links += """
<ul id="%s"%s>
    <li><a href="#%s">Intro</a></li>
    %s
</ul>""" % (nodename.replace(" ", ""), selectedText, name.replace(" ", ""), childLinks)


    resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, node)
    filename = resource.getFilename()
    pages += """<iframe id="%s" frameborder="0" width="100%%" height="95%%" src="%s"></iframe>""" % (name.replace(" ", ""), filename)
    return links, pages

def CreateiPhoneNavigation(rootItem, output_dir):
    html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>%s</title>
<meta name="viewport" content="width=320; initial-scale=1.0; maximum-scale=1.0; user-scalable=0;"/>
<style type="text/css" media="screen">@import "iui/iui.css";</style>
<script type="application/x-javascript" src="iui/iui.js"></script>
</head>
<body>
    <div class="toolbar">
        <h1 id="pageTitle">%s</h1>
        <a id="backButton" class="button" href="#"></a>
    </div>
""" % (rootItem.title.text, rootItem.title.text)

    links, pages = AddiPhoneItems(rootItem, isroot=True)
    html += links + pages

    html += """</body>
</html>
"""
    
    afile = open(os.path.join(output_dir, "iPhone.html"), "w")
    afile.write(html.encode("utf-8"))
    afile.close()
    
    destdir = os.path.join(output_dir, "iui")
    if os.path.exists(destdir):
        shutil.rmtree(destdir)
    shutil.copytree(os.path.join(settings.AppDir, "externals", "iui-0.13", "iui"), destdir)

def CreateJoustJavascript(pub, output_dir):
    name = pub.title.text
    resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, pub)
    filename = resource.getFilename()
    text = u"""
function addJoustItems(theMenu){
var level1ID = -1;
var level2ID = -1;
var level3ID = -1;
"""
    text = text + """level1ID = theMenu.addEntry(-1, "Book", "%s", "%s", "%s");\n""" % (string.replace(name, "\"", "\\\""), filename, string.replace(name, "\"", "\\\""))
    text = text + AddJoustItems(pub, 1)
    text = text + "theMenu.openAll();\n"
    text = text + "return theMenu; \n}"

    afile = open(os.path.join(output_dir, "joustitems.js"), "w")
    afile.write(text.encode("utf-8"))
    afile.close()
    

def AddJoustItems(nodes, level):
    text = u""

    children = nodes.items
        
    for root in children:
        filename = ""

        name = root.title.text
        if not name:
            name = ""
        resource = ims.utils.getIMSResourceForIMSItem(appdata.currentPackage, root)
        filename = resource.getFilename()

        if isinstance(root, ims.contentpackage.Item) and len(root.items) > 0:
            nodeType = "Book"
        else:
            nodeType = "Document"
        text = text + u"""level%sID = theMenu.addChild(level%sID,"%s", "%s", "%s", "%s");\n""" % (level + 1, level, nodeType, name.replace('"', '\\"'), filename, name.replace('"', '\\"'))

        if len(root.children) > 0:
            text = text + AddJoustItems(root, level + 1)

    return text
    
def guessEncodingForText(text):
    encoding = chardet.detect(text)['encoding']
    try:
        text.decode(encoding)
        return encoding
    except:
        return None

def getCurrentEncoding():
    import locale
    encoding = locale.getdefaultlocale()[1]
    if not encoding or encoding == 'ascii':
        if sys.platform == "darwin":
            encoding = "utf-8"
        else:
            encoding = "iso-8859-1" 
    
    return encoding
    
def makeUnicode(text, encoding="", errors='strict'):
    if not isinstance(text, str):
        return text
        
    # Always try latin1 first, since it sometimes gets misread / detected as other encodings
    detect_encoding = guessEncodingForText(text)
    encodings = [detect_encoding, 'latin_1', getCurrentEncoding(), 'utf-8']
    if encoding != "":
        encodings.insert(0, encoding)
        
    for guess_encoding in encodings:
        try:
            return text.decode(guess_encoding, errors)
        except:
            pass
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
                sepmarker = mydir.rfind(os.sep, 0, sepmarker-1)
                
            myfilename = os.path.join(mydir[sepmarker+1:], myfilename)
            mydir = mydir[0:sepmarker]
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
        finalname = '{}{}{}'.format(basename, counter, ext)
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
    return str(uuid.uuid4())
