from HTMLParser import HTMLParser

import cStringIO
import os
import re
import string
import sys

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
        
    return utils.makeUnicode(html, encoding)
    
def GetEncoding(myhtml):
    """Checks for document HTML encoding and returns it if found."""
    import re
    match = re.search("""<meta.*?content=["]?text/html;\s*charset=([^\"]*)["]?""", myhtml, re.IGNORECASE)
    if match:
        return match.group(1).lower() #python encodings always in lowercase
    else:
        return None

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
