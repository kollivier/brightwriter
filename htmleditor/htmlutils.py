from HTMLParser import HTMLParser

import cStringIO
import os
import re
import string
import sys
import types

from externals import BeautifulSoup

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

def getUnicodeHTMLForFile(filename):
    html = open(filename, "rb").read()
    encoding = GetEncoding(html)
    if not encoding:
        encoding = ""
        
    return makeUnicode(html, encoding)
    
def GetEncoding(myhtml):
    """Checks for document HTML encoding and returns it if found."""
    import re
    match = re.search("""<meta.*?content=["]?text/html;\s*charset=([^\"]*)["]?""", myhtml, re.IGNORECASE)
    if match:
        return match.group(1).lower() #python encodings always in lowercase
    else:
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

def stripEmptyParagraphs(soup):
    matches = soup.findAll(text=re.compile("^\s*&nbsp;\s*$"))
    for match in matches:
        match.extract()
        
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
                        "Word-2000" : 1,
                        "force-output" : 1,
                        "output-xhtml" : 1,
                        "doctype" : "strict",
                        "drop-empty-paras": 1,
                        "output-encoding" : "utf8",
                        "clean": 1
                       }
    if options:
        default_options.extend(options)

    # first fix up footnotes so that HTMLTidy won't ditch them
    soup = BeautifulSoup.BeautifulSoup(html, smartQuotesTo="html")
    footnoteFixer(soup) #html)
    stripEmptyParagraphs(soup)
    
    html, errors = tidylib.tidy_document(soup.prettify(encoding=None), options=default_options)
    
    soup = BeautifulSoup.BeautifulSoup(html, smartQuotesTo="html")
    addMetaTag(soup, [('http-equiv', 'Content-type'), ('content', 'text/html; charset=utf-8')])
    
    return soup.prettify(encoding=None), errors

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

if __name__ == '__main__':
    unittest.main()
