from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
from html.parser import HTMLParser
from xmlutils import *

import analyzer
import bs4 as BeautifulSoup
import io
import fileutils
import os
import re
import settings
import sys
import urllib.request, urllib.parse, urllib.error
import utils

import six


def getCurrentEncoding():
    import locale
    encoding = locale.getdefaultlocale()[1]
    if not encoding or encoding == 'ascii':
        if sys.platform == "darwin":
            encoding = "utf-8"
        else:
            encoding = "iso-8859-1" 
    
    return encoding

def TextToHTMLChar(mytext):
    
    return TextToXMLChar(mytext)
    
def GetFullPathForURL(url, basedir):
    if url.find("file://") == 0:
        # Using urlretrieve on a local file simply returns the filename
        # and does not copy or reproduce the file.
        try:
            path = urllib.request.urlretrieve(url)[0]
            
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
    content = open(filename, encoding='utf-8').read()
    soup = BeautifulSoup.BeautifulSoup(content)
    if soup:
        title = soup.find('title')
        if title:
            return title.string.strip()
            
    return os.path.splitext(os.path.basename(filename))[0]
    
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

def stripEmptyParagraphs(soup):
    matches = soup.findAll(text=re.compile("^\s*&nbsp;\s*$"))
    for match in matches:
        match.extract()

def removeVMLAttrs(soup):
    matches = soup.findAll(attrs={"v:shapes": re.compile(".*")})
    for match in matches:
        del match["v:shapes"]

def addMetaTag(soup, attrs):
    """
    This is used basically to re-add the stripped encoding meta tag caused
    by running the document through HTMLTidy.
    """
    head = soup.find('head')
    if head:
        meta = soup.find(attrs={'http-equiv': 'Content-type'})
        if meta:
            meta.extract()
        tag = BeautifulSoup.Tag(soup, "meta", attrs)
        head.insert(0, tag)

def cleanUpHTML(html, options=None):
    import tidylib
    tidylib.BASE_OPTIONS = {}

    default_options = { 
                        "force-output" : 1,
                        "output-xhtml" : 1,
                        "doctype" : "strict",
                        "drop-empty-paras": 0,
                        "output-encoding" : "utf8",
                        "clean": 1,
                        "bare": 1,
                        "hide-endtags": 0,
                        "tidy-mark": 0
                       }
    if options:
        default_options.extend(options)

    # first fix up footnotes so that HTMLTidy won't ditch them
    soup = BeautifulSoup.BeautifulSoup(html, smartQuotesTo="html")
    footnoteFixer(soup) #html)
    stripEmptyParagraphs(soup)
    removeVMLAttrs(soup)
    addMetaTag(soup, [('http-equiv', 'Content-type'), ('content', 'text/html; charset=utf-8')])
    
    return tidylib.tidy_document(soup.prettify(encoding=None), options=default_options)

    
def ensureValidXHTML(html):
    soup = BeautifulSoup.BeautifulSoup(html, smartQuotesTo="html")
    styles = soup.findAll("style")
    for style in styles:
        if not 'type' in style:
            style['type'] = 'text/css'

    bookmarks = soup.findAll("a", {"name": True})
    for bookmark in bookmarks:
        bookmark['id'] = bookmark['name']
        del bookmark['name']

    return soup.prettify(encoding=None)


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
                html = html.replace(link, urllib.parse.quote(destLink))
            else:
                print("unable to copy file: " + sourcefile)
        else:
            print("cannot find source file: " + sourcefile)
                
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
    for i in list(d.keys()):
        x=x.replace(i,d[i])
    return x

def GetEncoding(myhtml):
    """Checks for document HTML encoding and returns it if found."""
    import re
    test_html = myhtml
    if isinstance(test_html, six.text_type):
        # since checking a byte string will be the common case for determining encoding,
        # convert unicode objects into a bytestring before searching. if a charset other than
        # utf-8 is used, this test will still work since the meta tag data is all ASCII.
        test_html = myhtml.encode("utf-8", errors="replace")
    match = re.search(b"""<meta.*?content=["]?text/html;\s*charset=([^\"]*)["]?""", test_html, re.IGNORECASE)
    if match:
        return match.group(1).lower().decode("utf-8") #python encodings always in lowercase
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
    
    # if encoding and encoding.lower() in ["windows-1252", "iso-8859-1", "iso-8859-2"]:
    #     text = convNotSoSmartQuotesToHtmlEntity(text)
    
    # text = utils.makeUnicode(text, encoding, 'xmlcharrefreplace')
    
    soup = BeautifulSoup.BeautifulSoup(myhtml)
    if not soup.body:
        raise Exception(f"No body found for {myhtml}")
    # get BeautifulSoup to explicitly declare the encoding
    text = soup.body.prettify(encoding='utf-8').decode('utf-8')
    if soup.html.head:
        scripts = soup.html.head.findAll('script')
        scripts.reverse() # since we're prepending, we need to do it in reverse order
        for script in scripts:
            text = str(script) + text
    
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
