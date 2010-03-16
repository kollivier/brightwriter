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
    if url.find("file://") == 0:
        # Using urlretrieve on a local file simply returns the filename
        # and does not copy or reproduce the file.
        try:
            path = urllib.urlretrieve(url)[0]
            
            if not os.path.exists(path):
                path = basedir + "/" + path
    
            return path
        except:
            pass
    elif url.find('://') == -1: # no protocol, it's probably a relative file
        return os.path.join(basedir, url)
    
    return url
    
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
    
def footnoteFixer(soup):
     matches = soup.findAll(style=re.compile("^mso-footnote-id:"))
     for match in matches:
        del match['style']
        text = match.findAll(text=re.compile("[\d+]"))
        if text and len(text) > 0:
            match.insert(0, text[0].strip())
     
        for span in match.findAll("span"):
            span.extract()

def getUnicodeHTMLForFile(filename):
    html = open(filename, "rb").read()
    encoding = GetEncoding(html)
    if not encoding:
        encoding = ""
        
    return utils.makeUnicode(html, encoding)

def cleanUpHTML(filename, options=None):
    import tidylib
    tidylib.BASE_OPTIONS = {}

    default_options = { 
                        "Word-2000" : 1,
                        "force-output" : 1,
                        "output-xhtml" : 1,
                        "drop-empty-paras": 1,
                        "output-encoding" : "utf8",
                       }
    if options:
        default_options.extend(options)
        
    html = getUnicodeHTMLForFile(filename)

    # first fix up footnotes so that HTMLTidy won't ditch them
    soup = BeautifulSoup.BeautifulSoup(html, smartQuotesTo="html")
    footnoteFixer(soup) #html)
    stripEmptyParagraphs(soup)
    
    html, errors = tidylib.tidy_document(soup.prettify(encoding=None), options=default_options)
    
    html = addMetaTag(html, [('http-equiv', 'Content-Type'), ('content', 'text/html; charset=utf-8')])
    
    return html.encode("utf8"), errors
    


def copyDependentFilesAndUpdateLinks(oldfile, filename):
    myanalyzer = analyzer.ContentAnalyzer()
    myanalyzer.analyzeFile(filename)
    htmldir = os.path.dirname(oldfile)
    html = utils.openFile(filename, "r").read()
    encoding = GetEncoding(html)
    if encoding == None:
        encoding = utils.getCurrentEncoding()
        
    html = utils.makeUnicode(html, encoding)
    
    if not encoding:
        encoding = utils.guessEncodingForText(text)
    
    if encoding and encoding.lower() in ["windows-1252", "iso-8859-1", "iso-8859-2"]:
        html = convNotSoSmartQuotesToHtmlEntity(html)
    
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
    d =      {  "\x82":"&sbquo;",
                "\x83":"&fnof;",
                "\x84":"&bdquo;",
                "\x85":"&hellip;",
                "\x86":"&dagger;",
                "\x87":"&Dagger;",
                "\x88":"&circ;",
                "\x89":"&permil;",
                "\x8A":"&Scaron;",
                "\x8B":"&lsaquo;",
                "\x8C":"&OElig;",
                "\x91":"&lsquo;",
                "\x92":"&rsquo;",
                "\x93":"&ldquo;",
                "\x94":"&rdquo;",
                "\x95":"&bull;",
                "\x96":"&ndash;",
                "\x97":"&mdash;",
                "\x98":"&tilde;",
                "\x99":"&trade;",
                "\x9A":"&scaron;",
                "\x9B":"&rsaquo;",
                "\x9C":"&oelig;"}
    for i in d.keys():
        x=x.replace(i,d[i])
    return x

def GetEncoding(myhtml):
    """Checks for document HTML encoding and returns it if found."""
    import re
    match = re.search("""<meta.*?content=["]?text/html;\s*charset=([^\"]*)["]?""", myhtml, re.IGNORECASE)
    if match:
        return match.group(1).lower() #python encodings always in lowercase
    else:
        return None

