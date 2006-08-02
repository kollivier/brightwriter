import sys, os, string, re
import unittest
import urlparse

link_re = """href\s*?=(.*?)\s?>"""
media_re = """src\s*?=(.*?)\s?/?>"""
object_media_re = """<param name="?src|filename"? value=(.*?)\s?/?>"""

ignored_protocols = ["javascript", "mailto", "gopher"]


def findAllMatches(re_string, text, start=0):
    """
    findAllMatches finds matches for a given regex, and returns a list of objects.
    Note the stripping of text is not generally usable yet, it assumes matches
    are in continu ous blocks, which is true of the wx docs.
    """
    regex = re.compile(re_string, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    match = regex.search(text, start)
    results = []
    
    startpoint = -1
    endpoint = -1
    
    if match:
        startpoint = match.start() 
    
    while match:
        start = match.end()
        results.append(match)
        endpoint = match.end()
        match = regex.search(text, start)

    return results

class ContentAnalyzer:
    def __init__(self):
        self.filename = ""
        self.mediafiles = []
        self.numurls = 0
        self.links = []
        self.fileLinks = []
        self.webLinks = []
        
    def analyzeFile(self, filename):
        self.filename = filename
        self.analyzeText( open(filename, "rb").read() )
        
    def analyzeText(self, text):
        self.contents = text
        self.__GetLinksFromText()
        self.__ParseLinks()
        
    def __GetLinksFromText(self):
        matches = findAllMatches(link_re, self.contents)
        for match in matches:
            link = match.group(1).split(" ")[0].replace('"', '')
            self.links.append( link )
        
        matches = findAllMatches(media_re, self.contents)
        matches.extend( findAllMatches(object_media_re, self.contents) )
        
        # filter out any duplicate media files 
        for match in matches:
            media = match.group(1).split(" ")[0].replace('"', '')
            if not media in self.mediafiles:
                self.mediafiles.append( media )
                
    def __ParseLinks(self):
        for link in self.links + self.mediafiles:
            parsedLink = urlparse.urlparse(link)
            if parsedLink[1] == "" and not link.split(":")[0] in ignored_protocols:
                self.fileLinks.append(link)
            else:
                self.webLinks.append(link)
                
                
class AnalyzerTests(unittest.TestCase):

    def testJavaScriptLink(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href="javascript:alert('welcome!')">Welcome</a>""")
        self.assertEqual(analyzer.fileLinks, [])
        
    def testEmailLink(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href="mailto:atotallyfakeaddress@atotallyfakeserver.com">Welcome</a>""")
        self.assertEqual(analyzer.fileLinks, [])

    def testAbsoluteFileLink(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href="file:///home/kevino/welcome.html">Welcome</a>""")
        self.assertEqual(analyzer.fileLinks, ['file:///home/kevino/welcome.html'])

    def testLink(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href="welcome.html">Welcome</a>""")
        self.assertEqual(analyzer.fileLinks, ['welcome.html'])
        
    def testAbsoluteLink(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href="http://www.example.com/welcome.html">Welcome</a>""")
        self.assertEqual(analyzer.webLinks, ['http://www.example.com/welcome.html'])
        
    def testLinkNoQuotes(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<a href=welcome.html>Welcome</a>""")
        self.assertEqual(analyzer.fileLinks, ['welcome.html'])
        
    def testImage(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<img align="center" SRC="welcome.gif"/>""")
        self.assertEqual(analyzer.fileLinks, ["welcome.gif"])
        
    def testAbsoluteImage(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<img align="center" SRC="http://www.example.com/welcome.gif"/>""")
        self.assertEqual(analyzer.webLinks, ["http://www.example.com/welcome.gif"])
        
    def testImageNoQuotes(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<img align=center SRC=welcome.gif>""")
        self.assertEqual(analyzer.fileLinks, ["welcome.gif"])
        
    def testEmbed(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<embed src="welcome.swf" quality="autolow" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" scale="exactfit">""")
        self.assertEqual(analyzer.fileLinks, ["welcome.swf"])
        
    def testAbsoluteEmbed(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<embed src="http://www.example.com/welcome.swf" quality="autolow" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" scale="exactfit">""")
        self.assertEqual(analyzer.webLinks, ["http://www.example.com/welcome.swf"])
        
    def testEmbedNoQuotes(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""<embed src=welcome.swf quality="autolow" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" scale="exactfit">""")
        self.assertEqual(analyzer.fileLinks, ["welcome.swf"])
        
    def testObject(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""
<CENTER>
<OBJECT classid=clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95>
	<Param name="AutoSize" value="1"/>
	<Param name="AutoStart" value="True"/>
	<Param name="AutoRewind" value="1"/>
	<Param name="Filename" value="welcome.wmv"/>
	<Param name="PreviewMode" value="1"/>
</OBJECT>
</CENTER>""")
        self.assertEqual(analyzer.mediafiles, ["welcome.wmv"])
        
    def testAbsoluteObject(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""
<CENTER>
<OBJECT classid=clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95>
	<Param name="AutoSize" value="1"/>
	<Param name="AutoStart" value="True"/>
	<Param name="AutoRewind" value="1"/>
	<Param name="Filename" value="http://www.example.com/welcome.wmv"/>
	<Param name="PreviewMode" value="1"/>
</OBJECT>
</CENTER>""")
        self.assertEqual(analyzer.mediafiles, ["http://www.example.com/welcome.wmv"])
    
    def testObjectNoQuotes(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""
<CENTER>
<OBJECT classid=clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95>
	<Param name=AutoSize value=1/>
	<Param name=AutoStart value=True/>
	<Param name=AutoRewind value=1/>
	<Param name=Filename value=welcome.wmv/>
	<Param name=PreviewMode value=1/>
</OBJECT>
</CENTER>""")
        self.assertEqual(analyzer.mediafiles, ["welcome.wmv"])
    
    
    def testObjectEmbed(self):
        analyzer = ContentAnalyzer()
        analyzer.analyzeText("""
<CENTER>
<OBJECT classid=clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95>
	<Param name="AutoSize" value="1"/>
	<Param name="AutoStart" value="_autostart_"/>
	<Param name="AutoRewind" value="1"/>
	<Param name="Filename" value="welcome.wmv"/>
	<Param name="PreviewMode" value="1"/>
	<embed src="welcome.wmv" type="video/wmv" autostart="True"/><br>
</OBJECT>
</CENTER>
""")
        self.assertEqual(analyzer.mediafiles, ["welcome.wmv"])

def getTestSuite():
    return unittest.makeSuite(AnalyzerTests)

if __name__ == '__main__':
    unittest.main()
        
        