import os
import sys
import xml.dom.minidom

from xmlobjects import *

class NCXTextWrapper(Tag):
    def __init__(self, name="ncx:docTitle"):
        Tag.__init__(self, name)
        
        self.ncxText = Tag("ncx:text")
        
        self.children = [self.ncxText]

class NCXHead(Tag):
    def __init__(self, name="ncx:head"):
        Tag.__init__(self, name)
        
        self.metatags = TagList("ncx:meta", tagClass=Tag)
        
        self.children = [self.metatags]

class NCXNavPoint(Tag):
    def __init__(self, name="ncx:navPoint"):
        Tag.__init__(self, name)
        
        self.label = NCXTextWrapper("ncx:navLabel")
        self.content = Tag("ncx:content")
        self.navPoints = TagList("ncx:navPoint", tagClass=NCXNavPoint)
        
        self.children = [self.label, self.content, self.navPoints]
        

class NCX(RootTag):
    def __init__(self, name="ncx:ncx"):
        Tag.__init__(self, name)
        
        self.attrs["xmlns:ncx"] = "http://www.daisy.org/z3986/2005/ncx/"
        self.attrs["version"] = "2005-1"
        self.head = NCXHead()
        self.docTitle = NCXTextWrapper("ncx:docTitle")
        self.navPoints = Container("ncx:navMap", "ncx:navPoint", NCXNavPoint)
        
        self.filename = "toc.ncx"
        
        self.children = [self.head, self.docTitle, self.navPoints]
