from HTMLParser import HTMLParser
from xmlutils import *

import analyzer
import externals.BeautifulSoup as BeautifulSoup
import cStringIO
import fileutils
import os
import re
import settings
import string
import sys
import urllib
import utils

def TextToHTMLChar(mytext):
    
    return TextToXMLChar(mytext)
    
def GetFullPathForURL(url, basedir):
    path = urllib.unquote(url)
    if path.find("file://") == 0 and os.path.exists(urllib.url2pathname(path)):
        path = urllib.urlretrieve(url)[0]
            
    if not os.path.exists(path):
        path = basedir + "/" + path
    
    return path
    
def getTitleForPage(filename):
    """
    Returns the text of the <title> tag in the HTML page if it has one, returns None otherwise.
    """
    soup = BeautifulSoup.BeautifulSoup(open(filename).read())
    if soup:
        title = soup.find('title')
        if title:
            return title.string
            
    return None

def copyDependentFilesAndUpdateLinks(oldfile, filename):
    myanalyzer = analyzer.ContentAnalyzer()
    myanalyzer.analyzeFile(filename)
    htmldir = os.path.dirname(oldfile)
    html = utils.openFile(filename, "r").read()
    encoding = GetEncoding(html)
    if encoding == None:
        encoding = utils.getCurrentEncoding()
        
    html = utils.makeUnicode(html, encoding)
    
    for link in myanalyzer.fileLinks:
        sourcefile = GetFullPathForURL(link, htmldir)
        
        if os.path.exists(sourcefile):
            sourcedir = os.path.dirname(sourcefile)
            htmlname = os.path.basename(filename)
            depName = os.path.basename(link)
            destLink = u"../File/" + htmlname + "_files/" + depName
            destdir = os.path.join(settings.ProjectDir, os.path.dirname(destLink[3:].replace("/", os.sep)))
            if not os.path.exists(destdir):
                os.makedirs(destdir)
            result = fileutils.CopyFile(depName, sourcedir, destdir)
            if result:
                html = html.replace(link, urllib.quote(destLink))
            else:
                print "unable to copy file: " + sourcefile
        else:
            print "cannot find source file: " + sourcefile
                
    output = utils.openFile(filename, "w")
    output.write(html.encode(encoding))
    output.close()

def convNotSoSmartQuotesToHtmlEntity(x):
    """
    Found at http://myzope.kedai.com.my/blogs/kedai/128
    """ 
    d =      {  "\xc2\x82":"&sbquo;",
                "\xc2\x83":"&fnof;",
                "\xc2\x84":"&bdquo;",
                "\xc2\x85":"&hellip;",
                "\xc2\x86":"&dagger;",
                "\xc2\x87":"&Dagger;",
                "\xc2\x88":"&circ;",
                "\xc2\x89":"&permil;",
                "\xc2\x8A":"&Scaron;",
                "\xc2\x8B":"&lsaquo;",
                "\xc2\x8C":"&OElig;",
                "\xc2\x91":"&lsquo;",
                "\xc2\x92":"&rsquo;",
                "\xc2\x93":"&ldquo;",
                "\xc2\x94":"&rdquo;",
                "\xc2\x95":"&bull;",
                "\xc2\x96":"&ndash;",
                "\xc2\x97":"&mdash;",
                "\xc2\x98":"&tilde;",
                "\xc2\x99":"&trade;",
                "\xc2\x9A":"&scaron;",
                "\xc2\x9B":"&rsaquo;",
                "\xc2\x9C":"&oelig;"}
    for i in d.keys():
        x=x.replace(i,d[i])
    return x

def GetEncoding(myhtml):
    """Checks for document HTML encoding and returns it if found."""
    import re
    match = re.search("""<meta\s+http-equiv=["]?Content-Type["]?\s+content=["]?text/html;\s*charset=([^\"]*)["]?>""", myhtml, re.IGNORECASE)
    if match:
        return match.group(1).lower() #python encodings always in lowercase
    else:
        return None

def GetBody(myhtml):
    """
    Function: _GetBody(self, myhtml)
    Last Updated: 9/24/02
    Description: Internal function to get the data in between the <BODY></BODY> tags.

    Arguments:
    - myhtml: a string containing the HTML page

    Return values:
    Returns the data between the <BODY></BODY> tags of the HTML page
            """
    inbody = 0
    inscript = 0
    bodystart = 0
    bodyend = 0
    text = ""
    uppercase = 1
    encoding = None
    html = myhtml.readline()
    while not html == "":
        if not encoding and string.find(html.lower(), "<meta") != -1:
            encoding = GetEncoding(html)
        #if we're inside a script, mark it so that we can test if body tag is inside the script
        scriptstart = string.find(html, "<SCRIPT")
        if scriptstart == -1:
            scriptstart = string.find(html, "<script")

        if not string.find(html, "</SCRIPT>") == -1 or not string.find(html, "</script>") == -1:
            inscript = 0

        #if we've found a script BEFORE the start of the body tag, and then found a body tag
        #it would be part of the script
        #that's why we check the script status first
        if not scriptstart == -1 and inbody == 0:
            inscript = 1

        #check for start of body in upper and lowercase
        bodystart = string.find(string.lower(html), "<body")

        #if body is found, mark the end of it
        if not bodystart == -1:
            bodystart = string.find(html, ">", bodystart)

        #if we've found both a body tag and a script tag, find which one comes first
        #if script is first, this isn't the "real" body tag
        if bodystart != -1 and scriptstart != -1:
            if bodystart > scriptstart:
                inscript = 1

        #if we are not in a script, and we've found the body tag, capture the text
        if inscript == 0 and (not bodystart == -1 or inbody):
            inbody = 1
            bodyend = string.find(string.lower(html), "</body>")
                
            #if both <BODY> and </BODY> are on same line, grab it all
            if not bodystart == -1 and not bodyend == -1:
                text = text + html[bodystart+1:bodyend]
                bodystart = -1
                bodyend = -1
                inbody = 0
            elif not bodyend == -1:
                #if bodyend == 0:
                #   bodyend = 1 #a hack because -1 means everything
                inbody = 0
                text = text + html[0:bodyend] 
                bodyend = -1
            elif not bodystart == -1:
                text = text + html[bodystart+1:-1] 
                bodystart = -1
            elif inbody == 1:
                text = text + html 
        html = myhtml.readline()
    
    if encoding and encoding in ["windows-1252", "iso-8859-1", "iso-8859-2"]:
        text = convNotSoSmartQuotesToHtmlEntity(text)
        
    if not encoding:
        encoding = ""
        
    return utils.makeUnicode(text, encoding)