def GetBodySoup(myhtml):
    soup = BeautifulSoup.BeautifulSoup(myhtml.read())
    return soup.body.prettify(encoding=None)

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
    htmltext = myhtml.readlines()
    for html in htmltext:
        if not encoding and string.find(html.lower(), "<meta") != -1:
            encoding = GetEncoding(html)
        #if we're inside a script, mark it so that we can test if body tag is inside the script
        scriptstart = string.find(html, "<SCRIPT")
        if scriptstart == -1:
            scriptstart = string.find(html, "<script")

        if not string.find(html.lower(), "</script>") == -1:
            inscript = 0

        #check for start of body in upper and lowercase
        bodystart = string.find(string.lower(html), "<body")

        #if body is found, mark the end of it
        if not bodystart == -1:
            bodystart = string.find(html, ">", bodystart)

        #if we've found both a body tag and a script tag, find which one comes first
        #if script is first, this isn't the "real" body tag
        if (not inbody and bodystart != -1) and scriptstart != -1:
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
    
    if not encoding:
        encoding = utils.guessEncodingForText(text)
    
    if encoding and encoding.lower() in ["windows-1252", "iso-8859-1", "iso-8859-2"]:
        text = convNotSoSmartQuotesToHtmlEntity(text)
    
    print "calling makeUnicode"
    text = utils.makeUnicode(text, encoding, 'xmlcharrefreplace')
    
    soup = BeautifulSoup.BeautifulSoup('\n'.join(htmltext))
    if soup.html.head:
        scripts = soup.html.head.findAll('script')
        scripts.reverse() # since we're prepending, we need to do it in reverse order
        for script in scripts:
            text = script + text
    
    return text

import unittest

class HTMLTests(unittest.TestCase):
    def setUp(self):
        self.html = """
<html>
<head>
<script>
document.write("<BODY></BODY>")
</script>
</head>
<body>
<p>This is a sample MS Office footnote <a style='mso-footnote-id:
ftn1' href="#_ftn1" name="_ftnref1" title=""><span class=MsoFootnoteReference><span
style='mso-special-character:footnote'><![if !supportFootnotes]><span
class=MsoFootnoteReference><span lang=EN-US style='font-size:12.0pt;font-family:
"Times New Roman";mso-fareast-font-family:"Times New Roman";color:black;
mso-ansi-language:EN-US;mso-fareast-language:ES;mso-bidi-language:AR-SA'>[1]</span></span><![endif]></span></span></a><o:p></o:p></span></p>

<hr />

<p class=MsoFootnoteText><a style='mso-footnote-id:ftn1' href="#_ftnref1"
name="_ftn1" title=""><span class=MsoFootnoteReference><span lang=EN-US
style='mso-ansi-language:EN-US'><span style='mso-special-character:footnote'><![if !supportFootnotes]><span
class=MsoFootnoteReference><span lang=EN-US style='font-size:10.0pt;font-family:
"Times New Roman";mso-fareast-font-family:"Times New Roman";mso-ansi-language:
EN-US;mso-fareast-language:ES;mso-bidi-language:AR-SA'>[1]</span></span><![endif]></span></span></span></a>
This is a sample MS Office reference</p>

</body>
</html>
"""

    def testFootnoteFixer(self):
        soup = BeautifulSoup.BeautifulSoup(self.html)
        footnoteFixer(soup)
        html = str(soup)
        self.assert_(html.find("""<a href="#_ftn1" name="_ftnref1" title="">[1]</a>""") != -1)
        self.assert_(html.find("""<a href="#_ftnref1" name="_ftn1" title="">[1]</a>""") != -1)
        
    def testGetEncoding(self):
        html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"><html><head>
<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type"></head><body></body></html>
        """
        
        encoding = GetEncoding(html)
        self.assertEquals(encoding.lower(), "iso-8859-1")
        
        html = """
<html><head>
<meta http-equiv="Content-Language" content="en-us">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
</head><body></body></html>
        """
        
        encoding = GetEncoding(html)
        self.assertEquals(encoding, "windows-1252")

def getTestSuite():
    return unittest.makeSuite(HTMLTests)

if __name__ == '__main__':
    unittest.main()
